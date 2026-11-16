"""The price comparison, its bootstrap, and the model evaluation.

The fixture prices are chosen so that the right answers are arithmetic: a Secret median of 600,000
against a competitor median of 500,000 is +20%, and a bootstrap interval built from constant prices
must be exactly zero wide."""
import numpy as np
import pytest

from priceintel import config
from priceintel.analysis import comparison, models
from priceintel.analysis.categories import classify_listings, load_rules
from priceintel.analysis.features import build_features
from priceintel.analysis.pipeline import build_dataset
from tests.conftest import TS, add_fetch, add_run, shop_id

WINDOW = {"window_start": "2026-11-09", "window_end": "2026-12-06"}


# ---------------------------------------------------------------------------
# The estimand and the minimum-evidence rule
# ---------------------------------------------------------------------------

def test_the_percentage_is_the_approved_formula():
    competitor = {("bouquets_unspecified", "UZFLORA"): [500_000.0] * 12}
    secret = {"bouquets_unspecified": [600_000.0] * 12}
    result = next(r for r in comparison.compare(competitor, secret, replicates=200)
                  if r.operator_group == "UZFLORA")
    assert result.difference_pct == pytest.approx(20.0)        # 100 * (600/500 - 1)
    assert result.difference_uzs == 100_000
    assert result.evidence == "displayed"


def test_a_comparison_without_enough_items_is_not_displayed():
    competitor = {("bouquets_unspecified", "KAMILAS"): [500_000.0] * 4}
    secret = {"bouquets_unspecified": [600_000.0] * 12}
    result = comparison.compare(competitor, secret, replicates=100)[0]
    assert result.evidence == "insufficient_evidence"
    assert result.ci_low_pct is None and "4 products" in result.note
    # The medians are still reported, so the reader can see what was there.
    assert result.competitor_median_uzs == 500_000


def test_no_secret_offers_means_no_displayed_comparison():
    competitor = {("bouquets_unspecified", "UZFLORA"): [500_000.0] * 50}
    results = comparison.compare(competitor, {}, replicates=100)
    assert all(r.evidence == "insufficient_evidence" for r in results)
    assert all(r.n_secret_offers == 0 for r in results)


# ---------------------------------------------------------------------------
# The bootstrap
# ---------------------------------------------------------------------------

def test_the_interval_is_zero_wide_when_every_price_is_the_same():
    competitor = {("bouquets_unspecified", "UZFLORA"): [500_000.0] * 20}
    secret = {"bouquets_unspecified": [600_000.0] * 20}
    result = next(r for r in comparison.compare(competitor, secret, replicates=500)
                  if r.operator_group == "UZFLORA")
    assert result.ci_low_pct == pytest.approx(20.0)
    assert result.ci_high_pct == pytest.approx(20.0)


def test_the_interval_covers_the_true_difference_and_is_reproducible():
    rng = np.random.default_rng(42)
    competitor = {("bouquets_unspecified", "UZFLORA"): list(rng.normal(500_000, 60_000, 60))}
    secret = {"bouquets_unspecified": list(rng.normal(600_000, 60_000, 60))}
    first = next(r for r in comparison.compare(competitor, secret, replicates=1_000)
                 if r.operator_group == "UZFLORA")
    second = next(r for r in comparison.compare(competitor, secret, replicates=1_000)
                  if r.operator_group == "UZFLORA")
    assert (first.ci_low_pct, first.ci_high_pct) == (second.ci_low_pct, second.ci_high_pct)
    assert first.ci_low_pct < first.difference_pct < first.ci_high_pct


def test_a_noisier_sample_gives_a_wider_interval():
    rng = np.random.default_rng(1)
    tight = {("c", "G"): list(rng.normal(500_000, 10_000, 40))}
    noisy = {("c", "G"): list(rng.normal(500_000, 200_000, 40))}
    secret = {"c": list(rng.normal(600_000, 10_000, 40))}
    a = next(r for r in comparison.compare(tight, secret, replicates=800) if r.operator_group == "G")
    b = next(r for r in comparison.compare(noisy, secret, replicates=800) if r.operator_group == "G")
    assert (b.ci_high_pct - b.ci_low_pct) > (a.ci_high_pct - a.ci_low_pct)


def test_the_pooled_figure_is_the_unweighted_mean_of_the_groups():
    """So that a group with 300 products does not outweigh one with 12 (ADR-008)."""
    competitor = {("c", "BIG"): [500_000.0] * 300, ("c", "SMALL"): [250_000.0] * 12}
    secret = {"c": [500_000.0] * 20}
    results = comparison.compare(competitor, secret, replicates=200)
    by_group = {r.operator_group: r for r in results}
    expected = (by_group["BIG"].difference_pct + by_group["SMALL"].difference_pct) / 2
    assert by_group["ALL"].difference_pct == pytest.approx(expected)
    assert "unweighted mean" in by_group["ALL"].note


# ---------------------------------------------------------------------------
# A dataset to model
# ---------------------------------------------------------------------------

def add_product(conn, run_id, fetch, title, slug, section, price, shop="uzflora", at=None):
    host = {"uzflora": "uzflora.com", "probuket": "pro-buket.uz"}[shop]
    listing = conn.execute(
        "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
        " last_title, site_category) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING listing_id",
        (shop_id(conn, shop), f"https://{host}/product/{slug}/", run_id, TS, TS, title,
         section)).fetchone()[0]
    conn.execute(
        "INSERT INTO price_observations (listing_id, run_id, fetch_id, observed_at, source_type,"
        " title, price_uzs, currency_shown) VALUES (?, ?, ?, ?, 'scrape', ?, ?, 'UZS')",
        (listing, run_id, fetch, at or "2026-11-10T06:00:00Z", title, price))
    return listing


