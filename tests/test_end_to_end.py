"""Checkpoint 4: a new record travels from a web page to the decision the owner reads.

The brief's Checkpoint 4 asks for an "operational end-to-end release candidate integrating live
collection, database, pipeline, analysis/model and application" where "a user or source can add a
new record and the system produces an updated operational or decision-support output", proved by a
"reproducible end-to-end new-record test".

That is this file. A scripted fetcher stands in for the four shops - no network, so the test is
reproducible anywhere - and everything downstream is the real code: the real parsers, the real
validator, the real database with its constraints and triggers, the real cleaning pipeline, the real
statistics, the real dashboard.

The test that matters is the last one: collect, analyse and read the decision; then a shop changes
its catalogue, collect again, and the decision the dashboard shows must change with it.
"""
import json

import pytest

from priceintel import config
from priceintel.analysis import comparison, hypothesis, models
from priceintel.analysis.categories import classify_listings, load_rules
from priceintel.analysis.features import build_features
from priceintel.analysis.pipeline import build_dataset
from priceintel.collect.http import FetchAttempt
from priceintel.collect.runner import collect
from priceintel.db import connect
from priceintel.web.data import Databases, Selection, decision_table
from priceintel.web.views import render
from tests.conftest import FAKE_COMMIT

ROBOTS = "User-agent: *\nAllow: /\n"
WINDOW = {"window_start": "2026-11-09", "window_end": "2026-12-06"}
TODAY = "2026-11-20T06:00:00Z"


def uzflora_card(name: str, price: int) -> str:
    return (f'<li class="uz-product-card product instock product_cat-bukety post-{abs(hash(name)) % 9999}">'
            f'<span class="product-price">{price:,} '
            f'<span class="woocommerce-Price-currencySymbol">UZS</span></span>'
            f'<a class="product-name" href="https://uzflora.com/product/{abs(hash(name)) % 9999}/">'
            f'{name}</a></li>').replace(",", " ")


def probuket_card(name: str, price: int) -> str:
    return (f'<div class="pr-bl" data-cat="bukety" data-id="{abs(hash(name)) % 9999}">'
            f'<div class="h-3"><a href="/c/all/p/{abs(hash(name)) % 9999}/">{name}</a></div>'
            f'<div class="pr-status pr-status--on">В наличии</div>'
            f'<div class="price"><span class="pay_arr" data-pay="UZS" data-val="{price}">'
            f'{price}</span></div>'
            f'<div class="hide-bl"><p><strong>Состав:</strong> розы — 15 шт.</p></div></div>')


class ScriptedFetcher:
    """Serves pages from a dict instead of the internet, so the test is reproducible offline."""

    def __init__(self, pages: dict[str, str]):
        self.pages = pages
        self.timeout_s = 30
        self.now = lambda: TODAY

    def get(self, url, min_delay_s, *, max_attempts=None, backoff_s=None):
        body = self.pages.get(url)
        status = 200 if body is not None else 404
        return [FetchAttempt(url, TODAY, 1, status, (body or "").encode("utf-8"), 1, None)]


def pages_for(uzflora_prices: list[int], probuket_prices: list[int]) -> dict[str, str]:
    pages = {"https://uzflora.com/robots.txt": ROBOTS, "https://pro-buket.uz/robots.txt": ROBOTS}
    pages["https://uzflora.com/shop/?currency=UZS"] = "<ul>" + "".join(
        uzflora_card(f"Букет «У{i}»", p) for i, p in enumerate(uzflora_prices)) + "</ul>"
    pages["https://pro-buket.uz/catalog/"] = "".join(
        probuket_card(f"Букет «П{i}»", p) for i, p in enumerate(probuket_prices))
    return pages


