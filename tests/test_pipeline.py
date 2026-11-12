"""The cleaning and transformation pipeline: every decision it makes, and the arithmetic that proves
nothing was lost on the way.

The fixture is built so the right answer is known by hand. One product is observed three times at
200k, 220k and 240k (median 220k); one is on sale, so its regular price is the old price; one shows
only a starting price; one is priced per stem; one has no analysis category; one is priced far above
its category so it must be flagged as an outlier without being removed."""
import pytest

from priceintel import config
from priceintel.analysis.categories import classify_listings, load_rules
from priceintel.analysis.features import build_features
from priceintel.analysis.pipeline import (
    CV_FOLDS,
    build_dataset,
    dataset_summary,
)
from tests.conftest import add_fetch, add_run, shop_id

WINDOW = {"window_start": "2026-11-09", "window_end": "2026-12-06"}


@pytest.fixture(scope="module")
def rules():
    return load_rules(config.CATEGORY_RULES_FILE)


def add_listing(conn, run_id, title, slug, section, shop="uzflora"):
    host = {"uzflora": "uzflora.com", "loveflowers": "loveflowers.uz",
            "probuket": "pro-buket.uz"}[shop]
    return conn.execute(
        "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
        " last_title, site_category) VALUES (?, ?, ?, '2026-11-09T06:00:00Z',"
        " '2026-11-09T06:00:00Z', ?, ?) RETURNING listing_id",
        (shop_id(conn, shop), f"https://{host}/product/{slug}/", run_id, title,
         section)).fetchone()[0]


def observe(conn, listing_id, run_id, fetch_id, price, *, old=None, at="2026-11-09T06:00:00Z",
            is_from=0, availability="in_stock"):
    conn.execute(
        "INSERT INTO price_observations (listing_id, run_id, fetch_id, observed_at, source_type,"
        " title, price_uzs, old_price_uzs, is_from_price, availability, currency_shown)"
        " VALUES (?, ?, ?, ?, 'scrape', 'x', ?, ?, ?, ?, 'UZS')",
        (listing_id, run_id, fetch_id, at, price, old, is_from, availability))


@pytest.fixture
def built(market_db, rules):
    runs = [add_run(market_db, purpose="test") for _ in range(3)]
    fetches = [add_fetch(market_db, r) for r in runs]
    days = ("2026-11-09T06:00:00Z", "2026-11-10T06:00:00Z", "2026-11-11T06:00:00Z")

    plain = add_listing(market_db, runs[0], "Букет «Спокойный»", "plain", "bukety")
    for run, fetch, day, price in zip(runs, fetches, days, (200_000, 220_000, 240_000)):
        observe(market_db, plain, run, fetch, price, at=day)

    on_sale = add_listing(market_db, runs[0], "Букет «Акция»", "sale", "bukety")
    observe(market_db, on_sale, runs[0], fetches[0], 260_000, old=400_000)

    from_price = add_listing(market_db, runs[0], "Букет «От»", "from", "bukety")
    observe(market_db, from_price, runs[0], fetches[0], 150_000, is_from=1)

    # A fetch belongs to one shop: the provenance trigger refuses an observation whose fetch came
    # from a different shop, so loveflowers needs its own fetch in this run.
    love_fetch = add_fetch(market_db, runs[0], shop="loveflowers",
                           url="https://loveflowers.uz/tcat/tsvety-raznye/")
    per_stem = add_listing(market_db, runs[0], "Гербера красная", "gerbera", "tsvety-raznye",
                           shop="loveflowers")
    observe(market_db, per_stem, runs[0], love_fetch, 18_000)

    no_category = add_listing(market_db, runs[0], "Мужская забота", "gift", "podarki")
    observe(market_db, no_category, runs[0], fetches[0], 300_000)

    # Eight more ordinary bouquets, spread the way a real catalogue is (180k-390k), so the rule has
    # enough data and a 400k bouquet is ordinary rather than extreme. Then one genuinely extreme
    # price, which is what the rule must catch.
    for i in range(8):
        listing = add_listing(market_db, runs[0], f"Букет «Обычный {i}»", f"ord{i}", "bukety")
        observe(market_db, listing, runs[0], fetches[0], 180_000 + i * 30_000)
    extreme = add_listing(market_db, runs[0], "Букет «Огромный»", "huge", "bukety")
    observe(market_db, extreme, runs[0], fetches[0], 9_000_000)

    classify_listings(market_db, rules)
    build_features(market_db, rules)
    run_id, counts = build_dataset(market_db, purpose="test", rules_version=rules.version, **WINDOW)
    return market_db, run_id, counts, {"plain": plain, "on_sale": on_sale, "from": from_price,
                                       "per_stem": per_stem, "no_category": no_category,
                                       "extreme": extreme}


