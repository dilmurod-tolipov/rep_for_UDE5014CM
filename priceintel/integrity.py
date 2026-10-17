"""Cross-database integrity checks. SQLite cannot enforce foreign keys between two database files,
so the links between market_intel and secret_shop are checked here (pipeline + tests)."""
import sqlite3


def cross_db_orphans(market: sqlite3.Connection, secret: sqlite3.Connection) -> list[str]:
    """Problems found; an empty list means both databases agree."""
    problems = []
    posts = {r[0] for r in secret.execute("SELECT post_url FROM products")}
    own = market.execute(
        "SELECT l.listing_id, l.url FROM listings l JOIN shops s ON s.shop_id = l.shop_id"
        " WHERE s.is_own_shop = 1").fetchall()
    for listing_id, url in own:
        if url not in posts:
            problems.append(f"market_intel own listing {listing_id} ({url}) has no secret_shop product")
    return problems