def collect_and_analyse(conn, pages, *, replicates=200):
    """The whole chain, exactly as `python -m priceintel refresh` runs it."""
    rules = load_rules(config.CATEGORY_RULES_FILE)
    summary = collect(conn, ["uzflora", "probuket"], purpose="test",
                      fetcher=ScriptedFetcher(pages), git=(FAKE_COMMIT, False))
    classify_listings(conn, rules)
    build_features(conn, rules)
    run_id, stages = build_dataset(conn, purpose="test", rules_version=rules.version, **WINDOW)
    tests = hypothesis.groups_differ_within_category(comparison.competitor_prices(conn, run_id))
    hypothesis.store(conn, run_id, tests)
    comparison.run_comparison(conn, run_id, replicates=replicates)
    models.store(conn, run_id, models.evaluate(conn, run_id))
    return summary, run_id, stages


@pytest.fixture
def system(market_db, tmp_path):
    """A system with one round of collection behind it."""
    pages = pages_for([400_000 + i * 10_000 for i in range(12)],
                      [1_200_000 + i * 20_000 for i in range(12)])
    summary, run_id, stages = collect_and_analyse(market_db, pages)
    secret_path = tmp_path / "secret_shop.db"
    from priceintel.db import init_secret_db
    init_secret_db(secret_path, config.SECRET_MIGRATIONS, config.SECRET_SOURCES_FILE)
    db = Databases(market_db, connect(secret_path), __import__(
        "priceintel.queries", fromlist=["available"]).available(config.QUERIES_DIR))
    return db, run_id, summary, stages


def get(db, path, **params):
    return render(path, {k: [str(v)] for k, v in params.items()}, db)


# ---------------------------------------------------------------------------
# The chain
# ---------------------------------------------------------------------------

def test_collection_stores_records_with_full_provenance(system):
    db, run_id, summary, _ = system
    assert summary.status == "success" and summary.observations_saved == 24
    row = db.market.execute("""
        SELECT o.price_uzs, o.currency_shown, f.url, f.content_sha256, r.git_commit, r.git_dirty
        FROM price_observations o
        JOIN fetch_log f ON f.fetch_id = o.fetch_id
        JOIN scrape_runs r ON r.run_id = o.run_id LIMIT 1""").fetchone()
    assert row["currency_shown"] == "UZS"
    assert row["url"].startswith("https://") and len(row["content_sha256"]) == 64
    assert len(row["git_commit"]) == 40 and row["git_dirty"] == 0


def test_the_pipeline_turns_those_records_into_a_dataset(system):
    _, run_id, _, stages = system
    assert stages.products_in == 24 and stages.products_included == 24


def test_the_analysis_runs_on_that_dataset(system):
    db, run_id, _, _ = system
    tests = db.market.execute("SELECT COUNT(*) FROM hypothesis_tests WHERE pipeline_run_id = ?",
                              (run_id,)).fetchone()[0]
    comparisons = db.market.execute(
        "SELECT COUNT(*) FROM comparison_results WHERE pipeline_run_id = ?", (run_id,)).fetchone()[0]
    model_runs = db.market.execute("SELECT COUNT(*) FROM model_runs WHERE pipeline_run_id = ?",
                                   (run_id,)).fetchone()[0]
    assert tests >= 1 and comparisons >= 2 and model_runs == 3


@pytest.mark.parametrize("path, title", [("/", "Overview"), ("/decision", "What to look at"),
                                         ("/analysis", "Analysis"), ("/models", "Models"),
                                         ("/coverage", "Coverage"),
                                         ("/price-position", "Price position"),
                                         ("/quality", "Data quality")])
def test_every_page_serves_the_new_build(system, path, title):
    db, _, _, _ = system
    response = get(db, path, purpose="test")
    assert response.status == 200
    assert title in response.body
    assert "No analysis has been built" not in response.body, f"{path} cannot see the new build"


def test_the_api_serves_the_same_figures(system):
    db, _, _, _ = system
    payload = json.loads(get(db, "/api/02_category_coverage.json", purpose="test").body)
    assert payload["rows"], "the API must answer from the same data the pages show"


# ---------------------------------------------------------------------------
# The test the checkpoint is for
# ---------------------------------------------------------------------------

