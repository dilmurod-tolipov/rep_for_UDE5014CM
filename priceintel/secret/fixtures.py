"""Load and remove Secret's synthetic operational data.

The owner takes orders by phone and Telegram and keeps no digital record, so Secret's operational
tables (clients, orders, payments, staff) have no real rows and never will in this project. They
exist because the approved proposal promised them and because the schema is part of what LO2
assesses - and they are exercised with declared fixtures rather than left empty, so the constraints,
triggers and views can be demonstrated and tested.

Two rules hold everything together:

1. **Everything loaded here is `is_synthetic = 1`.** The flag is NOT NULL on every operational
   table, the database triggers refuse a row whose flag disagrees with its parent, and
   `priceintel.integrity` fails the cross-database check if a synthetic row ever becomes reachable
   from the analysis side. Fabricated data cannot quietly become evidence.
2. **This module never touches `market_intel`.** Secret's real prices reach the comparison only
   through `reference_offers`, imported from one export of its public channel (ADR-007, ADR-010).

`load_fixtures` is idempotent in the useful sense: it refuses to run twice, so a second call cannot
double the demo revenue. `clear_fixtures` removes synthetic rows only, and leaves anything real
alone, which is what makes it safe to run on a database that has both.
"""
import json
import sqlite3
from pathlib import Path

from priceintel.db import transaction


class FixtureError(RuntimeError):
    pass


def _category_ids(conn: sqlite3.Connection) -> dict[str, int]:
    return {r["code"]: r["category_id"] for r in conn.execute("SELECT code, category_id FROM categories")}


def synthetic_counts(conn: sqlite3.Connection) -> dict[str, int]:
    """How many synthetic rows each operational table holds."""
    counts = {}
    for table in ("admin_users", "clients", "addresses", "products", "orders", "payments"):
        counts[table] = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE is_synthetic = 1").fetchone()[0]
    counts["order_items"] = conn.execute(
        "SELECT COUNT(*) FROM order_items i JOIN orders o ON o.order_id = i.order_id"
        " WHERE o.is_synthetic = 1").fetchone()[0]
    counts["product_price_history"] = conn.execute(
        "SELECT COUNT(*) FROM product_price_history h JOIN products p ON p.product_id = h.product_id"
        " WHERE p.is_synthetic = 1").fetchone()[0]
    return counts


def load_fixtures(conn: sqlite3.Connection, fixtures_file: Path | str) -> dict[str, int]:
    """Insert the synthetic demonstration data. Raises if any is already present."""
    existing = synthetic_counts(conn)
    if any(existing.values()):
        raise FixtureError(
            "synthetic rows are already loaded "
            f"({', '.join(f'{k}={v}' for k, v in existing.items() if v)}); "
            "run `python -m priceintel fixtures --clear` first")

    data = json.loads(Path(fixtures_file).read_text(encoding="utf-8"))
    categories = _category_ids(conn)
    unknown = {p["category"] for p in data["products"]} - set(categories)
    if unknown:
        # The two databases must share one category vocabulary; a fixture may not invent a category.
        raise FixtureError(f"fixture categories not in secret_shop.categories: {sorted(unknown)}")

    with transaction(conn):
        users: dict[str, int] = {}
        for u in data["admin_users"]:
            users[u["username"]] = conn.execute(
                "INSERT INTO admin_users (username, display_name, role, is_synthetic)"
                " VALUES (:username, :display_name, :role, 1) RETURNING admin_user_id", u).fetchone()[0]

        clients: dict[str, int] = {}
        addresses: dict[str, int] = {}
        for c in data["clients"]:
            clients[c["ref"]] = conn.execute(
                "INSERT INTO clients (display_name, phone_last4, preferred_channel, note,"
                " is_synthetic) VALUES (?, ?, ?, ?, 1) RETURNING client_id",
                (c["display_name"], c.get("phone_last4"), c.get("preferred_channel", "phone"),
                 c.get("note"))).fetchone()[0]
            for a in c.get("addresses", []):
                addresses[a["ref"]] = conn.execute(
                    "INSERT INTO addresses (client_id, district, line1, landmark, is_default,"
                    " is_synthetic) VALUES (?, ?, ?, ?, ?, 1) RETURNING address_id",
                    (clients[c["ref"]], a["district"], a["line1"], a.get("landmark"),
                     a.get("is_default", 0))).fetchone()[0]

        products: dict[str, int] = {}
        first_price_at = min(o["placed_at"] for o in data["orders"])
        for p in data["products"]:
            products[p["ref"]] = conn.execute(
                "INSERT INTO products (origin, title, category_id, is_synthetic)"
                " VALUES ('manual', ?, ?, 1) RETURNING product_id",
                (p["title"], categories[p["category"]])).fetchone()[0]
            # The catalogue price is a dated row, not a column: see migration 003.
            conn.execute(
                "INSERT INTO product_price_history (product_id, effective_from, price_uzs,"
                " changed_by, reason) VALUES (?, ?, ?, ?, 'fixture: opening catalogue price')",
                (products[p["ref"]], first_price_at, p["price_uzs"], users.get("owner")))

        for o in data["orders"]:
            order_id = conn.execute(
                "INSERT INTO orders (client_id, address_id, created_by, channel, placed_at,"
                " fulfil_at, status, delivery_fee_uzs, cancel_reason, is_synthetic)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1) RETURNING order_id",
                (clients[o["client"]], addresses.get(o.get("address")), users[o["created_by"]],
                 o["channel"], o["placed_at"], o.get("fulfil_at"), o.get("status", "new"),
                 o.get("delivery_fee_uzs", 0), o.get("cancel_reason"))).fetchone()[0]
            for line_no, item in enumerate(o["items"], start=1):
                # items_total_uzs on the order is maintained by a trigger from these lines.
                conn.execute(
                    "INSERT INTO order_items (order_id, line_no, product_id, quantity,"
                    " unit_price_uzs) VALUES (?, ?, ?, ?, ?)",
                    (order_id, line_no, products[item["product"]], item["quantity"],
                     item["unit_price_uzs"]))
            for pay in o.get("payments", []):
                conn.execute(
                    "INSERT INTO payments (order_id, paid_at, method, amount_uzs, status,"
                    " reference, is_synthetic) VALUES (?, ?, ?, ?, ?, ?, 1)",
                    (order_id, pay["paid_at"], pay["method"], pay["amount_uzs"], pay["status"],
                     pay.get("reference")))

    return synthetic_counts(conn)


def clear_fixtures(conn: sqlite3.Connection) -> dict[str, int]:
    """Remove synthetic operational rows, and nothing else. Returns what was removed."""
    removed = synthetic_counts(conn)
    with transaction(conn):
        conn.execute("DELETE FROM payments WHERE is_synthetic = 1")
        conn.execute("DELETE FROM order_items WHERE order_id IN"
                     " (SELECT order_id FROM orders WHERE is_synthetic = 1)")
        conn.execute("DELETE FROM orders WHERE is_synthetic = 1")
        # product_price_history and product_attributes cascade with their product.
        conn.execute("DELETE FROM products WHERE is_synthetic = 1")
        conn.execute("DELETE FROM addresses WHERE is_synthetic = 1")
        conn.execute("DELETE FROM clients WHERE is_synthetic = 1")
        conn.execute("DELETE FROM admin_users WHERE is_synthetic = 1")
    return removed
