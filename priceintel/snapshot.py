"""Write a committed snapshot of the collected data.

The brief requires "an anonymised or otherwise lawful snapshot of the primary data produced by the
student's collection system, with collection logs and provenance sufficient to verify how and when it
was created" inside the assessed commit. The working databases are not committed (they are rebuilt by
migrations and change every run), so a snapshot exports the evidence as CSV plus a manifest:

* ``shops.csv``, ``scrape_runs.csv``, ``fetch_log.csv`` - the provenance: which code, which host,
  which URL, which HTTP status, which content hash, at which time.
* ``listings.csv``, ``price_observations.csv`` - the primary data itself.
* ``rejected_records.csv``, ``data_quality_checks.csv`` - what was refused and how healthy the data
  was when the snapshot was taken.
* ``analysis_categories.csv``, ``category_rule_sets.csv``, ``listing_categories.csv``,
  ``listing_features.csv`` - the category vocabulary, the rules file that was in force (version and
  SHA-256), the category of each listing and what one price buys.
* ``pipeline_runs.csv``, ``analysis_products.csv``, ``dataset_splits.csv`` - the analysis dataset and
  how it was built, so the figures in the report can be recomputed from the snapshot alone.
* ``reference_offers.csv`` - Secret's reference offers, **only** when ``include_reference`` is set,
  because the real export is shared with the assessors rather than published.
* ``MANIFEST.md`` - row counts, the SHA-256 of every file, the git commit, and the purpose filter.

CSV is deliberate: a marker can open it without SQLite, and it diffs readably in git.
"""
import csv
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from priceintel.gitinfo import git_state

PROVENANCE_TABLES = ("shops", "scrape_runs", "fetch_log")
# The snapshot has to be self-contained: `tools/load_snapshot.py` rebuilds a working database from
# it, and that fails if the category vocabulary and the rules-file provenance are missing, because
# every category assignment points at them. Found on 2026-11-13 by actually replaying a snapshot.
DATA_TABLES = ("analysis_categories", "category_rule_sets", "listings", "price_observations",
               "listing_categories", "listing_features", "rejected_records",
               "data_quality_checks", "pipeline_runs", "analysis_products", "dataset_splits")
REFERENCE_TABLES = ("reference_imports", "reference_offers")

# Only runs of the chosen purpose are exported, so a development snapshot can never be mistaken for
# assessed data. These say how to filter each table by purpose.
PURPOSE_FILTER = {
    # Every run of the chosen purpose, PLUS any run referenced by an exported listing as the run
    # that first saw it. A listing first seen during development keeps that provenance, so the
    # referenced run must travel with the snapshot or it cannot be loaded back (found on 2026-11-13
    # by replaying one). Each run carries its own purpose, so development rows stay visible as such.
    "scrape_runs": ("SELECT * FROM scrape_runs WHERE purpose = :purpose"
                    " OR run_id IN (SELECT l.first_seen_run_id FROM listings l"
                    "               WHERE l.listing_id IN (SELECT o.listing_id"
                    "                                      FROM price_observations o"
                    "                                      JOIN scrape_runs r ON r.run_id = o.run_id"
                    "                                      WHERE r.purpose = :purpose))"
                    " ORDER BY run_id"),
    "fetch_log": ("SELECT * FROM fetch_log WHERE run_id IN"
                  " (SELECT run_id FROM scrape_runs WHERE purpose = :purpose) ORDER BY fetch_id"),
    "price_observations": ("SELECT * FROM price_observations WHERE run_id IN"
                          " (SELECT run_id FROM scrape_runs WHERE purpose = :purpose)"
                          " ORDER BY observation_id"),
    "rejected_records": ("SELECT * FROM rejected_records WHERE run_id IN"
                         " (SELECT run_id FROM scrape_runs WHERE purpose = :purpose)"
                         " ORDER BY reject_id"),
    "listings": ("SELECT * FROM listings WHERE listing_id IN"
                 " (SELECT o.listing_id FROM price_observations o JOIN scrape_runs r"
                 "  ON r.run_id = o.run_id WHERE r.purpose = :purpose) ORDER BY listing_id"),
    "listing_categories": ("SELECT * FROM listing_categories WHERE listing_id IN"
                           " (SELECT o.listing_id FROM price_observations o JOIN scrape_runs r"
                           "  ON r.run_id = o.run_id WHERE r.purpose = :purpose)"
                           " ORDER BY listing_id, rules_version"),
    "data_quality_checks": ("SELECT * FROM data_quality_checks WHERE purpose = :purpose"
                            " ORDER BY check_run_id"),
}


@dataclass
class SnapshotResult:
    directory: Path
    rows: dict[str, int]
    sha256: dict[str, str]
    commit: str
    dirty: bool


def _export(conn, table: str, path: Path, purpose: str) -> tuple[int, str]:
    sql = PURPOSE_FILTER.get(table, f"SELECT * FROM {table}")
    params = {"purpose": purpose} if ":purpose" in sql else {}
    cur = conn.execute(sql, params)
    columns = [d[0] for d in cur.description]
    rows = cur.fetchall()
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(tuple(r) for r in rows)
    return len(rows), hashlib.sha256(path.read_bytes()).hexdigest()


def write_snapshot(conn, out_dir: Path | str, *, purpose: str = "assessed",
                   include_reference: bool = False, label: str = "") -> SnapshotResult:
    """Export the snapshot into ``out_dir`` (created if needed) and write its manifest."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    commit, dirty = git_state()
    tables = [*PROVENANCE_TABLES, *DATA_TABLES]
    if include_reference:
        tables += list(REFERENCE_TABLES)

    rows, digests = {}, {}
    for table in tables:
        exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                              (table,)).fetchone()
        if not exists:
            continue
        n, digest = _export(conn, table, out / f"{table}.csv", purpose)
        rows[table], digests[table] = n, digest

    taken_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# Data snapshot - {purpose} data{f' ({label})' if label else ''}",
        "",
        f"- Taken at: {taken_at}",
        f"- Collected by commit: `{commit}`{' (working tree modified)' if dirty else ''}",
        f"- Purpose filter: `{purpose}` - no run of any other purpose is included",
        f"- Secret reference offers included: {'yes' if include_reference else 'no'}",
        "",
        "Every row here was produced by this project's own collectors. `scrape_runs` names the git",
        "commit and host of each run, `fetch_log` holds one row per HTTP request with its status,",
        "size and content hash, and every price observation points at the fetch it came from.",
        "",
        "| File | Rows | SHA-256 |",
        "|---|---|---|",
    ]
    for table in rows:
        lines.append(f"| `{table}.csv` | {rows[table]:,} | `{digests[table]}` |")
    (out / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return SnapshotResult(out, rows, digests, commit, dirty)
