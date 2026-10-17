"""Secret's side end to end on a fake t.me: collect -> secret_shop -> snapshot -> market_intel,
plus the cross-database check. Synthetic fixtures only."""
from datetime import datetime, timezone
from pathlib import Path

import pytest

from priceintel import config
from priceintel.db import connect, init_secret_db
from priceintel.integrity import cross_db_orphans
from priceintel.secret.collector import collect_secret
from priceintel.secret.snapshot import snapshot_secret
from tests.test_collect_integration import make_fetcher

FIXTURES = Path(__file__).parent / "fixtures"
NOW = datetime(2026, 10, 18, 0, 0, tzinfo=timezone.utc)
GIT = ("2" * 40, False)


@pytest.fixture
def secret_db(tmp_path):
    path = tmp_path / "secret_shop.db"
    init_secret_db(path, config.SECRET_MIGRATIONS, config.SECRET_SOURCES_FILE)
    conn = connect(path)
    conn.execute("UPDATE source_channels SET preview_url = 'https://t.me/s/test_channel'")
    yield conn
    conn.close()


def routes():
    page = lambda n: (200, (FIXTURES / f"telegram_page{n}_synthetic.html").read_text(encoding="utf-8"))
    return {"https://t.me/robots.txt": (404, "not found"),
            "https://t.me/s/test_channel": page(1),
            "https://t.me/s/test_channel?before=101": page(2)}


def run(secret_db, purpose="dev"):
    fetcher, site = make_fetcher(routes())
    return collect_secret(secret_db, purpose=purpose, fetcher=fetcher, git=GIT, now=NOW), site


def test_collects_prices_with_provenance_and_rejects_ambiguous_posts(secret_db):
    s, site = run(secret_db)
    assert s.status == "success" and (s.pages_ok, s.pages_requested) == (2, 2)
    assert (s.prices_saved, s.posts_rejected, s.posts_too_old) == (3, 2, 1)
    assert "https://t.me/s/test_channel?before=95" not in site.requests   # stopped at the 14-day cutoff
    prices = {r["post_url"]: r["price_uzs"] for r in secret_db.execute("SELECT * FROM v_current_prices")}
    assert prices == {"https://t.me/test_channel/101": 1180000, "https://t.me/test_channel/108": 4100000,
                      "https://t.me/test_channel/99": 750000}
    row = secret_db.execute(
        "SELECT f.url, f.http_status, f.content_sha256, p.caption FROM product_price_history h"
        " JOIN source_fetches f USING (fetch_id) JOIN products p USING (product_id)"
        " WHERE p.post_id = 101").fetchone()
    assert row["url"] == "https://t.me/s/test_channel" and row["http_status"] == 200
    assert len(row["content_sha256"]) == 64 and "+998" not in row["caption"]   # contacts not stored
    assert sorted(r[0] for r in secret_db.execute("SELECT rule FROM rejected_posts")) == \
        ["multiple_prices", "no_price"]


def test_every_run_adds_a_fresh_dated_observation(secret_db):
    run(secret_db)
    run(secret_db)
    q = lambda sql: secret_db.execute(sql).fetchone()[0]
    assert q("SELECT COUNT(*) FROM products") == 3
    assert q("SELECT COUNT(*) FROM product_price_history") == 6


def test_snapshot_writes_own_system_rows_and_databases_agree(secret_db, market_db):
    run(secret_db)
    run_id, n = snapshot_secret(market_db, secret_db, purpose="dev", git=GIT, now=NOW)
    assert n == 3
    rows = market_db.execute(
        "SELECT s.is_own_shop, o.source_type, o.fetch_id, r.kind FROM price_observations o"
        " JOIN listings l USING (listing_id) JOIN shops s USING (shop_id)"
        " JOIN scrape_runs r ON r.run_id = o.run_id").fetchall()
    assert {tuple(r) for r in rows} == {(1, "own_system", None, "own_snapshot")}
    assert cross_db_orphans(market_db, secret_db) == []
    assert snapshot_secret(market_db, secret_db, purpose="dev", git=GIT, now=NOW)[1] == 0  # idempotent


def test_dev_prices_never_enter_an_assessed_snapshot(secret_db, market_db):
    run(secret_db, purpose="dev")
    assert snapshot_secret(market_db, secret_db, purpose="assessed", git=GIT, now=NOW)[1] == 0


def test_orphan_check_detects_listing_without_secret_product(secret_db, market_db):
    run(secret_db)
    snapshot_secret(market_db, secret_db, purpose="dev", git=GIT, now=NOW)
    secret_db.execute("PRAGMA foreign_keys = OFF")
    secret_db.execute("DELETE FROM product_attributes")
    secret_db.execute("UPDATE products SET post_url = 'https://t.me/test_channel/999' WHERE post_id = 101")
    problems = cross_db_orphans(market_db, secret_db)
    assert len(problems) == 1 and "test_channel/101" in problems[0]