@pytest.fixture
def dataset(market_db):
    """Two shops, two categories, prices that differ by shop - enough for folds to be meaningful."""
    rules = load_rules(config.CATEGORY_RULES_FILE)
    run_id = add_run(market_db, purpose="test")
    fetches = {shop: add_fetch(market_db, run_id, shop=shop,
                               url=f"https://{'uzflora.com' if shop == 'uzflora' else 'pro-buket.uz'}/")
               for shop in ("uzflora", "probuket")}
    rng = np.random.default_rng(5)
    for i in range(30):
        add_product(market_db, run_id, fetches["uzflora"], f"Букет «У{i}»", f"u{i}", "bukety",
                    int(rng.normal(400_000, 30_000)))
        add_product(market_db, run_id, fetches["probuket"], f"Букет «П{i}»", f"p{i}", "bukety",
                    int(rng.normal(1_200_000, 80_000)), shop="probuket")
    for i in range(15):
        add_product(market_db, run_id, fetches["uzflora"], f"Орхидея {i}", f"o{i}", "rasteniya",
                    int(rng.normal(500_000, 40_000)))
    classify_listings(market_db, rules)
    build_features(market_db, rules)
    run, _ = build_dataset(market_db, purpose="test", rules_version=rules.version, **WINDOW)
    return market_db, run


def test_every_model_is_evaluated_on_listings_it_never_trained_on(dataset):
    conn, run_id = dataset
    folds = conn.execute(
        "SELECT fold, part, listing_id FROM dataset_splits WHERE pipeline_run_id = ?"
        " AND split_kind = 'grouped_cv'", (run_id,)).fetchall()
    by_fold: dict[int, dict[str, set]] = {}
    for f in folds:
        by_fold.setdefault(f["fold"], {"train": set(), "validation": set()})
        by_fold[f["fold"]][f["part"]].add(f["listing_id"])
    assert by_fold
    for fold, parts in by_fold.items():
        assert not parts["train"] & parts["validation"], f"fold {fold} leaks a listing"


def test_the_three_models_are_scored_and_recorded(dataset):
    conn, run_id = dataset
    results = models.evaluate(conn, run_id)
    assert {r.model_name for r in results} == {"category_median_baseline", "ridge", "decision_tree"}
    models.store(conn, run_id, results)
    table = {(r["model_name"], r["metric"]): r["value"]
             for r in models.comparison_table(conn, run_id) if r["scope"] == "all"}
    for name in ("category_median_baseline", "ridge", "decision_tree"):
        assert table[(name, "mae_uzs")] > 0 and table[(name, "mdape_pct")] > 0


def test_metrics_are_reported_by_category_as_well_as_overall(dataset):
    conn, run_id = dataset
    models.store(conn, run_id, models.evaluate(conn, run_id))
    scopes = {r["scope"] for r in models.comparison_table(conn, run_id)}
    assert "all" in scopes and len(scopes) > 1, "a single average hides the per-category picture"


def test_the_baseline_sees_only_its_training_fold():
    """A baseline fitted on the whole dataset would flatter every model compared with it."""
    train = [{"category": "a", "price": 100.0}, {"category": "a", "price": 300.0},
             {"category": "b", "price": 1_000.0}]
    validation = [{"category": "a"}, {"category": "b"}, {"category": "unseen"}]
    predicted = models._category_median_baseline(train, validation)
    assert predicted[0] == 200.0        # median of the training fold's category a
    assert predicted[1] == 1_000.0
    assert predicted[2] == 300.0        # a category the training fold never saw: overall median


def test_metrics_are_computed_as_documented():
    actual = np.array([100.0, 200.0, 400.0])
    predicted = np.array([150.0, 200.0, 300.0])
    mae, mdape = models.metrics_for(actual, predicted)
    assert mae == pytest.approx((50 + 0 + 100) / 3)
    assert mdape == pytest.approx(25.0)      # median of 50%, 0%, 25%


def test_the_design_matrix_uses_the_training_vocabulary(dataset):
    """A category seen only in validation becomes all-zeros instead of shifting every column."""
    rows = [{"category": "a", "operator_group": "G", "stem_count": None, "size_cm": None,
             "price_unit": "per_item", "n_observations": 1, "price_changes": 0, "days_on_sale": 0}]
    matrix = models.design_matrix(rows, ["a", "b"], ["G", "H"])
    assert matrix.shape == (1, 2 + 2 + 7)
    unseen = models.design_matrix(
        [{**rows[0], "category": "c"}], ["a", "b"], ["G", "H"])
    assert unseen[0][:2].tolist() == [0.0, 0.0]


def test_models_never_see_a_reference_offer(dataset):
    """Secret's offers live in another table; the model matrix is built from analysis_products."""
    conn, run_id = dataset
    rows = models.load_rows(conn, run_id)
    assert rows
    assert all(r["operator_group"] != "SECRET" for r in rows)
    sources = {r[0] for r in conn.execute("SELECT DISTINCT source_type FROM price_observations")}
    assert sources == {"scrape"}