def row_for(conn, run_id, listing_id):
    return conn.execute("SELECT * FROM analysis_products WHERE pipeline_run_id = ?"
                        " AND listing_id = ?", (run_id, listing_id)).fetchone()


# ---------------------------------------------------------------------------
# Transformation
# ---------------------------------------------------------------------------

def test_a_product_contributes_one_median_however_often_it_was_seen(built):
    conn, run_id, _, ids = built
    row = row_for(conn, run_id, ids["plain"])
    assert row["n_observations"] == 3 and row["observed_days"] == 3
    assert row["regular_price_uzs"] == 220_000          # median of 200k, 220k, 240k
    assert row["price_changes"] == 2


def test_the_regular_price_of_a_discounted_product_is_its_old_price(built):
    conn, run_id, _, ids = built
    row = row_for(conn, run_id, ids["on_sale"])
    assert (row["regular_price_uzs"], row["sale_price_uzs"]) == (400_000, 260_000)
    assert row["days_on_sale"] == 1


# ---------------------------------------------------------------------------
# Cleaning decisions
# ---------------------------------------------------------------------------

def test_starting_prices_are_not_used_as_prices_but_stay_visible(built):
    """loveflowers publishes "от 550 000" on most of its cards. Those products must not be priced
    from a starting figure, and must not vanish either: the count has to be on the record."""
    conn, run_id, counts, ids = built
    assert counts.observations_from_price == 1
    row = row_for(conn, run_id, ids["from"])
    assert row is not None, "the product must still be counted"
    assert row["included"] == 0 and row["exclusion_reason"] == "starting_price_only"
    assert row["regular_price_uzs"] == 150_000, "recorded as the lower bound it is"
    assert counts.products_starting_price_only == 1


def test_per_stem_products_are_excluded_with_a_reason_not_deleted(built):
    conn, run_id, counts, ids = built
    row = row_for(conn, run_id, ids["per_stem"])
    assert row["included"] == 0 and row["exclusion_reason"] == "priced_per_stem"
    assert row["regular_price_uzs"] == 18_000, "the price is still recorded, just not pooled"
    assert counts.products_per_stem == 1


def test_products_without_a_category_are_excluded_with_a_reason(built):
    conn, run_id, counts, ids = built
    row = row_for(conn, run_id, ids["no_category"])
    assert row["included"] == 0 and row["exclusion_reason"] == "no_analysis_category"
    assert counts.products_no_category == 1


def test_outliers_are_judged_within_one_shop_s_own_category(built):
    conn, run_id, counts, ids = built
    row = row_for(conn, run_id, ids["extreme"])
    assert row["is_outlier"] == 1
    assert row["included"] == 1, "an outlier stays in the dataset; the robustness check removes it"
    assert counts.products_outliers_flagged == 1
    ordinary = row_for(conn, run_id, ids["plain"])
    assert ordinary["is_outlier"] == 0
    # A 400,000 UZS bouquet among 180,000-390,000 ones is not an outlier: the rule measures distance
    # from the category median in median absolute deviations, not distance from the cheapest.
    assert row_for(conn, run_id, ids["on_sale"])["is_outlier"] == 0


def test_a_missing_stem_count_is_never_invented(built):
    conn, run_id, _, ids = built
    assert row_for(conn, run_id, ids["plain"])["stem_count"] is None


def test_the_stage_counts_account_for_every_row(built):
    """The arithmetic the report quotes: nothing disappears between stages."""
    conn, run_id, counts, _ = built
    assert counts.observations_used == counts.observations_in - counts.observations_from_price
    assert (counts.products_included ==
            counts.products_in - counts.products_no_category - counts.products_per_stem
            - counts.products_starting_price_only)
    stored = conn.execute("SELECT COUNT(*) FROM analysis_products WHERE pipeline_run_id = ?",
                          (run_id,)).fetchone()[0]
    assert stored == counts.products_in
    included = conn.execute("SELECT COUNT(*) FROM v_analysis_dataset").fetchone()[0]
    assert included == counts.products_included


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------

