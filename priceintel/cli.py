"""Command line: ``python -m priceintel <command>``."""
import argparse
from pathlib import Path

from priceintel import config
from priceintel.db import MigrationError, connect, init_market_db, init_secret_db


def cmd_init_db(args) -> int:
    try:
        m_applied, n_shops = init_market_db(args.db, config.MARKET_MIGRATIONS, config.SHOPS_FILE)
        s_applied, n_channels = init_secret_db(args.secret_db, config.SECRET_MIGRATIONS,
                                               config.SECRET_SOURCES_FILE)
    except MigrationError as e:
        print(f"error: {e}")
        return 1
    for name, path, applied, extra in (
            ("market_intel", args.db, m_applied, f"shops loaded: {n_shops}"),
            ("secret_shop", args.secret_db, s_applied, f"Secret channels loaded: {n_channels}")):
        print(f"{name}: {path}")
        print(f"  migrations applied now: {', '.join(applied) if applied else 'none (already up to date)'}")
        print(f"  {extra}")
    return 0


def cmd_collect_secret(args) -> int:
    from priceintel.collect.runner import CollectError
    from priceintel.secret.collector import collect_secret
    conn = _open_existing(args.secret_db)
    if conn is None:
        return 1
    try:
        s = collect_secret(conn, args.channel, since_days=args.days, purpose=args.purpose,
                           triggered_by=args.trigger)
    except CollectError as e:
        print(f"error: {e}")
        return 1
    print(f"secret_shop run {s.run_id} [{args.purpose}] status={s.status}")
    print(f"  pages ok/requested: {s.pages_ok}/{s.pages_requested}  prices saved: {s.prices_saved}"
          f"  posts rejected: {s.posts_rejected}  older than {args.days} days: {s.posts_too_old}")
    for e in s.errors[:10]:
        print(f"  ! {e}")
    return 0 if s.status in ("success", "partial") else 2


def cmd_snapshot_secret(args) -> int:
    from priceintel.integrity import cross_db_orphans
    from priceintel.secret.snapshot import snapshot_secret
    market, secret = _open_existing(args.db), _open_existing(args.secret_db)
    if market is None or secret is None:
        return 1
    run_id, n = snapshot_secret(market, secret, purpose=args.purpose, max_age_days=args.max_age_days)
    problems = cross_db_orphans(market, secret)
    print(f"market_intel run {run_id} [own_snapshot, {args.purpose}]: {n} Secret prices written")
    print(f"cross-database check: {'OK' if not problems else f'{len(problems)} problem(s)'}")
    for p in problems[:10]:
        print(f"  ! {p}")
    return 0 if not problems else 3


def cmd_secret_prices(args) -> int:
    conn = _open_existing(args.secret_db)
    if conn is None:
        return 1
    rows = conn.execute("SELECT * FROM v_current_prices ORDER BY published_at DESC LIMIT ?",
                        (args.limit,)).fetchall()
    if not rows:
        print("no Secret prices yet")
        return 0
    print(f"{'price UZS':>11} {'published (UTC)':20} {'observed (UTC)':20} {'run':>4} {'purpose':8} title / post")
    for r in rows:
        print(f"{r['price_uzs']:>11,} {r['published_at']:20} {r['observed_at']:20} {r['run_id']:>4} "
              f"{r['purpose']:8} {r['title'][:45]}\n{'':67}{r['post_url']}")
    return 0


def cmd_check_integrity(args) -> int:
    from priceintel.integrity import cross_db_orphans
    market, secret = _open_existing(args.db), _open_existing(args.secret_db)
    if market is None or secret is None:
        return 1
    problems = cross_db_orphans(market, secret)
    print("cross-database check: OK" if not problems else f"{len(problems)} problem(s):")
    for p in problems:
        print(f"  ! {p}")
    return 0 if not problems else 3


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


def cmd_classify(args) -> int:
    """Assign categories to stored listings from the versioned rules file."""
    from priceintel.analysis.categories import RulesError, classify_listings, load_rules
    conn = _open_existing(args.db)
    if conn is None:
        return 1
    try:
        rules = load_rules(args.rules)
        counts = classify_listings(conn, rules, shop_codes=args.shop or None)
    except RulesError as e:
        print(f"error: {e}")
        return 1
    print(f"rules {rules.version} ({rules.source_file}, sha256 {rules.sha256[:12]}...)")
    print(f"listings classified: {sum(counts.values())}")
    for code in rules.categories:
        if counts.get(code):
            print(f"  {code:22} {counts[code]:>5}")
    excluded = counts.get("out_of_scope", 0) + counts.get("unclassified", 0)
    print(f"  (excluded from analysis: {excluded} = out_of_scope + unclassified)")
    return 0


