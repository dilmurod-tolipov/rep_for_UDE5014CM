"""What one price buys, and what the database preserves about it.

Both come from the approval decision of 2026-11-03, clarification 3: currency, variant, discount
status and availability must be preserved, and the UZS comparison must follow an explicit,
reproducible price-selection rule. The per-stem case is the one that matters in practice: in the
development crawl, `roses_mono` held a single gerbera stem at 18,000 UZS and a 101-stem bundle at
2,500,000 UZS."""
import pytest

from priceintel import config
from priceintel.analysis.categories import load_rules
from priceintel.analysis.features import build_features, extract, feature_summary
from priceintel.collect.validate import RawItem, Rejection, ValidItem, validate
from tests.conftest import TS, add_fetch, add_run, shop_id


@pytest.fixture(scope="module")
def rules():
    return load_rules(config.CATEGORY_RULES_FILE)


# ---------------------------------------------------------------------------
# What one price buys
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title, composition, section, unit, stems, evidence", [
    # The shop states a quantity: the price buys that many stems.
    ("Акция! Розы Красные 101 шт.", None, "rozy", "per_bundle", 101, "stated"),
    ("Букет из 11 персиковых роз", None, None, "per_bundle", 11, "stated"),
    ("15 розовых роз в коробке", "Состав: розы — 15 шт, фисташка", "rozy", "per_bundle", 15,
     "stated"),
    # The shop says the price is per stem, whatever else the title counts.
    ("Тюльпаны микс 3 (за шт)", None, "tsvety-raznye", "per_stem", 1, "stated"),
    # A single flower in a by-the-stem section, or a bare flower name.
    ("Гербера красная", None, "tsvety-raznye", "per_stem", 1, "inferred"),
    ("Розы Голландия красные", None, "rozy", "per_stem", 1, "inferred"),
    # One arrangement sold as one thing.
    ("Букет «Лазурный берег»", None, "bukety", "per_item", None, "stated"),
    ("Цветы в коробке «Рубин»", None, "tsvety-v-korobke", "per_item", None, "stated"),
    # A potted plant is one item by its category, not by guesswork - the rule the orchid exposed.
    ("Орхидея фаленопсис", None, "rasteniya", "per_item", None, "stated"),
])
def test_price_unit_is_read_from_the_text(rules, title, composition, section, unit, stems,
                                          evidence):
    f = extract(title, composition, section, rules)
    assert (f.price_unit, f.stem_count, f.evidence) == (unit, stems, evidence), f.rule_id


def test_stem_count_is_never_invented(rules):
    """A bouquet that does not say how many stems it holds gets no stem count."""
    f = extract("Букет «Осенняя палитра»", None, "bukety", rules)
    assert f.price_unit == "per_item" and f.stem_count is None


def test_size_in_centimetres_is_kept_when_stated(rules):
    assert extract("Роза Эквадор 60 см", None, "rozy", rules).size_cm == 60
    assert extract("Роза Эквадор", None, "rozy", rules).size_cm is None


def test_features_are_stored_and_the_comparable_view_excludes_per_stem(market_db, rules):
    from priceintel.analysis.categories import classify_listings
    run_id = add_run(market_db, purpose="test")
    add_fetch(market_db, run_id)
    for title, section in (("Букет «Лазурный берег»", "bukety"),
                           ("Гербера красная", "tsvety-raznye"),
                           ("Акция! Розы Красные 101 шт.", "rozy")):
        market_db.execute(
            "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
            " last_title, site_category) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (shop_id(market_db, "loveflowers"),
             f"https://loveflowers.uz/product/{abs(hash(title)) % 10000}/", run_id, TS, TS, title,
             section))
    classify_listings(market_db, rules)
    counts = build_features(market_db, rules)
    assert counts == {"per_item": 1, "per_stem": 1, "per_bundle": 1}

    comparable = market_db.execute(
        "SELECT price_unit FROM v_comparable_listings WHERE rules_version = ?",
        (rules.version,)).fetchall()
    assert {r[0] for r in comparable} == {"per_item", "per_bundle"}, "per_stem must not be pooled"

    summary = feature_summary(market_db, rules.version)
    assert sum(r["n_listings"] for r in summary) == 3
    assert any(r["price_unit"] == "per_stem" and r["evidence"] == "inferred" for r in summary)


def test_rebuilding_features_is_idempotent(market_db, rules):
    from priceintel.analysis.categories import classify_listings
    run_id = add_run(market_db, purpose="test")
    market_db.execute(
        "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
        " last_title, site_category) VALUES (?, 'https://uzflora.com/product/x/', ?, ?, ?,"
        " 'Букет «Тест»', 'bukety')", (shop_id(market_db, "uzflora"), run_id, TS, TS))
    classify_listings(market_db, rules)
    build_features(market_db, rules)
    build_features(market_db, rules)
    assert market_db.execute("SELECT COUNT(*) FROM listing_features").fetchone()[0] == 1


# ---------------------------------------------------------------------------
# Currency, variant, discount status, availability
# ---------------------------------------------------------------------------

def item(**kw):
    base = dict(url="https://pro-buket.uz/c/all/p/roses-15/", title="15 розовых роз в коробке",
                price_text="1300578", old_price_text="1995961", currency="UZS",
                availability="in_stock", composition_text="Состав: розы — 15 шт, фисташка")
    return RawItem(**{**base, **kw})


def test_validation_preserves_what_makes_prices_comparable():
    v = validate(item(), "pro-buket.uz")
    assert isinstance(v, ValidItem)
    assert v.currency_shown == "UZS"                  # the label the shop printed
    assert v.old_price_uzs == 1995961                 # discount status
    assert v.availability == "in_stock"               # availability
    assert "15 шт" in v.composition_text              # what is in it


@pytest.mark.parametrize("currency", ["USD", "RUB", "$", "EUR"])
def test_a_price_in_another_currency_is_quarantined_never_converted(currency):
    rejection = validate(item(currency=currency), "pro-buket.uz")
    assert isinstance(rejection, Rejection) and rejection.rule == "currency_not_uzs"


def test_the_database_refuses_a_scraped_price_in_another_currency(market_db):
    """Belt and braces: even if a parser were changed, the database will not store it."""
    import sqlite3
    run_id = add_run(market_db, purpose="test")
    fetch = add_fetch(market_db, run_id)
    listing = market_db.execute(
        "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
        " last_title) VALUES (?, 'https://uzflora.com/product/usd/', ?, ?, ?, 'Test')"
        " RETURNING listing_id", (shop_id(market_db, "uzflora"), run_id, TS, TS)).fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError, match="never converts"):
        market_db.execute(
            "INSERT INTO price_observations (listing_id, run_id, fetch_id, observed_at,"
            " source_type, title, price_uzs, currency_shown)"
            " VALUES (?, ?, ?, ?, 'scrape', 'Test', 250000, 'USD')",
            (listing, run_id, fetch, TS))
