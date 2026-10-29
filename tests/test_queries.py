"""The five stakeholder queries: each one runs, and each answers its question correctly on a small
dataset built so that the right answer is known by hand.

The fixture gives UZFLORA four bouquets: three at 200k / 300k / 400k and one discounted to 260k from
400k, which counts at its regular (old) price, so the competitor median is 350k. Secret has three
offers at 330k / 360k / 390k, median 360k, so Q1 must report +2.9% (360/350 - 1). One UZFLORA product
is observed twice at different prices, which also proves repeated observations are collapsed."""
import pytest

from priceintel import config
from priceintel.analysis.categories import classify_listings, load_rules
from priceintel.queries import QueryError, available, format_table, question_of, run
from priceintel.reference.offers import import_offers
from tests.conftest import TS, add_fetch, add_run, shop_id

QUERIES = available(config.QUERIES_DIR)


def params(**over):
    base = {"rules_version": "1.1.0", "purpose": "test", "min_items": 3, "limit": 20}
    return base | over


def add_product(conn, run_id, fetch_id, title, price, *, shop="uzflora", slug, old=None,
                observed_at=TS, site_category="bukety"):
    host = {"uzflora": "uzflora.com", "probuket": "pro-buket.uz"}[shop]
    listing_id = conn.execute(
        "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
        " last_title, site_category) VALUES (?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT (shop_id, url) DO UPDATE SET last_seen_at = excluded.last_seen_at"
        " RETURNING listing_id",
        (shop_id(conn, shop), f"https://{host}/product/{slug}/", run_id, TS, observed_at, title,
         site_category)).fetchone()[0]
    conn.execute(
        "INSERT INTO price_observations (listing_id, run_id, fetch_id, observed_at, source_type,"
        " title, price_uzs, old_price_uzs) VALUES (?, ?, ?, ?, 'scrape', ?, ?, ?)",
        (listing_id, run_id, fetch_id, observed_at, title, price, old))
    return listing_id


@pytest.fixture
def market(market_db, tmp_path):
    rules = load_rules(config.CATEGORY_RULES_FILE)
    first = add_run(market_db, purpose="test")
    fetch1 = add_fetch(market_db, first)
    for i, price in enumerate((200_000, 300_000, 400_000), start=1):
        add_product(market_db, first, fetch1, f"Букет {i}", price, slug=f"b{i}")
    add_product(market_db, first, fetch1, "Букет со скидкой", 260_000, slug="sale", old=400_000)
    # A second run: one product changes price, which Q3 must find and Q1 must collapse.
    second = add_run(market_db, purpose="test")
    fetch2 = add_fetch(market_db, second)
    add_product(market_db, second, fetch2, "Букет 1", 240_000, slug="b1",
                observed_at="2026-10-21T06:00:00Z")
    # Secret: three bouquet offers at 330k / 360k / 390k, so the median is 360k. Imported through
    # the real importer (CSV fallback shape) rather than inserted by hand.
    csv_path = tmp_path / "secret_offers.csv"
    lines = ["published_at,post_url,price_uzs,title"]
    for i, price in enumerate((330_000, 360_000, 390_000), start=1):
        lines.append(f"2026-11-0{i}T09:00:00,https://t.me/secret_flowersuz/90{i},{price},"
                     f"Букет Secret {i}")
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    import_offers(market_db, csv_path, exported_at="2026-11-21", consent_note="synthetic test data",
                  purpose="test", rules=rules)
    classify_listings(market_db, rules)
    return market_db


@pytest.mark.parametrize("name", sorted(n for n in QUERIES if n[0].isdigit()))
def test_every_query_runs_and_states_its_question(market, name):
    columns, rows = run(market, QUERIES[name], params())
    assert columns, f"{name} returned no columns"
    assert question_of(QUERIES[name]).startswith("Q")
    format_table(columns, rows)        # must not raise on real output


def test_price_position_uses_regular_prices_and_the_minimum_evidence_rule(market):
    columns, rows = run(market, QUERIES["01_price_position_by_category"], params())
    row = dict(zip(columns, next(r for r in rows if r[0] == "bouquets_unspecified")))
    # Competitor median over 4 products: 200k, 300k, 400k and the discounted one at its OLD price
    # (400k) -> median 350k. Secret median 360k -> +2.9%.
    assert row["competitor_products"] == 4
    assert row["competitor_median_uzs"] == 350_000
    assert row["secret_median_uzs"] == 360_000
    assert row["difference_pct"] == pytest.approx(2.9, abs=0.05)
    assert row["evidence"] == "displayed"


def test_price_position_hides_a_comparison_with_too_little_evidence(market):
    columns, rows = run(market, QUERIES["01_price_position_by_category"], params(min_items=10))
    assert rows and all(dict(zip(columns, r))["evidence"] == "insufficient_evidence" for r in rows)


def test_coverage_counts_products_not_observations(market):
    columns, rows = run(market, QUERIES["02_category_coverage"], params())
    row = dict(zip(columns, rows[0]))
    assert row["n_products"] == 4 and row["secret_offers"] == 3
    assert row["verdict"] == "comparison can be displayed"


def test_price_changes_finds_the_one_product_that_moved(market):
    columns, rows = run(market, QUERIES["03_price_changes"], params())
    assert len(rows) == 1
    row = dict(zip(columns, rows[0]))
    assert (row["was_uzs"], row["now_uzs"], row["change_uzs"]) == (200_000, 240_000, 40_000)
    assert row["change_pct"] == pytest.approx(20.0)


def test_collection_health_reports_runs_and_quarantine(market):
    columns, rows = run(market, QUERIES["04_collection_health"], params())
    row = dict(zip(columns, rows[0]))
    assert row["runs"] == 2 and row["records_quarantined"] == 0


def test_discounts_use_the_latest_observation_only(market):
    columns, rows = run(market, QUERIES["05_discounts_in_market"], params())
    row = dict(zip(columns, rows[0]))
    assert row["products"] == 4 and row["on_sale"] == 1
    assert row["mean_discount_pct"] == pytest.approx(35.0)


def test_a_missing_parameter_is_refused_rather_than_guessed(market):
    with pytest.raises(QueryError, match="needs parameter"):
        run(market, QUERIES["01_price_position_by_category"], {"purpose": "test"})
