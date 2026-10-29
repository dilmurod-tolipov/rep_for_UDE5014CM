"""Data-quality checks and the committed data snapshot.

The checks are evidence about the dataset, so what matters in a test is that each one measures the
right thing and that a breach is reported as a breach - not that everything passes."""
import csv

import pytest

from priceintel import config
from priceintel.analysis.categories import classify_listings, load_rules
from priceintel.quality import run_checks
from priceintel.snapshot import write_snapshot
from tests.conftest import TS, add_fetch, add_observation, add_run, shop_id


@pytest.fixture
def rules():
    return load_rules(config.CATEGORY_RULES_FILE)


def add_listing(conn, run_id, title, slug, site_category="bukety", shop="uzflora"):
    return conn.execute(
        "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
        " last_title, site_category) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING listing_id",
        (shop_id(conn, shop), f"https://uzflora.com/product/{slug}/", run_id, TS, TS, title,
         site_category)).fetchone()[0]


@pytest.fixture
def collected(market_db, rules):
    """Three products collected in one successful run, one record quarantined."""
    run_id = add_run(market_db, purpose="test")
    fetch = add_fetch(market_db, run_id)
    for i, price in enumerate((200_000, 300_000, 400_000), start=1):
        listing = add_listing(market_db, run_id, f"Букет {i}", f"b{i}")
        add_observation(market_db, listing, run_id, fetch, price=price)
    market_db.execute(
        "INSERT INTO rejected_records (run_id, fetch_id, shop_id, rejected_at, rule, detail,"
        " raw_payload) VALUES (?, ?, ?, ?, 'missing_price', 'no price on card', '{}')",
        (run_id, fetch, shop_id(market_db, "uzflora"), TS))
    market_db.execute(
        "UPDATE scrape_runs SET status = 'success', finished_at = ?, pages_requested = 2,"
        " pages_ok = 2, observations_saved = 3, records_rejected = 1 WHERE run_id = ?",
        (TS, run_id))
    classify_listings(market_db, rules)
    return market_db


def result(results, name):
    return next(r for r in results if r.check_name == name)


def test_checks_measure_the_dataset_and_are_recorded(collected, rules):
    results = run_checks(collected, purpose="test", rules_version=rules.version)
    assert result(results, "products_collected").measured == 3
    assert result(results, "runs_completed").measured == 1
    assert result(results, "run_success_rate").measured == 100.0
    # one rejected of four parsed records = 25%
    assert result(results, "quarantine_rate").measured == 25.0
    assert "missing_price" in result(results, "quarantine_rate").detail
    stored = collected.execute("SELECT COUNT(*) FROM data_quality_checks").fetchone()[0]
    assert stored == len(results)


def test_missing_the_data_target_is_reported_as_a_failure(collected, rules):
    results = run_checks(collected, purpose="test", rules_version=rules.version, store=False)
    products = result(results, "products_collected")
    assert products.threshold == 300 and products.status == "fail"   # 3 of 300
    assert result(results, "quarantine_rate").status == "fail"       # 25% against a 5% threshold


def test_integrity_checks_pass_because_the_schema_enforces_them(collected, rules):
    results = run_checks(collected, purpose="test", rules_version=rules.version, store=False)
    assert result(results, "duplicate_observations").measured == 0
    assert result(results, "orphan_observations").measured == 0
    assert result(results, "duplicate_observations").status == "pass"


def test_stale_data_is_visible(collected, rules):
    """The fixture's observations are dated 2026-10-20, so freshness must breach its threshold."""
    assert result(run_checks(collected, purpose="test", rules_version=rules.version, store=False),
                  "freshness_days").status == "fail"


def test_checks_only_see_the_requested_purpose(collected, rules):
    results = run_checks(collected, purpose="assessed", rules_version=rules.version, store=False)
    assert result(results, "products_collected").measured == 0


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------

def test_snapshot_exports_data_with_provenance_and_a_manifest(collected, rules, tmp_path):
    run_checks(collected, purpose="test", rules_version=rules.version)
    out = write_snapshot(collected, tmp_path / "snap", purpose="test", label="unit-test")

    assert out.rows["price_observations"] == 3
    assert out.rows["listings"] == 3
    assert out.rows["rejected_records"] == 1
    assert out.rows["fetch_log"] >= 1           # the provenance of every price
    assert out.rows["data_quality_checks"] > 0

    with (out.directory / "price_observations.csv").open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert {r["source_type"] for r in rows} == {"scrape"}
    assert all(r["fetch_id"] for r in rows), "every exported price must name its HTTP request"

    manifest = (out.directory / "MANIFEST.md").read_text(encoding="utf-8")
    assert "Purpose filter: `test`" in manifest
    assert out.sha256["price_observations"] in manifest
    assert "Secret reference offers included: no" in manifest


def test_snapshot_never_mixes_purposes(collected, rules, tmp_path):
    other = add_run(collected, purpose="dev")
    fetch = add_fetch(collected, other)
    listing = add_listing(collected, other, "Букет dev", "dev1")
    add_observation(collected, listing, other, fetch, price=999_000)

    out = write_snapshot(collected, tmp_path / "snap", purpose="test")
    with (out.directory / "price_observations.csv").open(encoding="utf-8") as fh:
        prices = {int(r["price_uzs"]) for r in csv.DictReader(fh)}
    assert 999_000 not in prices
    assert out.rows["scrape_runs"] == 1


def test_reference_offers_are_exported_only_when_asked(collected, tmp_path):
    without = write_snapshot(collected, tmp_path / "a", purpose="test")
    assert "reference_offers" not in without.rows
    with_ref = write_snapshot(collected, tmp_path / "b", purpose="test", include_reference=True)
    assert "reference_offers" in with_ref.rows
    assert "Secret reference offers included: yes" in (
        with_ref.directory / "MANIFEST.md").read_text(encoding="utf-8")
