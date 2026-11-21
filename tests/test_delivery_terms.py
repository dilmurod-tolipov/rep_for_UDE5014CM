"""Dated delivery terms per shop, and the rule that a delivery fee never touches a price.

The approved analysis plan says delivery fees are "recorded per shop with a date and reported
descriptively, never added to a price". Two things therefore need testing: that a reading can be
recorded and quoted with its source and date, and that recording one changes no price anywhere.
The second is the one that matters, because adding a fee to a price would compare shops on a number
neither of them advertises.

The readings here are invented test values. Real readings are entered from each shop's own delivery
page through `python -m priceintel record-delivery-terms`, and the table ships empty."""
import sqlite3

import pytest

from priceintel import config
from priceintel.analysis.categories import classify_listings, load_rules
from priceintel.analysis.features import build_features
from priceintel.analysis.pipeline import build_dataset
from priceintel.cli import main
from tests.conftest import add_fetch, add_run, shop_id

WINDOW = {"window_start": "2026-11-09", "window_end": "2026-12-06"}
PAGE = "https://pro-buket.uz/dostavka/"


def record(conn, shop="probuket", *, on="2026-11-21", fee=30_000, free_over=None, same_day=1,
           url=PAGE, text="Доставка 30 000 сум по Ташкенту", by="student"):
    return conn.execute(
        "INSERT INTO shop_delivery_terms (shop_id, observed_on, source_url, delivery_fee_uzs,"
        " free_delivery_threshold_uzs, same_day, raw_text, recorded_by)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING term_id",
        (shop_id(conn, shop), on, url, fee, free_over, same_day, text, by)).fetchone()[0]


def test_the_table_ships_empty(market_db):
    """Delivery terms are facts about other businesses: nothing is seeded, because an invented fee
    would be fabricated evidence about a real company."""
    assert market_db.execute("SELECT COUNT(*) FROM shop_delivery_terms").fetchone()[0] == 0


def test_a_reading_is_stored_with_its_source_and_date(market_db):
    record(market_db)
    row = market_db.execute("SELECT * FROM v_shop_delivery_terms_latest").fetchone()
    assert row["code"] == "probuket" and row["observed_on"] == "2026-11-21"
    assert row["delivery_fee_uzs"] == 30_000 and row["source_url"] == PAGE


def test_the_view_shows_the_newest_reading_per_shop(market_db):
    record(market_db, on="2026-11-15", fee=25_000)
    record(market_db, on="2026-11-21", fee=30_000)
    rows = list(market_db.execute("SELECT * FROM v_shop_delivery_terms_latest"))
    assert len(rows) == 1 and rows[0]["delivery_fee_uzs"] == 30_000


def test_not_stated_is_not_zero(market_db):
    """A page that says nothing about a fee is different from a page offering free delivery."""
    record(market_db, fee=None, text="Страница не указывает стоимость доставки")
    assert market_db.execute(
        "SELECT delivery_fee_uzs FROM shop_delivery_terms").fetchone()[0] is None
    record(market_db, shop="uzflora", fee=0, text="Бесплатная доставка")
    assert market_db.execute(
        "SELECT delivery_fee_uzs FROM shop_delivery_terms WHERE shop_id = ?",
        (shop_id(market_db, "uzflora"),)).fetchone()[0] == 0


def test_a_reading_cannot_be_edited(market_db):
    record(market_db)
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        market_db.execute("UPDATE shop_delivery_terms SET delivery_fee_uzs = 1")


def test_one_reading_per_shop_per_day(market_db):
    record(market_db)
    with pytest.raises(sqlite3.IntegrityError, match="UNIQUE"):
        record(market_db)


def test_mirrors_have_no_terms_of_their_own(market_db):
    """A mirror domain republishes another operator's catalogue and is never crawled (ADR-001), so
    recording terms against it would double-count one business."""
    with pytest.raises(sqlite3.IntegrityError, match="not a mirror"):
        record(market_db, shop="uzflowers", url="https://uzflowers.uz/dostavka/")


@pytest.mark.parametrize("kwargs, message", [
    ({"on": "21-11-2026"}, "CHECK"),                       # date must be ISO
    ({"url": "http://pro-buket.uz/x"}, "CHECK"),           # source must be https
    ({"fee": -1}, "CHECK"),                                # a negative fee is not a fee
    ({"fee": 5_000_000}, "CHECK"),                         # nor is five million a delivery charge
    ({"text": "   "}, "CHECK"),                            # the page's own words are required
])
def test_bad_readings_are_refused(market_db, kwargs, message):
    with pytest.raises(sqlite3.IntegrityError, match=message):
        record(market_db, **kwargs)


def test_recording_delivery_terms_changes_no_price(market_db):
    """The decisive test: the analysis dataset is identical before and after a fee is recorded."""
    rules = load_rules(config.CATEGORY_RULES_FILE)
    run = add_run(market_db, purpose="test")
    fetch = add_fetch(market_db, run, shop="probuket", url="https://pro-buket.uz/catalog/")
    for i, price in enumerate((400_000, 500_000, 600_000), start=1):
        listing = market_db.execute(
            "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
            " last_title, site_category) VALUES (?, ?, ?, '2026-11-09T06:00:00Z',"
            " '2026-11-09T06:00:00Z', ?, 'bukety') RETURNING listing_id",
            (shop_id(market_db, "probuket"), f"https://pro-buket.uz/c/all/p/{i}/", run,
             f"Букет {i}")).fetchone()[0]
        market_db.execute(
            "INSERT INTO price_observations (listing_id, run_id, fetch_id, observed_at,"
            " source_type, title, price_uzs, currency_shown) VALUES (?, ?, ?,"
            " '2026-11-09T06:00:00Z', 'scrape', 'x', ?, 'UZS')", (listing, run, fetch, price))
    classify_listings(market_db, rules)
    build_features(market_db, rules)

    def prices():
        run_id, _ = build_dataset(market_db, purpose="test", rules_version=rules.version, **WINDOW)
        return sorted(r[0] for r in market_db.execute(
            "SELECT regular_price_uzs FROM analysis_products WHERE pipeline_run_id = ?"
            " AND included = 1", (run_id,)))

    before = prices()
    record(market_db, fee=50_000, free_over=1_000_000)
    assert prices() == before == [400_000, 500_000, 600_000], (
        "a delivery fee must never reach a product price")


def test_the_cli_records_a_reading_and_refuses_an_unknown_shop(tmp_path, capsys):
    from priceintel.db import init_market_db
    db = tmp_path / "market.db"
    init_market_db(db, config.MARKET_MIGRATIONS, config.SHOPS_FILE)
    code = main(["record-delivery-terms", "probuket", "--db", str(db),
                 "--observed-on", "2026-11-21", "--source-url", PAGE,
                 "--raw-text", "Доставка 30 000 сум", "--recorded-by", "student",
                 "--fee", "30000", "--same-day", "1"])
    out = capsys.readouterr().out
    assert code == 0 and "probuket" in out and "30,000 UZS" in out

    assert main(["record-delivery-terms", "nosuchshop", "--db", str(db),
                 "--observed-on", "2026-11-21", "--source-url", PAGE,
                 "--raw-text", "x", "--recorded-by", "student"]) == 1
    assert "unknown shop" in capsys.readouterr().out
