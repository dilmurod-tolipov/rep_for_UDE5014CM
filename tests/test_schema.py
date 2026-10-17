"""market_intel schema: the database itself must refuse invalid or untraceable data."""
import sqlite3

import pytest

from priceintel import config
from priceintel.db import MigrationError, connect, migrate
from tests.conftest import (add_fetch, add_listing, add_observation, add_run, shop_id)


def test_init_creates_schema_and_is_idempotent(tmp_path):
    from priceintel.db import init_market_db
    path = tmp_path / "m.db"
    applied, n = init_market_db(path, config.MARKET_MIGRATIONS, config.SHOPS_FILE)
    assert applied == ["001_core.sql", "002_listing_site_category.sql"] and n == 10
    applied_again, _ = init_market_db(path, config.MARKET_MIGRATIONS, config.SHOPS_FILE)
    assert applied_again == []
    conn = connect(path)
    assert conn.execute("SELECT COUNT(*) FROM shops").fetchone()[0] == 10  # no duplicates
    active = {r[0] for r in conn.execute("SELECT operator FROM shops WHERE is_active = 1 AND is_own_shop = 0")}
    assert len(active) >= 4  # v2 proposal minimum: four independent competitor operators


def test_valid_observation_is_stored_with_full_provenance(market_db):
    run = add_run(market_db)
    fetch = add_fetch(market_db, run)
    listing = add_listing(market_db, run)
    add_observation(market_db, listing, run, fetch, price=250000, old=300000)
    row = market_db.execute(
        "SELECT o.price_uzs, o.is_on_sale, f.url AS fetched_url, f.content_sha256, r.git_commit"
        " FROM price_observations o JOIN fetch_log f USING (fetch_id) JOIN scrape_runs r ON r.run_id = o.run_id"
    ).fetchone()
    assert row["price_uzs"] == 250000 and row["is_on_sale"] == 1
    assert row["fetched_url"].startswith("https://") and len(row["content_sha256"]) == 64
    assert len(row["git_commit"]) == 40


@pytest.mark.parametrize("price, old", [(0, None), (-5000, None), (250000, 200000)])
def test_invalid_prices_are_refused(market_db, price, old):
    run = add_run(market_db)
    fetch = add_fetch(market_db, run)
    listing = add_listing(market_db, run)
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        add_observation(market_db, listing, run, fetch, price=price, old=old)


def test_same_listing_twice_in_one_run_is_refused(market_db):
    """Idempotent re-runs: UNIQUE (listing_id, run_id)."""
    run = add_run(market_db)
    fetch = add_fetch(market_db, run)
    listing = add_listing(market_db, run)
    add_observation(market_db, listing, run, fetch)
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
        add_observation(market_db, listing, run, fetch)


def test_scraped_observation_needs_fetch_from_same_run(market_db):
    run1, run2 = add_run(market_db), add_run(market_db)
    fetch_run1 = add_fetch(market_db, run1)
    listing = add_listing(market_db, run1)
    with pytest.raises(sqlite3.IntegrityError, match="provenance"):
        add_observation(market_db, listing, run2, fetch_run1)
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        add_observation(market_db, listing, run2, None)  # scrape rows must have a fetch


def test_observations_are_append_only(market_db):
    run = add_run(market_db)
    obs = add_observation(market_db, add_listing(market_db, run), run, add_fetch(market_db, run))
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        market_db.execute("UPDATE price_observations SET price_uzs = 1 WHERE observation_id = ?", (obs,))
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        market_db.execute("DELETE FROM price_observations WHERE observation_id = ?", (obs,))


def test_own_shop_prices_are_kept_separate(market_db):
    run = add_run(market_db, kind="own_snapshot")
    competitor = add_listing(market_db, run)
    with pytest.raises(sqlite3.IntegrityError, match="separation"):
        add_observation(market_db, competitor, run, None, source="own_system")
    own = add_listing(market_db, run, shop="secret", url="internal://secret_shop/products/1")
    add_observation(market_db, own, run, None, source="own_system")  # allowed


def test_assessed_run_requires_clean_committed_code(market_db):
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        add_run(market_db, purpose="assessed", dirty=1)
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        add_run(market_db, purpose="assessed", commit="unknown")
    add_run(market_db, purpose="assessed")  # clean 40-char commit is fine


def test_disallowed_shop_cannot_be_activated(market_db):
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        market_db.execute("UPDATE shops SET is_active = 1 WHERE code = 'fiori'")
    assert market_db.execute("SELECT is_active FROM shops WHERE shop_id = ?",
                             (shop_id(market_db, "fiori"),)).fetchone()[0] == 0


def test_edited_migration_is_detected(tmp_path):
    mig = tmp_path / "migrations"
    mig.mkdir()
    (mig / "001_init.sql").write_text("CREATE TABLE t (x INTEGER) STRICT;", encoding="utf-8")
    conn = connect(tmp_path / "x.db")
    assert migrate(conn, mig) == ["001_init.sql"]
    (mig / "001_init.sql").write_text("CREATE TABLE t (x TEXT) STRICT;", encoding="utf-8")
    with pytest.raises(MigrationError, match="changed after it was applied"):
        migrate(conn, mig)
