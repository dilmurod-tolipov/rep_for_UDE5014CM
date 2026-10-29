"""Cross-database integrity checks.

SQLite cannot enforce a foreign key between two database files, so the links between `market_intel`
and `secret_shop` are checked in code - by the pipeline, by the dashboard on every page load, by the
`check-integrity` command and by the tests. This is the price of the two-database design, and the
brief asks for it to be demonstrated rather than asserted.

What is checked, and why each one matters:

1. **One category vocabulary.** Both databases label products with the same category codes, which come
   from the versioned rules file. If `secret_shop.categories` drifts from
   `market_intel.analysis_categories`, the shop side and the market side stop being comparable - the
   failure would show up as an empty comparison rather than as an error, which is worse.
2. **No own-shop listings in market_intel.** Secret's prices used to be copied into
   `price_observations` as `own_system` rows. That path was withdrawn (ADR-007) and the rows deleted,
   so finding one again means the withdrawn code has come back.
3. **No reference row inside the primary data.** `price_observations.source_type` must be `scrape`
   only; Secret's offers belong in `reference_offers`.
4. **Reference offers carry a known category and rules version**, so a figure on a page can always be
   traced to the rules that produced it.

Checks for `analysis.product_matches` are added here when that table arrives; the function signature
is the place the pipeline already calls.
"""
import sqlite3


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                        (name,)).fetchone() is not None


def cross_db_orphans(market: sqlite3.Connection, secret: sqlite3.Connection) -> list[str]:
    """Problems found; an empty list means both databases agree."""
    problems: list[str] = []

    # 1. The two databases must use one category vocabulary.
    if _table_exists(market, "analysis_categories") and _table_exists(secret, "categories"):
        known = {r[0] for r in market.execute("SELECT code FROM analysis_categories")}
        for code, in secret.execute("SELECT code FROM categories ORDER BY code"):
            if code not in known:
                problems.append(
                    f"secret_shop category {code!r} is not a market_intel analysis category "
                    f"(known: {', '.join(sorted(known))})")

    # 2. The withdrawn own_system path must stay withdrawn.
    own = market.execute(
        "SELECT COUNT(*) FROM listings l JOIN shops s ON s.shop_id = l.shop_id"
        " WHERE s.is_own_shop = 1").fetchone()[0]
    if own:
        problems.append(f"market_intel holds {own} own-shop listing(s); Secret's offers belong in "
                        f"reference_offers, not in listings (ADR-007)")

    # 3. Primary data is scraped data only.
    for source_type, count in market.execute(
            "SELECT source_type, COUNT(*) FROM price_observations GROUP BY source_type"):
        if source_type != "scrape":
            problems.append(f"price_observations holds {count} row(s) with source_type "
                            f"{source_type!r}; only 'scrape' is primary data")

    # 4. Reference offers must name a known category and the rules version that assigned it.
    if _table_exists(market, "reference_offers"):
        unknown = market.execute(
            "SELECT COUNT(*) FROM reference_offers o"
            " LEFT JOIN analysis_categories c ON c.code = o.category"
            " WHERE o.category IS NOT NULL AND c.code IS NULL").fetchone()[0]
        if unknown:
            problems.append(f"{unknown} reference offer(s) carry a category that is not declared")
        missing_version = market.execute(
            "SELECT COUNT(*) FROM reference_offers WHERE category IS NOT NULL"
            " AND rules_version IS NULL").fetchone()[0]
        if missing_version:
            problems.append(f"{missing_version} reference offer(s) have a category but no rules "
                            f"version, so the figure could not be traced to its rules")
    return problems
