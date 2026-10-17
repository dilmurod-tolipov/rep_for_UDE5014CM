"""Copy Secret's current prices from secret_shop into market_intel (source_type 'own_system').

Only prices collected with the same purpose are copied, so dev observations of Secret can never
enter an assessed snapshot. Own-shop listings use the post URL as the shared natural key."""
import platform
import sqlite3
from datetime import datetime, timedelta, timezone

from priceintel import __version__
from priceintel.collect.http import utc_now
from priceintel.db import transaction
from priceintel.gitinfo import git_state


def snapshot_secret(market: sqlite3.Connection, secret: sqlite3.Connection, purpose: str = "dev",
                    max_age_days: int = 2, git: tuple[str, bool] | None = None,
                    now: datetime | None = None) -> tuple[int, int]:
    """Returns (market run_id, observations written)."""
    commit, dirty = git or git_state()
    since = ((now or datetime.now(timezone.utc)) - timedelta(days=max_age_days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = secret.execute(
        "SELECT product_id, post_url, post_id, title, price_uzs, observed_at FROM v_current_prices"
        " WHERE purpose = ? AND observed_at >= ? ORDER BY product_id", (purpose, since)).fetchall()
    own_shop = market.execute("SELECT shop_id FROM shops WHERE is_own_shop = 1").fetchone()
    if own_shop is None:
        raise RuntimeError("market_intel has no own shop; run init-db")
    started, written = utc_now(), 0
    with transaction(market):
        run_id = market.execute(
            "INSERT INTO scrape_runs (kind, purpose, triggered_by, started_at, git_commit, git_dirty,"
            " scraper_version, runner_host) VALUES ('own_snapshot', ?, 'manual', ?, ?, ?, ?, ?)",
            (purpose, started, commit, int(dirty), __version__, platform.node() or "unknown")).lastrowid
        for r in rows:
            listing_id = market.execute(
                "INSERT INTO listings (shop_id, url, external_id, first_seen_run_id, first_seen_at,"
                " last_seen_at, last_title) VALUES (?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT (shop_id, url) DO UPDATE SET last_seen_at = excluded.last_seen_at,"
                " last_title = excluded.last_title RETURNING listing_id",
                (own_shop[0], r["post_url"], str(r["post_id"]), run_id, r["observed_at"],
                 r["observed_at"], r["title"])).fetchone()[0]
            # Idempotent: the same secret_shop observation is copied at most once.
            written += market.execute(
                "INSERT INTO price_observations (listing_id, run_id, observed_at, source_type, title,"
                " price_uzs, raw_price_text) SELECT ?, ?, ?, 'own_system', ?, ?, ?"
                " WHERE NOT EXISTS (SELECT 1 FROM price_observations"
                "                   WHERE listing_id = ? AND observed_at = ? AND source_type = 'own_system')",
                (listing_id, run_id, r["observed_at"], r["title"], r["price_uzs"],
                 f"secret_shop product {r['product_id']}", listing_id, r["observed_at"])).rowcount
        market.execute(
            "UPDATE scrape_runs SET finished_at = ?, status = ?, observations_saved = ? WHERE run_id = ?",
            (max(utc_now(), started), "success" if rows else "failed", written, run_id))
    return run_id, written
