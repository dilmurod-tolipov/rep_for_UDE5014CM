"""Rebuild a database from a committed CSV snapshot.

The brief requires that "the final assessed system must reproduce the analysis from its saved data",
and the Module Leader repeated it in the approval decision: without a Telegram account, without the
student's machine, without the working databases. The snapshots in ``data/snapshots/`` are that saved
data, and this script turns one back into a database that the pipeline, the queries and the dashboard
read exactly as they read the live one.

    python tools/load_snapshot.py data/snapshots/assessed-window --db data/replay.db

It applies the migrations first, then loads each CSV into its table in dependency order, with foreign
keys deferred for the load only. Row counts are compared with the snapshot's manifest, so a truncated
or edited file is reported rather than silently loaded.
"""
import argparse
import csv
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from priceintel import config                                        # noqa: E402
from priceintel.db import connect, migrate                           # noqa: E402

# Parents before children: every foreign key points at a table already loaded.
LOAD_ORDER = ("shops", "analysis_categories", "category_rule_sets", "scrape_runs", "fetch_log",
              "listings", "price_observations", "rejected_records", "listing_categories",
              "listing_features", "data_quality_checks", "pipeline_runs", "analysis_products",
              "dataset_splits", "reference_imports", "reference_offers")
MANIFEST_ROW = re.compile(r"\|\s*`(?P<file>[\w.]+)`\s*\|\s*(?P<rows>[\d,]+)\s*\|")


def manifest_counts(directory: Path) -> dict[str, int]:
    manifest = directory / "MANIFEST.md"
    if not manifest.exists():
        return {}
    return {m["file"].removesuffix(".csv"): int(m["rows"].replace(",", ""))
            for m in MANIFEST_ROW.finditer(manifest.read_text(encoding="utf-8"))}


def writable_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """Columns that can be written. The last field of `table_xinfo` is the hidden flag: 0 is an
    ordinary column, 2 and 3 are generated columns, which are exported into the CSV for the reader
    but computed on insert (`price_observations.is_on_sale`)."""
    return {row[1] for row in conn.execute(f'PRAGMA table_xinfo("{table}")') if row[-1] == 0}


def load_table(conn: sqlite3.Connection, path: Path, table: str) -> int:
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return 0
    writable = writable_columns(conn, table)
    columns = [c for c in rows[0] if c in writable]
    placeholders = ", ".join("?" * len(columns))
    quoted = ", ".join(f'"{c}"' for c in columns)
    conn.executemany(f'INSERT OR REPLACE INTO "{table}" ({quoted}) VALUES ({placeholders})',
                     [[None if r[c] == "" else r[c] for c in columns] for r in rows])
    return len(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("snapshot", type=Path, help="a directory under data/snapshots/")
    ap.add_argument("--db", type=Path, default=Path("data/replay.db"))
    args = ap.parse_args(argv)

    if args.db.exists():
        args.db.unlink()
    conn = connect(args.db)
    applied = migrate(conn, config.MARKET_MIGRATIONS)
    print(f"{args.db}: {len(applied)} migrations applied")

    expected = manifest_counts(args.snapshot)
    problems = []
    conn.execute("PRAGMA defer_foreign_keys = ON")
    with conn:
        conn.execute("BEGIN")
        for table in LOAD_ORDER:
            path = args.snapshot / f"{table}.csv"
            if not path.exists():
                continue
            if table in ("listing_categories", "listing_features") and not (
                    args.snapshot / "category_rule_sets.csv").exists():
                continue    # their parent rows are not in this snapshot; see the note below
            loaded = load_table(conn, path, table)
            note = ""
            if table in expected and expected[table] != loaded:
                note = f"  <-- manifest says {expected[table]:,}"
                problems.append(f"{table}: loaded {loaded}, manifest {expected[table]}")
            print(f"  {table:22} {loaded:>7,} rows{note}")
        conn.execute("COMMIT")

    missing = [t for t in ("analysis_categories", "category_rule_sets")
               if not (args.snapshot / f"{t}.csv").exists()]
    if missing:
        print(f"note: this snapshot predates {', '.join(missing)} being exported; the category "
              f"assignments it carries cannot be loaded. Rebuild them with:")
        print(f"      python -m priceintel classify --db {args.db}")
        print(f"      python -m priceintel pipeline --db {args.db} --purpose assessed")

    broken = conn.execute("PRAGMA foreign_key_check").fetchall()
    if broken:
        problems.append(f"{len(broken)} foreign key violations after load")
    print("integrity:", "OK" if not problems else "PROBLEMS")
    for p in problems:
        print(f"  ! {p}")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
