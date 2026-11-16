"""The figures and the robustness checks.

A figure is evidence only if it is labelled and reproducible, so the tests check that each file is a
standalone SVG with a title and a description rather than that it "looks right". The robustness
checks are tested on data built so that one group drives the result: dropping that group must change
the answer, and dropping another must not."""
from pathlib import Path

import numpy as np
import pytest

from priceintel import config
from priceintel.analysis import comparison, eda, robustness
from priceintel.analysis.categories import classify_listings, load_rules
from priceintel.analysis.features import build_features
from priceintel.analysis.pipeline import build_dataset
from tests.conftest import TS, add_fetch, add_run, shop_id

WINDOW = {"window_start": "2026-11-09", "window_end": "2026-12-06"}
HOSTS = {"uzflora": "uzflora.com", "probuket": "pro-buket.uz", "loveflowers": "loveflowers.uz"}


@pytest.fixture
def analysed(market_db):
    rules = load_rules(config.CATEGORY_RULES_FILE)
    run_id = add_run(market_db, purpose="test")
    fetches = {s: add_fetch(market_db, run_id, shop=s, url=f"https://{HOSTS[s]}/") for s in HOSTS}
    rng = np.random.default_rng(11)
    # uzflora and loveflowers price alike; probuket is three times dearer, so it is the group that
    # drives any difference the test finds.
    for shop, centre in (("uzflora", 400_000), ("loveflowers", 420_000), ("probuket", 1_300_000)):
        for i in range(20):
            listing = market_db.execute(
                "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at,"
                " last_seen_at, last_title, site_category) VALUES (?, ?, ?, ?, ?, ?, 'bukety')"
                " RETURNING listing_id",
                (shop_id(market_db, shop), f"https://{HOSTS[shop]}/product/{shop}{i}/", run_id,
                 TS, TS, f"Букет «{shop} {i}»")).fetchone()[0]
            market_db.execute(
                "INSERT INTO price_observations (listing_id, run_id, fetch_id, observed_at,"
                " source_type, title, price_uzs, currency_shown) VALUES (?, ?, ?,"
                " '2026-11-10T06:00:00Z', 'scrape', 'Букет', ?, 'UZS')",
                (listing, run_id, fetches[shop], int(rng.normal(centre, 30_000))))
    classify_listings(market_db, rules)
    build_features(market_db, rules)
    pipeline_run_id, _ = build_dataset(market_db, purpose="test", rules_version=rules.version,
                                       **WINDOW)
    return market_db, pipeline_run_id


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

def test_the_five_required_figures_are_written_and_labelled(analysed, tmp_path):
    conn, run_id = analysed
    figures = eda.write_figures(conn, run_id, tmp_path / "figures")
    assert len(figures) >= 5, "the brief asks for at least five visualisations"
    for path in figures:
        svg = path.read_text(encoding="utf-8")
        assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg, "must stand alone in the report"
        assert "<title>" in svg and "<desc>" in svg, "an unlabelled chart is not evidence"
        assert "chart-title" in svg and "axis-label" in svg


def test_figures_carry_the_numbers_they_claim(analysed, tmp_path):
    conn, run_id = analysed
    eda.write_figures(conn, run_id, tmp_path / "figures")
    coverage = (tmp_path / "figures" / "01_coverage.svg").read_text(encoding="utf-8")
    for group in ("UZFLORA", "PROBUKET", "LOVEFLOWERS_NET"):
        assert group in coverage
    assert "bouquets_unspecified"[:16] in coverage


def test_the_summary_table_reports_median_and_spread(analysed):
    conn, run_id = analysed
    rows = eda.summary_statistics(conn, run_id)
    assert rows
    for row in rows:
        assert row["min_uzs"] <= row["median_uzs"] <= row["max_uzs"]
        assert row["iqr_uzs"] >= 0 and row["n_products"] > 0


# ---------------------------------------------------------------------------
# Robustness
# ---------------------------------------------------------------------------

def test_dropping_the_group_that_drives_the_result_changes_it(analysed):
    conn, run_id = analysed
    outcomes = robustness.run_all(conn, run_id, replicates=100, **WINDOW)
    by_variant = {o.variant: o for o in outcomes}
    assert "drop_probuket" in by_variant and "drop_uzflora" in by_variant

    # probuket is the dear group: without it the remaining two price alike, so the difference goes.
    assert by_variant["drop_probuket"].categories_significant == 0
    # Dropping one of the two similar groups leaves the difference in place.
    assert by_variant["drop_uzflora"].categories_significant >= 1


def test_every_check_is_stored_under_its_own_variant(analysed):
    conn, run_id = analysed
    outcomes = robustness.run_all(conn, run_id, replicates=100, **WINDOW)
    assert len(outcomes) >= 3, "the brief asks for at least three"
    stored = {r[0] for r in conn.execute(
        "SELECT DISTINCT variant FROM comparison_results WHERE pipeline_run_id = ?", (run_id,))}
    for outcome in outcomes:
        if outcome.n_products:
            assert outcome.variant in stored


def test_the_main_comparison_is_kept_beside_the_checks(analysed):
    conn, run_id = analysed
    comparison.run_comparison(conn, run_id, replicates=100)
    robustness.run_all(conn, run_id, replicates=100, **WINDOW)
    variants = {r[0] for r in conn.execute(
        "SELECT DISTINCT variant FROM comparison_results WHERE pipeline_run_id = ?", (run_id,))}
    assert "main" in variants and len(variants) > 3


def test_the_window_is_split_at_its_midpoint():
    assert robustness._midpoint("2026-11-09", "2026-12-06") == "2026-11-22"
