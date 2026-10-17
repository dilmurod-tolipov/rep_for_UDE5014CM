"""Command line: ``python -m priceintel <command>``."""
import argparse
from pathlib import Path

from priceintel import config
from priceintel.db import MigrationError, connect, init_market_db


def cmd_init_db(args) -> int:
    try:
        applied, n_shops = init_market_db(args.db, config.MARKET_MIGRATIONS, config.SHOPS_FILE)
    except MigrationError as e:
        print(f"error: {e}")
        return 1
    print(f"database: {args.db}")
    print(f"migrations applied now: {', '.join(applied) if applied else 'none (already up to date)'}")
    print(f"shops loaded from {config.SHOPS_FILE.name}: {n_shops}")
    return 0


def cmd_db_info(args) -> int:
    if not Path(args.db).exists():
        print(f"error: {args.db} does not exist; run `python -m priceintel init-db` first")
        return 1
    conn = connect(args.db)
    print(f"database: {args.db}")
    for r in conn.execute("SELECT version, filename, applied_at FROM schema_migrations ORDER BY version"):
        print(f"  migration {r['version']}  {r['filename']}  applied {r['applied_at']}")
    tables = [r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    print("  rows per table:")
    for t in tables:
        n = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f"    {t:22} {n}")
    print("  shops:")
    for r in conn.execute(
            "SELECT code, operator, is_active, robots_status FROM shops ORDER BY is_active DESC, code"):
        state = "active  " if r["is_active"] else "inactive"
        print(f"    {r['code']:13} {state} robots={r['robots_status']:15} operator={r['operator']}")
    conn.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m priceintel", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init-db", help="create/upgrade market_intel.db and load the shop registry")
    s.add_argument("--db", type=Path, default=config.MARKET_DB)
    s.set_defaults(func=cmd_init_db)

    s = sub.add_parser("db-info", help="show migrations, row counts and shops")
    s.add_argument("--db", type=Path, default=config.MARKET_DB)
    s.set_defaults(func=cmd_db_info)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
