"""Secret's operational schema: the constraints, the triggers, the fixtures and the leak checks.

Every row this file creates is synthetic, in a throw-away database. That is also what it is testing:
Secret's operational tables hold invented data (the owner keeps no digital records), so the schema's
real job is to make sure invented data can never be mistaken for evidence. The tests are therefore
mostly about what the database REFUSES.
"""
import json
import sqlite3

import pytest

from priceintel import config
from priceintel.db import connect, init_secret_db
from priceintel.integrity import cross_db_orphans
from priceintel.secret.fixtures import (FixtureError, clear_fixtures, load_fixtures,
                                        synthetic_counts)

TS = "2026-11-10T09:00:00Z"


@pytest.fixture
def secret_db(tmp_path):
    path = tmp_path / "secret_shop.db"
    init_secret_db(path, config.SECRET_MIGRATIONS, config.SECRET_SOURCES_FILE)
    conn = connect(path)
    yield conn
    conn.close()


@pytest.fixture
def loaded(secret_db):
    load_fixtures(secret_db, config.SECRET_FIXTURES_FILE)
    return secret_db


@pytest.fixture
def market(market_db):
    """market_intel with the category vocabulary registered, which is what the cross-database check
    compares Secret's categories against."""
    from priceintel.analysis.categories import load_rules, register_rules
    register_rules(market_db, load_rules(config.CATEGORY_RULES_FILE))
    return market_db


def category(conn, code="roses_mono"):
    return conn.execute("SELECT category_id FROM categories WHERE code = ?", (code,)).fetchone()[0]


def add_product(conn, *, synthetic=1, title="Test bouquet", price=500_000):
    pid = conn.execute(
        "INSERT INTO products (origin, title, category_id, is_synthetic)"
        " VALUES ('manual', ?, ?, ?) RETURNING product_id",
        (title, category(conn), synthetic)).fetchone()[0]
    conn.execute("INSERT INTO product_price_history (product_id, effective_from, price_uzs)"
                 " VALUES (?, ?, ?)", (pid, TS, price))
    return pid


def add_client(conn, *, synthetic=1, consent=None, name="Test client"):
    return conn.execute(
        "INSERT INTO clients (display_name, consent_recorded_at, is_synthetic)"
        " VALUES (?, ?, ?) RETURNING client_id", (name, consent, synthetic)).fetchone()[0]


def add_user(conn, *, synthetic=1, username="tester", role="manager"):
    return conn.execute(
        "INSERT INTO admin_users (username, display_name, role, is_synthetic)"
        " VALUES (?, 'Tester', ?, ?) RETURNING admin_user_id",
        (username, role, synthetic)).fetchone()[0]


def add_order(conn, client_id, user_id, *, synthetic=1, fee=0, address_id=None, status="new",
              reason=None):
    return conn.execute(
        "INSERT INTO orders (client_id, address_id, created_by, channel, placed_at, status,"
        " delivery_fee_uzs, cancel_reason, is_synthetic)"
        " VALUES (?, ?, ?, 'phone', ?, ?, ?, ?, ?) RETURNING order_id",
        (client_id, address_id, user_id, TS, status, fee, reason, synthetic)).fetchone()[0]


# ---------------------------------------------------------------------------
# The schema accepts a correct order
# ---------------------------------------------------------------------------

def test_an_order_totals_itself_from_its_lines(secret_db):
    """items_total_uzs is maintained by a trigger and total_uzs is generated, so a total can never
    be typed in by hand and can never disagree with the lines."""
    conn = secret_db
    client, user = add_client(conn), add_user(conn)
    product = add_product(conn, price=400_000)
    order = add_order(conn, client, user)
    assert conn.execute("SELECT total_uzs FROM orders WHERE order_id = ?", (order,)).fetchone()[0] == 0

    conn.execute("INSERT INTO order_items (order_id, line_no, product_id, quantity, unit_price_uzs)"
                 " VALUES (?, 1, ?, 3, 400000)", (order, product))
    row = conn.execute("SELECT items_total_uzs, total_uzs FROM orders WHERE order_id = ?",
                       (order,)).fetchone()
    assert row["items_total_uzs"] == 1_200_000 and row["total_uzs"] == 1_200_000

    conn.execute("DELETE FROM order_items WHERE order_id = ?", (order,))
    assert conn.execute("SELECT items_total_uzs FROM orders WHERE order_id = ?",
                        (order,)).fetchone()[0] == 0


