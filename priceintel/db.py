"""SQLite connection, migrations and seeding.

Migrations are numbered SQL files (``001_core.sql``, ``002_...``) applied in order, each in
its own transaction. ``schema_migrations`` stores the SHA-256 of every applied file, so a
migration edited after it was applied is detected instead of silently diverging.
"""
import hashlib
import json
import re
import sqlite3
from pathlib import Path

MIGRATION_NAME = re.compile(r"^(\d{3})_[a-z0-9_]+\.sql$")


class MigrationError(RuntimeError):
    pass


def connect(path: Path | str) -> sqlite3.Connection:
    """Open a database with foreign keys enforced. ``autocommit=True`` means each statement
    commits on its own unless we open a transaction explicitly (``with transaction(conn)``)."""
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, autocommit=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    if str(path) != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL")  # dashboard can read while the collector writes
    return conn


class transaction:
    """``with transaction(conn):`` runs the block atomically (BEGIN ... COMMIT / ROLLBACK)."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def __enter__(self):
        self.conn.execute("BEGIN IMMEDIATE")
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        self.conn.execute("COMMIT" if exc_type is None else "ROLLBACK")
        return False


def _migration_files(directory: Path) -> list[tuple[str, Path]]:
    files = []
    for f in sorted(directory.glob("*.sql")):
        m = MIGRATION_NAME.match(f.name)
        if not m:
            raise MigrationError(f"bad migration file name: {f.name} (expected NNN_name.sql)")
        files.append((m.group(1), f))
    return files


def migrate(conn: sqlite3.Connection, directory: Path) -> list[str]:
    """Apply pending migrations from ``directory``. Returns the file names applied now."""
    conn.execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
               version    TEXT PRIMARY KEY,
               filename   TEXT NOT NULL,
               sha256     TEXT NOT NULL,
               applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
           ) STRICT"""
    )
    applied = {r["version"]: r for r in conn.execute("SELECT * FROM schema_migrations")}
    done = []
    for version, path in _migration_files(directory):
        sql = path.read_text(encoding="utf-8")
        digest = hashlib.sha256(sql.encode("utf-8")).hexdigest()
        if version in applied:
            if applied[version]["sha256"] != digest:
                raise MigrationError(
                    f"{path.name} changed after it was applied; add a new migration instead"
                )
            continue
        try:
            # executescript runs the whole file; wrapping it in BEGIN/COMMIT makes it atomic.
            conn.executescript(
                f"BEGIN;\n{sql}\n"
                f"INSERT INTO schema_migrations (version, filename, sha256) "
                f"VALUES ('{version}', '{path.name}', '{digest}');\nCOMMIT;"
            )
        except sqlite3.Error as e:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise MigrationError(f"{path.name} failed: {e}") from e
        done.append(path.name)
    return done


SHOP_FIELDS = (
    "code", "name", "base_url", "operator", "operator_group", "is_mirror", "is_own_shop",
    "is_active", "robots_status", "robots_checked_at", "terms_url", "terms_checked_at",
    "crawl_delay_s", "compliance_notes",
)


def seed_shops(conn: sqlite3.Connection, shops_file: Path) -> int:
    """Insert or update the shop registry from JSON. Safe to run repeatedly."""
    shops = json.loads(shops_file.read_text(encoding="utf-8"))["shops"]
    defaults = {"is_own_shop": 0, "is_active": 1, "robots_status": "unchecked", "is_mirror": 0,
                "robots_checked_at": None, "terms_url": None, "terms_checked_at": None,
                "crawl_delay_s": 5.0, "compliance_notes": None}
    cols = ", ".join(SHOP_FIELDS)
    marks = ", ".join(f":{f}" for f in SHOP_FIELDS)
    updates = ", ".join(f"{f} = excluded.{f}" for f in SHOP_FIELDS if f != "code")
    with transaction(conn):
        for shop in shops:
            row = {**defaults, **shop}
            row["crawl_delay_s"] = float(row["crawl_delay_s"])
            row.setdefault("operator_group", row["operator"].upper().replace(" ", "_"))
            conn.execute(
                f"INSERT INTO shops ({cols}) VALUES ({marks}) "
                f"ON CONFLICT (code) DO UPDATE SET {updates}",
                {f: row[f] for f in SHOP_FIELDS},
            )
    return len(shops)


def seed_secret_sources(conn: sqlite3.Connection, sources_file: Path) -> int:
    """Insert or update categories and Secret's public channels. Safe to run repeatedly."""
    data = json.loads(sources_file.read_text(encoding="utf-8"))
    with transaction(conn):
        for c in data["categories"]:
            conn.execute("INSERT INTO categories (code, name) VALUES (:code, :name)"
                         " ON CONFLICT (code) DO UPDATE SET name = excluded.name", c)
        for ch in data["channels"]:
            row = {"crawl_delay_s": 5.0, "consent_note": None, "is_active": 0, **ch}
            row["crawl_delay_s"] = float(row["crawl_delay_s"])
            conn.execute(
                "INSERT INTO source_channels (code, kind, preview_url, robots_status, robots_checked_at,"
                " crawl_delay_s, consent_note, is_active) VALUES (:code, :kind, :preview_url, :robots_status,"
                " :robots_checked_at, :crawl_delay_s, :consent_note, :is_active)"
                " ON CONFLICT (code) DO UPDATE SET preview_url = excluded.preview_url,"
                " robots_status = excluded.robots_status, robots_checked_at = excluded.robots_checked_at,"
                " crawl_delay_s = excluded.crawl_delay_s, consent_note = excluded.consent_note", row)
    return len(data["channels"])


def init_secret_db(path: Path, migrations: Path, sources_file: Path) -> tuple[list[str], int]:
    conn = connect(path)
    try:
        applied = migrate(conn, migrations)
        n = seed_secret_sources(conn, sources_file)
    finally:
        conn.close()
    return applied, n


def init_market_db(path: Path, migrations: Path, shops_file: Path) -> tuple[list[str], int]:
    conn = connect(path)
    try:
        applied = migrate(conn, migrations)
        n = seed_shops(conn, shops_file)
    finally:
        conn.close()
    return applied, n
