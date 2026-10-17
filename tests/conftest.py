"""Shared test fixtures. Everything here is SYNTHETIC test data in throw-away databases;
none of it is collected data and none of it is used in the analysis."""
import pytest

from priceintel import config
from priceintel.db import connect, init_market_db

FAKE_COMMIT = "0" * 40
TS = "2026-10-20T06:00:00Z"


@pytest.fixture
def market_db(tmp_path):
    """A fresh, migrated and seeded market_intel database in a temp folder."""
    path = tmp_path / "market_intel.db"
    init_market_db(path, config.MARKET_MIGRATIONS, config.SHOPS_FILE)
    conn = connect(path)
    yield conn
    conn.close()


def shop_id(conn, code):
    return conn.execute("SELECT shop_id FROM shops WHERE code = ?", (code,)).fetchone()[0]


def add_run(conn, purpose="test", kind="competitor_scrape", commit=FAKE_COMMIT, dirty=0):
    cur = conn.execute(
        "INSERT INTO scrape_runs (kind, purpose, triggered_by, started_at, git_commit, git_dirty,"
        " scraper_version, runner_host) VALUES (?, ?, 'manual', ?, ?, ?, 'test', 'pytest')",
        (kind, purpose, TS, commit, dirty),
    )
    return cur.lastrowid


def add_fetch(conn, run_id, shop="uzflora", url="https://uzflora.com/shop/"):
    cur = conn.execute(
        "INSERT INTO fetch_log (run_id, shop_id, url, requested_at, robots_allowed, http_status,"
        " bytes, content_sha256, parse_ok) VALUES (?, ?, ?, ?, 1, 200, 100, ?, 1)",
        (run_id, shop_id(conn, shop), url, TS, "a" * 64),
    )
    return cur.lastrowid


def add_listing(conn, run_id, shop="uzflora", url="https://uzflora.com/product/test-bouquet/"):
    cur = conn.execute(
        "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at, last_title)"
        " VALUES (?, ?, ?, ?, ?, 'Test bouquet')",
        (shop_id(conn, shop), url, run_id, TS, TS),
    )
    return cur.lastrowid


def add_observation(conn, listing_id, run_id, fetch_id, price=250000, source="scrape", old=None):
    cur = conn.execute(
        "INSERT INTO price_observations (listing_id, run_id, fetch_id, observed_at, source_type,"
        " title, price_uzs, old_price_uzs) VALUES (?, ?, ?, ?, ?, 'Test bouquet', ?, ?)",
        (listing_id, run_id, fetch_id, TS, source, price, old),
    )
    return cur.lastrowid