def test_the_current_price_is_the_newest_dated_row(secret_db):
    """There is no price column on products on purpose: the catalogue price is a dated history row,
    so a price change cannot leave a stale copy behind."""
    conn = secret_db
    product = add_product(conn, price=500_000)
    conn.execute("INSERT INTO product_price_history (product_id, effective_from, price_uzs, reason)"
                 " VALUES (?, '2026-11-15T09:00:00Z', 650000, 'test: seasonal increase')", (product,))
    assert conn.execute("SELECT price_uzs FROM v_current_prices WHERE product_id = ?",
                        (product,)).fetchone()[0] == 650_000


def test_price_history_is_append_only(secret_db):
    product = add_product(conn_price := secret_db, price=500_000)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        conn_price.execute("UPDATE product_price_history SET price_uzs = 1 WHERE product_id = ?",
                           (product,))


# ---------------------------------------------------------------------------
# What the schema refuses: invalid, boundary and privacy cases
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("sql, message", [
    # A real customer may not be stored without recorded consent.
    ("INSERT INTO clients (display_name, is_synthetic) VALUES ('Real person', 0)", "CHECK"),
    # Only the last four digits of a phone number may be kept, and only as four digits.
    ("INSERT INTO clients (display_name, phone_last4, is_synthetic)"
     " VALUES ('X', '+998901234567', 1)", "CHECK"),
    # Money is integer UZS in a sane range.
    ("INSERT INTO admin_users (username, display_name, role, is_synthetic)"
     " VALUES ('Bad Name', 'x', 'owner', 1)", "CHECK"),
    ("INSERT INTO admin_users (username, display_name, role, is_synthetic)"
     " VALUES ('ok.name', 'x', 'director', 1)", "CHECK"),
])
def test_invalid_rows_are_refused(secret_db, sql, message):
    with pytest.raises(sqlite3.IntegrityError, match=message):
        secret_db.execute(sql)


def test_a_consented_real_client_is_allowed(secret_db):
    """The rule is about consent, not about forbidding real data outright."""
    client = add_client(secret_db, synthetic=0, consent="2026-11-10", name="Consented client")
    assert secret_db.execute("SELECT consent_recorded_at FROM clients WHERE client_id = ?",
                             (client,)).fetchone()[0] == "2026-11-10"


def test_a_delivery_fee_needs_somewhere_to_deliver_to(secret_db):
    client, user = add_client(secret_db), add_user(secret_db)
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        add_order(secret_db, client, user, fee=30_000)          # no address


def test_a_cancelled_order_must_say_why(secret_db):
    client, user = add_client(secret_db), add_user(secret_db)
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        add_order(secret_db, client, user, status="cancelled")
    assert add_order(secret_db, client, user, status="cancelled", reason="test: client changed date")


def test_captured_payments_cannot_exceed_the_order_total(secret_db):
    conn = secret_db
    client, user = add_client(conn), add_user(conn)
    product = add_product(conn, price=400_000)
    order = add_order(conn, client, user)
    conn.execute("INSERT INTO order_items (order_id, line_no, product_id, quantity, unit_price_uzs)"
                 " VALUES (?, 1, ?, 1, 400000)", (order, product))
    conn.execute("INSERT INTO payments (order_id, paid_at, method, amount_uzs, status, is_synthetic)"
                 " VALUES (?, ?, 'cash', 300000, 'captured', 1)", (order, TS))
    with pytest.raises(sqlite3.IntegrityError, match="exceed the order total"):
        conn.execute("INSERT INTO payments (order_id, paid_at, method, amount_uzs, status,"
                     " is_synthetic) VALUES (?, ?, 'cash', 150000, 'captured', 1)", (order, TS))
    # The boundary itself is allowed: paying the remaining 100,000 exactly.
    conn.execute("INSERT INTO payments (order_id, paid_at, method, amount_uzs, status, is_synthetic)"
                 " VALUES (?, ?, 'cash', 100000, 'captured', 1)", (order, TS))
    assert conn.execute("SELECT balance_uzs FROM v_order_summary WHERE order_id = ?",
                        (order,)).fetchone()[0] == 0


