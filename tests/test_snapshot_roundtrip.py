"""A snapshot must be enough on its own to rebuild the database and redo the analysis.

The brief requires that the assessed system "reproduce the analysis from its saved data", and the
approval decision repeats it: without the student's machine, without a Telegram account, without the
working databases. That is only true if a committed snapshot can be loaded back with foreign keys
enforced and the pipeline re-run on it.

Replaying a real snapshot on 2026-11-13 found two things this test now guards:

1. the snapshot did not export the category vocabulary or the rules-file provenance, so every
   category assignment in it pointed at rows that did not exist;
2. filtering by purpose dropped the development run that a listing was *first seen* in, breaking
   `listings.first_seen_run_id` - a listing collected first in development and then in the window
   could not be loaded back at all.
"""
import subprocess
import sys
from pathlib import Path

import pytest

from priceintel import config
from priceintel.analysis.categories import classify_listings, load_rules
from priceintel.analysis.features import build_features
from priceintel.analysis.pipeline import build_dataset
from priceintel.db import connect, migrate
from priceintel.snapshot import write_snapshot
from tests.conftest import add_fetch, add_run, shop_id

REPO = Path(__file__).resolve().parent.parent
WINDOW = {"window_start": "2026-11-09", "window_end": "2026-12-06"}


@pytest.fixture
def collected(market_db):
    """A listing first seen in a development run, then observed again inside the window - the shape
    that broke the replay."""
    rules = load_rules(config.CATEGORY_RULES_FILE)
    dev_run = add_run(market_db, purpose="dev")
    assessed_run = add_run(market_db, purpose="test")
    listing = market_db.execute(
        "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
        " last_title, site_category) VALUES (?, 'https://uzflora.com/product/b1/', ?,"
        " '2026-11-05T06:00:00Z', '2026-11-10T06:00:00Z', 'Букет «Тест»', 'bukety')"
        " RETURNING listing_id", (shop_id(market_db, "uzflora"), dev_run)).fetchone()[0]
    for run, at, price in ((dev_run, "2026-11-05T06:00:00Z", 300_000),
                           (assessed_run, "2026-11-10T06:00:00Z", 320_000)):
        fetch = add_fetch(market_db, run)
        market_db.execute(
            "INSERT INTO price_observations (listing_id, run_id, fetch_id, observed_at,"
            " source_type, title, price_uzs, currency_shown) VALUES (?, ?, ?, ?, 'scrape',"
            " 'Букет «Тест»', ?, 'UZS')", (listing, run, fetch, at, price))
    classify_listings(market_db, rules)
    build_features(market_db, rules)
    build_dataset(market_db, purpose="test", rules_version=rules.version, **WINDOW)
    return market_db, rules


def test_a_snapshot_can_be_loaded_back_with_foreign_keys_enforced(collected, tmp_path):
    conn, rules = collected
    out = write_snapshot(conn, tmp_path / "snap", purpose="test", label="roundtrip")

    replay_path = tmp_path / "replay.db"
    result = subprocess.run(
        [sys.executable, str(REPO / "tools" / "load_snapshot.py"), str(out.directory),
         "--db", str(replay_path)],
        capture_output=True, text=True, cwd=REPO)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "integrity: OK" in result.stdout

    replay = connect(replay_path)
    assert replay.execute("PRAGMA foreign_key_check").fetchall() == []
    assert replay.execute("SELECT COUNT(*) FROM listings").fetchone()[0] == 1
    # One observation, not two: the development run travels as provenance, but its observations do
    # not - a snapshot holds one purpose only, so assessed data can never be mixed with test data.
    assert replay.execute("SELECT COUNT(*) FROM price_observations").fetchone()[0] == 1
    assert replay.execute("SELECT COUNT(*) FROM scrape_runs").fetchone()[0] == 2


def test_the_snapshot_carries_the_run_a_listing_was_first_seen_in(collected, tmp_path):
    """Even when that run has another purpose: provenance travels with the data."""
    conn, _ = collected
    out = write_snapshot(conn, tmp_path / "snap", purpose="test")
    purposes = set()
    import csv
    with (out.directory / "scrape_runs.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            purposes.add(row["purpose"])
    assert purposes == {"dev", "test"}, "the first-seen development run must be exported too"


def test_the_snapshot_carries_the_rules_that_produced_its_categories(collected, tmp_path):
    conn, rules = collected
    out = write_snapshot(conn, tmp_path / "snap", purpose="test")
    for table in ("analysis_categories", "category_rule_sets", "listing_categories",
                  "listing_features"):
        assert table in out.rows, f"{table} must be in the snapshot or the categories cannot load"
    text = (out.directory / "category_rule_sets.csv").read_text(encoding="utf-8")
    assert rules.version in text and rules.sha256 in text


def test_the_analysis_can_be_rebuilt_from_the_replayed_database(collected, tmp_path):
    """The point of all of it: the figures can be recomputed without the original database."""
    conn, rules = collected
    out = write_snapshot(conn, tmp_path / "snap", purpose="test")
    replay_path = tmp_path / "replay.db"
    subprocess.run([sys.executable, str(REPO / "tools" / "load_snapshot.py"), str(out.directory),
                    "--db", str(replay_path)], check=True, capture_output=True, cwd=REPO)

    replay = connect(replay_path)
    migrate(replay, config.MARKET_MIGRATIONS)
    run_id, counts = build_dataset(replay, purpose="test", rules_version=rules.version, **WINDOW)
    assert counts.products_included == 1
    row = replay.execute("SELECT regular_price_uzs, n_observations FROM analysis_products"
                         " WHERE pipeline_run_id = ?", (run_id,)).fetchone()
    # Only the observation inside the window counts; the development one is provenance, not data.
    assert (row["regular_price_uzs"], row["n_observations"]) == (320_000, 1)