def test_a_new_record_changes_the_decision_the_dashboard_shows(system):
    """Collect, read the decision; a shop raises its prices; collect again; the decision moves.

    This is the end-to-end claim of the whole project: a source adds records and the system produces
    an updated decision-support output, with no manual step in between."""
    db, run_id, _, _ = system
    before = [r for r in decision_table(db.market, run_id) if r["evidence"] == "displayed"]
    assert before, "the first build must already produce a decision"
    spread_before = before[0]["spread_pct"]
    page_before = get(db, "/decision", purpose="test").body
    assert f"{spread_before:.0f}%" in page_before

    # PROBUKET doubles its prices and adds a product: new records, same system.
    pages = pages_for([400_000 + i * 10_000 for i in range(12)],
                      [2_400_000 + i * 40_000 for i in range(13)])
    _, new_run_id, stages = collect_and_analyse(db.market, pages)

    after = [r for r in decision_table(db.market, new_run_id) if r["evidence"] == "displayed"]
    spread_after = after[0]["spread_pct"]
    assert stages.products_in == 25, "the new product is in the dataset"
    assert spread_after > spread_before * 1.5, (
        f"the gap between the shops widened from {spread_before}% to {spread_after}%, and the "
        f"decision output must move with it")

    page_after = get(db, "/decision", purpose="test").body
    assert f"{spread_after:.0f}%" in page_after
    assert page_after != page_before


def test_the_decision_output_obeys_the_minimum_evidence_rule(system):
    """A category where one group has a single product must not set the headline: the first version
    of this table sent the owner to potted plants on a 3,948% spread, from one product."""
    db, run_id, _, _ = system
    conn = db.market
    # One potted plant per group, each a real listing: a category no one can compare on two items.
    collection_run = conn.execute("SELECT run_id FROM scrape_runs LIMIT 1").fetchone()[0]
    for shop, host, price in (("probuket", "pro-buket.uz", 50_000_000),
                              ("uzflora", "uzflora.com", 45_000)):
        shop_id = conn.execute("SELECT shop_id FROM shops WHERE code = ?", (shop,)).fetchone()[0]
        listing_id = conn.execute(
            "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
            " last_title, site_category) VALUES (?, ?, ?, ?, ?, 'Орхидея', 'rasteniya')"
            " RETURNING listing_id",
            (shop_id, f"https://{host}/product/orchid/", collection_run, TODAY,
             TODAY)).fetchone()[0]
        conn.execute(
            "INSERT INTO analysis_products (pipeline_run_id, listing_id, operator_group, category,"
            " price_unit, regular_price_uzs, n_observations, observed_days, first_observed_at,"
            " last_observed_at, included) VALUES (?, ?, ?, 'potted_plants', 'per_item', ?, 1, 1,"
            " ?, ?, 1)",
            (run_id, listing_id, "PROBUKET" if shop == "probuket" else "UZFLORA", price, TODAY,
             TODAY))
    rows = {r["category"]: r for r in decision_table(conn, run_id)}
    assert rows["potted_plants"]["evidence"] == "insufficient_evidence"
    assert "needs two groups" in rows["potted_plants"]["note"]
    displayed = [r for r in decision_table(conn, run_id) if r["evidence"] == "displayed"]
    assert all(r["category"] != "potted_plants" for r in displayed)


def test_a_failed_collection_does_not_rebuild_the_decision(market_db):
    """If collection fails, the dashboard keeps showing the last good build rather than an empty
    one: `refresh` stops at the first stage that fails."""
    pages = {"https://uzflora.com/robots.txt": ROBOTS}      # no catalogue page: nothing to parse
    summary = collect(market_db, ["uzflora"], purpose="test", fetcher=ScriptedFetcher(pages),
                      git=(FAKE_COMMIT, False))
    assert summary.status == "failed"
    assert market_db.execute("SELECT COUNT(*) FROM analysis_products").fetchone()[0] == 0
