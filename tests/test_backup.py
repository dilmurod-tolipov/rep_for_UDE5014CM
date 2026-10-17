"""Backup and restore: a backup taken with uncommitted WAL data is complete, verified and restorable."""
from priceintel import config
from priceintel.backup import backup_db, restore_db
from priceintel.db import connect, init_market_db
from tests.conftest import add_fetch, add_listing, add_observation, add_run


def test_backup_is_complete_verified_and_restorable(tmp_path):
    live = tmp_path / "market_intel.db"
    init_market_db(live, config.MARKET_MIGRATIONS, config.SHOPS_FILE)
    conn = connect(live)  # WAL mode: new rows sit in the -wal file while this connection is open
    run = add_run(conn)
    add_observation(conn, add_listing(conn, run), run, add_fetch(conn, run))

    info = backup_db(live, tmp_path / "backup" / "market_intel.db")
    assert info["integrity"] == "ok" and info["rows"]["price_observations"] == 1 and len(info["sha256"]) == 64

    # Simulate losing the data, then recover it from the backup.
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("DROP TRIGGER trg_price_obs_no_delete")
    conn.execute("DELETE FROM price_observations")
    conn.close()
    restored = restore_db(tmp_path / "backup" / "market_intel.db", live)
    assert restored["rows"]["price_observations"] == 1
    assert (tmp_path / "market_intel.db.before-restore").exists()
    check = connect(live)
    assert check.execute("SELECT COUNT(*) FROM price_observations").fetchone()[0] == 1
    assert check.execute("SELECT name FROM sqlite_master WHERE name = 'trg_price_obs_no_delete'").fetchone()
