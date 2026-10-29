"""Run the stakeholder queries in ``sql/queries/`` and print the result as a table.

The queries live in .sql files rather than in Python strings for three reasons: the marker and the
viva can read them as SQL, each file carries the stakeholder question it answers in its header, and
they can be pasted straight into any SQLite client. Every query takes named parameters
(``:rules_version``, ``:purpose``, ``:min_items``, ``:limit``); only the ones a query actually uses
are bound, so one set of defaults serves all five.
"""
import re
import sqlite3
from pathlib import Path

PARAM = re.compile(r"(?<![:\w]):([a-z_]+)")


class QueryError(ValueError):
    pass


def available(directory: Path) -> dict[str, Path]:
    """{'01_price_position_by_category': path, ...} - also accepts the name without its number."""
    files = {f.stem: f for f in sorted(directory.glob("*.sql"))}
    return files | {re.sub(r"^\d+_", "", stem): path for stem, path in files.items()}


def question_of(path: Path) -> str:
    """The stakeholder question from the file's first comment line."""
    first = path.read_text(encoding="utf-8").splitlines()[0]
    return first.lstrip("- ").strip()


def run(conn: sqlite3.Connection, path: Path, params: dict) -> tuple[list[str], list[tuple]]:
    sql = path.read_text(encoding="utf-8")
    needed = set(PARAM.findall(sql))
    missing = needed - set(params)
    if missing:
        raise QueryError(f"{path.name} needs parameter(s) {sorted(missing)}")
    cur = conn.execute(sql, {k: v for k, v in params.items() if k in needed})
    rows = cur.fetchall()
    return [d[0] for d in cur.description], [tuple(r) for r in rows]


def format_table(columns: list[str], rows: list[tuple], max_width: int = 42) -> str:
    """Plain fixed-width table: readable in a terminal and copy-pasteable into the report."""
    def cell(v):
        text = "" if v is None else (f"{v:,}" if isinstance(v, int) else str(v))
        return text if len(text) <= max_width else text[: max_width - 1] + "…"

    body = [[cell(v) for v in row] for row in rows]
    widths = [max(len(c), *(len(r[i]) for r in body)) if body else len(c)
              for i, c in enumerate(columns)]
    line = "  ".join(c.ljust(w) for c, w in zip(columns, widths))
    rule = "  ".join("-" * w for w in widths)
    out = [line, rule] + ["  ".join(c.ljust(w) for c, w in zip(r, widths)) for r in body]
    if not body:
        out.append("(no rows)")
    return "\n".join(out)