def test_only_the_window_and_the_requested_purpose_are_read(market_db, rules):
    run_id = add_run(market_db, purpose="test")
    fetch = add_fetch(market_db, run_id)
    inside = add_listing(market_db, run_id, "Букет «Внутри»", "in", "bukety")
    outside = add_listing(market_db, run_id, "Букет «Снаружи»", "out", "bukety")
    observe(market_db, inside, run_id, fetch, 300_000, at="2026-11-10T06:00:00Z")
    observe(market_db, outside, run_id, fetch, 300_000, at="2026-10-30T06:00:00Z")
    classify_listings(market_db, rules)
    build_features(market_db, rules)

    pipeline_run_id, counts = build_dataset(market_db, purpose="test", rules_version=rules.version,
                                            **WINDOW)
    assert counts.products_in == 1
    assert row_for(market_db, pipeline_run_id, outside) is None

    with pytest.raises(ValueError, match="no assessed observations"):
        build_dataset(market_db, purpose="assessed", rules_version=rules.version, **WINDOW)


def test_reference_offers_cannot_enter_the_dataset(built):
    """Secret's offers live in another table and are joined later, never summarised as products."""
    conn, run_id, _, _ = built
    sources = conn.execute(
        "SELECT DISTINCT o.source_type FROM price_observations o"
        " JOIN analysis_products p ON p.listing_id = o.listing_id"
        " WHERE p.pipeline_run_id = ?", (run_id,)).fetchall()
    assert {r[0] for r in sources} == {"scrape"}


# ---------------------------------------------------------------------------
# Splits (leakage control)
# ---------------------------------------------------------------------------

def test_grouped_folds_keep_a_listing_in_exactly_one_validation_fold(built):
    conn, run_id, counts, _ = built
    rows = conn.execute(
        "SELECT listing_id, COUNT(*) n FROM dataset_splits WHERE pipeline_run_id = ?"
        " AND split_kind = 'grouped_cv' AND part = 'validation' GROUP BY listing_id",
        (run_id,)).fetchall()
    assert len(rows) == counts.products_included
    assert all(r["n"] == 1 for r in rows), "a listing may be validated in one fold only"
    folds = conn.execute(
        "SELECT COUNT(DISTINCT fold) FROM dataset_splits WHERE pipeline_run_id = ?"
        " AND split_kind = 'grouped_cv'", (run_id,)).fetchone()[0]
    assert folds == CV_FOLDS


def test_leave_one_operator_group_out_holds_out_whole_groups(built):
    conn, run_id, _, _ = built
    rows = conn.execute("""
        SELECT d.fold, COUNT(DISTINCT p.operator_group) AS groups_held_out
        FROM dataset_splits d
        JOIN analysis_products p ON p.listing_id = d.listing_id
                                AND p.pipeline_run_id = d.pipeline_run_id
        WHERE d.pipeline_run_id = ? AND d.split_kind = 'leave_one_group_out'
          AND d.part = 'validation'
        GROUP BY d.fold""", (run_id,)).fetchall()
    assert rows and all(r["groups_held_out"] == 1 for r in rows)


def test_the_chronological_split_puts_later_products_in_the_test_set(built):
    conn, run_id, _, _ = built
    newest_train, oldest_test = conn.execute("""
        SELECT MAX(CASE WHEN d.part = 'train' THEN p.first_observed_at END),
               MIN(CASE WHEN d.part = 'test'  THEN p.first_observed_at END)
        FROM dataset_splits d
        JOIN analysis_products p ON p.listing_id = d.listing_id
                                AND p.pipeline_run_id = d.pipeline_run_id
        WHERE d.pipeline_run_id = ? AND d.split_kind = 'chronological'""", (run_id,)).fetchone()
    assert newest_train <= oldest_test


def test_rebuilding_adds_a_new_dataset_rather_than_overwriting_the_old_one(built, rules):
    conn, first_run, counts, _ = built
    second_run, second_counts = build_dataset(conn, purpose="test", rules_version=rules.version,
                                              **WINDOW)
    assert second_run != first_run
    assert second_counts.products_included == counts.products_included
    assert conn.execute("SELECT COUNT(*) FROM pipeline_runs").fetchone()[0] == 2
    # The view always reads the newest build.
    assert conn.execute("SELECT DISTINCT pipeline_run_id FROM v_analysis_dataset").fetchone()[0] \
        == second_run


def test_the_build_records_how_it_was_made(built):
    conn, run_id, _, _ = built
    row = conn.execute("SELECT * FROM pipeline_runs WHERE pipeline_run_id = ?",
                       (run_id,)).fetchone()
    assert row["pipeline_version"] and row["rules_version"]
    assert row["window_start"] == "2026-11-09" and row["window_end"] == "2026-12-06"
    assert len(row["git_commit"]) == 40 or row["git_commit"] == "unknown"


def test_summary_reports_products_per_category_and_group(built):
    conn, run_id, _, _ = built
    summary = dataset_summary(conn, run_id)
    assert summary and all(r["n_products"] > 0 for r in summary)
    assert all(r["min_price_uzs"] <= r["max_price_uzs"] for r in summary)
