"""Consistent backups and restores of the SQLite databases.

Uses SQLite's online backup API, so a backup taken while the collector is writing is still a
consistent snapshot (copying the .db file directly could miss data held in the WAL file).
Every backup is verified with PRAGMA integrity_check and summarised with row counts and SHA-256."""
import hashlib
import shutil
import sqlite3
from pathlib import Path

from priceintel.db import connect


def _summary(path: Path) -> dict:
    conn = sqlite3.connect(path)
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        rows = {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tables}
    finally:
        conn.close()
    return {"path": str(path), "integrity": integrity, "rows": rows,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def backup_db(src: Path, dest: Path) -> dict:
    """Copy ``src`` to ``dest`` (a single self-contained file, no WAL) and verify it."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    source = connect(src)
    target = sqlite3.connect(dest)
    try:
        source.backup(target)
        target.execute("PRAGMA journal_mode = DELETE")  # self-contained file
    finally:
        target.close()
        source.close()
    info = _summary(dest)
    if info["integrity"] != "ok":
        raise RuntimeError(f"backup of {src} failed integrity check: {info['integrity']}")
    return info


def restore_db(backup: Path, dest: Path) -> dict:
    """Replace ``dest`` with a verified backup. The current file is kept as ``<name>.before-restore``."""
    info = _summary(backup)
    if info["integrity"] != "ok":
        raise RuntimeError(f"refusing to restore {backup}: integrity check says {info['integrity']}")
    for suffix in ("-wal", "-shm"):
        Path(str(dest) + suffix).unlink(missing_ok=True)
    if dest.exists():
        shutil.copy2(dest, dest.with_name(dest.name + ".before-restore"))
    shutil.copy2(backup, dest)
    return _summary(dest)