def test_a_collected_product_must_prove_where_it_came_from(secret_db):
    """origin 'telegram' without provenance, and a hand-entered product pretending to have it, are
    both refused - the pair of CHECK constraints in migration 003."""
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        secret_db.execute("INSERT INTO products (origin, title, is_synthetic)"
                          " VALUES ('telegram', 'No provenance', 0)")
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        secret_db.execute("INSERT INTO products (origin, title, post_url, post_id, is_synthetic)"
                          " VALUES ('manual', 'Dressed up', 'https://t.me/x/1', 1, 1)")


def test_invented_data_cannot_claim_to_have_been_collected(secret_db):
    with pytest.raises(sqlite3.IntegrityError, match="CHECK"):
        secret_db.execute(
            "INSERT INTO products (origin, title, channel_id, post_url, post_id, published_at,"
            " first_seen_run_id, last_seen_at, is_synthetic)"
            " VALUES ('telegram', 'Fake collected', 1, 'https://t.me/x/9', 9, ?, 1, ?, 1)",
            (TS, TS))


# ---------------------------------------------------------------------------
# Synthetic and real data stay apart
# ---------------------------------------------------------------------------

def test_a_real_order_cannot_contain_a_synthetic_product(secret_db):
    """The rule that matters: fabricated products must not be able to produce real revenue."""
    conn = secret_db
    client = add_client(conn, synthetic=0, consent="2026-11-10")
    user = add_user(conn, synthetic=0, username="real.user")
    real_order = add_order(conn, client, user, synthetic=0)
    fake_product = add_product(conn, synthetic=1)
    with pytest.raises(sqlite3.IntegrityError, match="real order cannot contain a synthetic product"):
        conn.execute("INSERT INTO order_items (order_id, line_no, product_id, quantity,"
                     " unit_price_uzs) VALUES (?, 1, ?, 1, 500000)", (real_order, fake_product))


@pytest.mark.parametrize("case", ["address", "order", "payment"])
def test_a_child_row_must_share_its_parents_synthetic_flag(secret_db, case):
    conn = secret_db
    synthetic_client, synthetic_user = add_client(conn), add_user(conn)
    if case == "address":
        with pytest.raises(sqlite3.IntegrityError, match="must match its client"):
            conn.execute("INSERT INTO addresses (client_id, district, line1, is_synthetic)"
                         " VALUES (?, 'Test', 'Test 1', 0)", (synthetic_client,))
    elif case == "order":
        with pytest.raises(sqlite3.IntegrityError, match="must match its client"):
            add_order(conn, synthetic_client, synthetic_user, synthetic=0)
    else:
        order = add_order(conn, synthetic_client, synthetic_user)
        with pytest.raises(sqlite3.IntegrityError, match="must match its order"):
            conn.execute("INSERT INTO payments (order_id, paid_at, method, amount_uzs, status,"
                         " is_synthetic) VALUES (?, ?, 'cash', 1000, 'pending', 0)", (order, TS))


def test_the_integrity_check_catches_a_flag_flipped_after_insert(secret_db, market):
    """The triggers guard INSERT. An UPDATE could still flip a flag and make a fabricated order
    look real, so the cross-database check looks for the disagreement."""
    conn = secret_db
    client, user = add_client(conn), add_user(conn)
    order = add_order(conn, client, user)
    assert cross_db_orphans(market, conn) == []
    conn.execute("UPDATE orders SET is_synthetic = 0 WHERE order_id = ?", (order,))
    problems = cross_db_orphans(market, conn)
    assert any("synthetic flag differs from their client" in p for p in problems)


def test_the_integrity_check_catches_a_fixture_title_in_the_analysis_data(loaded, market):
    """If a fixture is ever imported as a Secret offer, the comparison would be computed from
    invented prices. The check finds it by title, which is what an importer copies."""
    assert cross_db_orphans(market, loaded) == []
    title = loaded.execute("SELECT title FROM products WHERE is_synthetic = 1 LIMIT 1").fetchone()[0]
    import_id = market.execute(
        "INSERT INTO reference_imports (source_kind, file_name, file_sha256, exported_at,"
        " imported_at, consent_note, purpose, rows_read, rows_stored, rows_skipped)"
        " VALUES ('csv', 'leak.csv', ?, '2026-11-20', '2026-11-20T10:00:00Z', 'test', 'test',"
        " 1, 1, 0) RETURNING import_id", ("b" * 64,)).fetchone()[0]
    market.execute(
        "INSERT INTO reference_offers (offer_id, import_id, post_id, post_url, published_at, title,"
        " price_uzs, raw_price_text, offer_group_id, category, rules_version, match_confidence)"
        " VALUES (1, ?, 1, 'https://t.me/secret_flowersuz/1', '2026-11-20T10:00:00Z', ?, 500000,"
        " '500 000', 1, 'roses_mono', '1.2.2', 'unique')", (import_id, title))
    problems = cross_db_orphans(market, loaded)
    assert any("fabricated data has reached the analysis side" in p for p in problems)


