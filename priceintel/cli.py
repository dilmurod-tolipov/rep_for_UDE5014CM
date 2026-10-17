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


def _open_existing(path):
    if not Path(path).exists():
        print(f"error: {path} does not exist; run `python -m priceintel init-db` first")
        return None
    return connect(path)


def cmd_collect(args) -> int:
    from priceintel.collect.runner import CollectError, collect
    conn = _open_existing(args.db)
    if conn is None:
        return 1
    codes = args.shop
    if args.all:
        codes = [r["code"] for r in conn.execute(
            "SELECT code FROM shops WHERE is_active = 1 AND is_own_shop = 0 ORDER BY code")]
    if not codes:
        print("error: give --shop CODE (repeatable) or --all")
        return 1
    try:
        s = collect(conn, codes, purpose=args.purpose, triggered_by=args.trigger,
                    max_pages=args.max_pages)
    except CollectError as e:
        print(f"error: {e}")
        return 1
    print(f"run {s.run_id} [{args.purpose}] status={s.status}")
    print(f"  pages ok/requested: {s.pages_ok}/{s.pages_requested}  robots-skipped: {s.robots_skipped}")
    print(f"  observations saved: {s.observations_saved}  duplicates skipped: {s.duplicates_skipped}"
          f"  rejected (quarantined): {s.records_rejected}")
    for e in s.errors[:10]:
        print(f"  ! {e}")
    return 0 if s.status in ("success", "partial") else 2


def cmd_listings(args) -> int:
    conn = _open_existing(args.db)
    if conn is None:
        return 1
    sql = "SELECT * FROM v_latest_prices WHERE 1 = 1"
    params: list = []
    if args.shop:
        sql += " AND shop = ?"
        params.append(args.shop)
    if args.run:
        sql += " AND run_id = ?"
        params.append(args.run)
    sql += " ORDER BY observed_at DESC, listing_id DESC LIMIT ?"
    params.append(args.limit)
    rows = conn.execute(sql, params).fetchall()
    if not rows:
        print("no observations yet")
        return 0
    print(f"{'shop':10} {'price UZS':>11} {'old':>11} {'observed (UTC)':20} {'run':>4} {'purpose':8} title / url")
    for r in rows:
        old = f"{r['old_price_uzs']:,}" if r["old_price_uzs"] else ""
        price = ("от " if r["is_from_price"] else "") + f"{r['price_uzs']:,}"
        print(f"{r['shop']:10} {price:>11} {old:>11} {r['observed_at']:20} {r['run_id']:>4} "
              f"{r['purpose']:8} {r['title'][:45]}\n{'':66}{r['url']}")
    return 0


def cmd_runs(args) -> int:
    conn = _open_existing(args.db)
    if conn is None:
        return 1
    rows = conn.execute("SELECT * FROM scrape_runs ORDER BY run_id DESC LIMIT ?", (args.limit,)).fetchall()
    for r in rows:
        print(f"run {r['run_id']:>4} {r['started_at']} {r['purpose']:8} {r['triggered_by']:9} "
              f"{r['status']:8} pages {r['pages_ok']}/{r['pages_requested']} "
              f"obs {r['observations_saved']} rejected {r['records_rejected']} "
              f"commit {r['git_commit'][:10]}{' (dirty)' if r['git_dirty'] else ''}")
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

    s = sub.add_parser("collect", help="scrape competitor catalogues into market_intel")
    s.add_argument("--db", type=Path, default=config.MARKET_DB)
    s.add_argument("--shop", action="append", default=[], help="shop code, e.g. uzflora (repeatable)")
    s.add_argument("--all", action="store_true", help="all active competitor shops")
    s.add_argument("--purpose", choices=["dev", "assessed"], default="dev",
                   help="'assessed' only after approval, from committed code (default: dev)")
    s.add_argument("--trigger", choices=["manual", "scheduled"], default="manual")
    s.add_argument("--max-pages", type=int, default=60, help="safety cap per shop")
    s.set_defaults(func=cmd_collect)

    s = sub.add_parser("listings", help="show the latest price of each collected listing")
    s.add_argument("--db", type=Path, default=config.MARKET_DB)
    s.add_argument("--shop")
    s.add_argument("--run", type=int, help="only listings whose latest observation is from this run")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_listings)

    s = sub.add_parser("runs", help="show recent collection runs")
    s.add_argument("--db", type=Path, default=config.MARKET_DB)
    s.add_argument("--limit", type=int, default=10)
    s.set_defaults(func=cmd_runs)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