def cmd_category_report(args) -> int:
    """Table 1: distinct listings per category and operator group, for one rules version."""
    from priceintel.analysis.categories import coverage_rows, load_rules
    conn = _open_existing(args.db)
    if conn is None:
        return 1
    version = args.rules_version or load_rules(args.rules).version
    rows = coverage_rows(conn, version, purpose=args.purpose)
    if not rows:
        print(f"no classifications for rules version {version}; run `classify` first")
        return 0
    operators = sorted({r["operator"] for r in rows})
    categories = sorted({r["category"] for r in rows})
    n = {(r["operator"], r["category"]): r["n_listings"] for r in rows}
    own = {r["operator"] for r in rows if r["is_own_shop"]}
    scope = f", purpose={args.purpose}" if args.purpose else ""
    print(f"distinct listings per category and operator group (rules {version}{scope})")
    print(f"{'category':22}" + "".join(f"{o[:13]:>15}" for o in operators) + f"{'total':>8}")
    for cat in categories:
        cells = "".join(f"{n.get((o, cat), 0):>15,}" for o in operators)
        print(f"{cat:22}{cells}{sum(n.get((o, cat), 0) for o in operators):>8,}")
    print(f"{'total':22}" + "".join(
        f"{sum(n.get((o, c), 0) for c in categories):>15,}" for o in operators))
    for o in operators:
        if o in own:
            print(f"note: {o} is the own shop (reference data), not a competitor group")
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


def cmd_backup(args) -> int:
    from priceintel.backup import backup_db
    out = Path(args.out)
    for src in (args.db, args.secret_db):
        if not Path(src).exists():
            print(f"error: {src} does not exist")
            return 1
        info = backup_db(Path(src), out / Path(src).name)
        total = sum(info["rows"].values())
        print(f"{Path(src).name}: integrity={info['integrity']} rows={total} sha256={info['sha256'][:16]}... -> {info['path']}")
    return 0


def cmd_restore(args) -> int:
    from priceintel.backup import restore_db
    src = Path(args.backup_dir)
    for dest in (args.db, args.secret_db):
        backup = src / Path(dest).name
        if not backup.exists():
            print(f"error: {backup} not found")
            return 1
        info = restore_db(backup, Path(dest))
        print(f"restored {dest} from {backup}: integrity={info['integrity']} rows={sum(info['rows'].values())}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m priceintel", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init-db", help="create/upgrade both databases and load shops and Secret's channel")
    s.add_argument("--db", type=Path, default=config.MARKET_DB)
    s.add_argument("--secret-db", type=Path, default=config.SECRET_DB)
    s.set_defaults(func=cmd_init_db)

    s = sub.add_parser("collect-secret", help="read Secret's prices from its public Telegram channel")
    s.add_argument("--secret-db", type=Path, default=config.SECRET_DB)
    s.add_argument("--channel", default="secret_flowersuz")
    s.add_argument("--days", type=int, default=14, help="posts published in the last N days")
    s.add_argument("--purpose", choices=["dev", "assessed"], default="dev")
    s.add_argument("--trigger", choices=["manual", "scheduled"], default="manual")
    s.set_defaults(func=cmd_collect_secret)

    s = sub.add_parser("snapshot-secret", help="copy Secret's current prices into market_intel (own_system)")
    s.add_argument("--db", type=Path, default=config.MARKET_DB)
    s.add_argument("--secret-db", type=Path, default=config.SECRET_DB)
    s.add_argument("--purpose", choices=["dev", "assessed"], default="dev")
    s.add_argument("--max-age-days", type=int, default=2, help="only prices observed this recently")
    s.set_defaults(func=cmd_snapshot_secret)

    s = sub.add_parser("secret-prices", help="show Secret's current prices (secret_shop)")
    s.add_argument("--secret-db", type=Path, default=config.SECRET_DB)
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(func=cmd_secret_prices)

    s = sub.add_parser("check-integrity", help="cross-database orphan check")
    s.add_argument("--db", type=Path, default=config.MARKET_DB)
    s.add_argument("--secret-db", type=Path, default=config.SECRET_DB)
    s.set_defaults(func=cmd_check_integrity)

    s = sub.add_parser("backup", help="consistent, verified copies of both databases")
    s.add_argument("--out", default="data/backups/latest")
    s.add_argument("--db", type=Path, default=config.MARKET_DB)
    s.add_argument("--secret-db", type=Path, default=config.SECRET_DB)
    s.set_defaults(func=cmd_backup)

    s = sub.add_parser("restore", help="replace both databases with a verified backup")
    s.add_argument("backup_dir")
    s.add_argument("--db", type=Path, default=config.MARKET_DB)
    s.add_argument("--secret-db", type=Path, default=config.SECRET_DB)
    s.set_defaults(func=cmd_restore)

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

    s = sub.add_parser("classify", help="assign analysis categories to stored listings (text only)")
    s.add_argument("--db", type=Path, default=config.MARKET_DB)
    s.add_argument("--rules", type=Path, default=config.CATEGORY_RULES_FILE)
    s.add_argument("--shop", action="append", default=[], help="shop code (repeatable; default: all)")
    s.set_defaults(func=cmd_classify)

    s = sub.add_parser("category-report", help="Table 1: distinct listings per category and operator")
    s.add_argument("--db", type=Path, default=config.MARKET_DB)
    s.add_argument("--rules", type=Path, default=config.CATEGORY_RULES_FILE)
    s.add_argument("--rules-version", help="report an older rules version instead of the current file")
    s.add_argument("--purpose", choices=["dev", "assessed", "test"],
                   help="only listings observed in runs of this purpose")
    s.set_defaults(func=cmd_category_report)

    s = sub.add_parser("runs", help="show recent collection runs")
    s.add_argument("--db", type=Path, default=config.MARKET_DB)
    s.add_argument("--limit", type=int, default=10)
    s.set_defaults(func=cmd_runs)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