# ---------------------------------------------------------------------------
# The fixtures themselves
# ---------------------------------------------------------------------------

def test_the_fixtures_load_declare_themselves_and_balance(loaded):
    counts = synthetic_counts(loaded)
    assert counts["orders"] == 5 and counts["order_items"] == 6 and counts["products"] == 5
    assert all(counts.values()), "every operational table should be exercised"
    not_declared = loaded.execute(
        "SELECT COUNT(*) FROM orders WHERE is_synthetic <> 1").fetchone()[0]
    assert not_declared == 0, "every fixture row must declare itself synthetic"
    # The demo data must be arithmetically coherent, or it demonstrates nothing.
    for row in loaded.execute("SELECT * FROM v_order_summary"):
        assert row["total_uzs"] == row["items_total_uzs"] + row["delivery_fee_uzs"]
        assert row["captured_uzs"] <= row["total_uzs"]
        assert row["balance_uzs"] == row["total_uzs"] - row["captured_uzs"]


def test_the_fixtures_only_use_categories_both_databases_know(loaded, market):
    """A fixture may not invent a category: that would break the one vocabulary the two databases
    share, and the cross-database check would fail."""
    assert cross_db_orphans(market, loaded) == []
    data = json.loads(config.SECRET_FIXTURES_FILE.read_text(encoding="utf-8"))
    known = {r[0] for r in market.execute("SELECT code FROM analysis_categories")}
    assert {p["category"] for p in data["products"]} <= known


def test_loading_twice_is_refused_rather_than_doubling_the_demo_revenue(loaded):
    with pytest.raises(FixtureError, match="already loaded"):
        load_fixtures(loaded, config.SECRET_FIXTURES_FILE)


def test_clearing_removes_synthetic_rows_and_keeps_real_ones(loaded):
    real_client = add_client(loaded, synthetic=0, consent="2026-11-10", name="Real client")
    removed = clear_fixtures(loaded)
    assert removed["orders"] == 5
    assert all(v == 0 for v in synthetic_counts(loaded).values())
    assert loaded.execute("SELECT COUNT(*) FROM clients WHERE client_id = ?",
                          (real_client,)).fetchone()[0] == 1
    # And the database is loadable again afterwards, so the demo can be reset.
    load_fixtures(loaded, config.SECRET_FIXTURES_FILE)
    assert synthetic_counts(loaded)["orders"] == 5


def test_the_sales_view_separates_synthetic_revenue(loaded):
    rows = list(loaded.execute("SELECT * FROM v_sales_by_category"))
    assert rows and all(r["is_synthetic"] == 1 for r in rows), (
        "the view must expose the flag, so no figure drawn from it can be shown without saying "
        "that it is demonstration data")
    cancelled = loaded.execute(
        "SELECT COUNT(*) FROM v_sales_by_category s JOIN orders o"
        " ON substr(o.placed_at, 1, 10) = s.day WHERE o.status = 'cancelled'").fetchone()[0]
    assert cancelled == 0, "a cancelled order is not revenue"


def test_the_dashboard_cannot_show_fixture_rows_as_real(loaded, market, tmp_path):
    """A row count of five orders, shown without saying they are invented, would read as real
    trade. The overview page carries a synthetic column and says so in words."""
    from priceintel.queries import available
    from priceintel.web.data import Databases, secret_shop_state
    from priceintel.web.views import render
    from tests.conftest import add_fetch, add_listing, add_observation, add_run
    run = add_run(market, purpose="test")
    add_observation(market, add_listing(market, run), run, add_fetch(market, run))
    db = Databases(market, loaded, available(config.QUERIES_DIR))
    state = secret_shop_state(db)
    assert state["counts"]["orders"] == 5 and state["synthetic"]["orders"] == 5
    body = render("/", {"purpose": ["test"]}, db).body
    assert "of which synthetic" in body
    assert "every operational row here is a declared synthetic fixture" in body
