"""Category rules: the right category for each kind of listing, exclusions first, nothing dropped
silently, no price anywhere in the decision, and idempotent storage.

The titles below are synthetic but written in the same style as the real catalogues seen in the
development crawl (poetic bouquet names, Russian flower names, WooCommerce section slugs)."""
import json

import pytest

from priceintel import config
from priceintel.analysis.categories import (
    MATCHERS,
    RulesError,
    classify,
    classify_listings,
    coverage_rows,
    flower_types_in,
    load_rules,
    register_rules,
)
from tests.conftest import TS, add_fetch, add_observation, add_run, shop_id


@pytest.fixture(scope="module")
def rules():
    return load_rules(config.CATEGORY_RULES_FILE)


def add_listing(conn, run_id, title, *, shop="uzflora", url=None, site_category=None, slug="x"):
    """A listing with a given title and the shop's own section slugs."""
    url = url or f"https://uzflora.com/product/{slug}/"
    cur = conn.execute(
        "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
        " last_title, site_category) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (shop_id(conn, shop), url, run_id, TS, TS, title, site_category))
    return cur.lastrowid


# ---------------------------------------------------------------------------
# Rule file integrity
# ---------------------------------------------------------------------------

def test_rules_file_loads_and_declares_only_text_fields(rules):
    assert rules.version == "1.1.0"
    assert len(rules.sha256) == 64
    declared = json.loads(config.CATEGORY_RULES_FILE.read_text(encoding="utf-8"))["fields_used"]
    assert declared == ["title", "url_path", "site_category"]


def test_rules_cannot_match_on_price(tmp_path, rules):
    """A rule that tried to look at a price (or any unknown field) must not load at all: this is
    what keeps the categories price-independent as the Module Leader required."""
    data = json.loads(config.CATEGORY_RULES_FILE.read_text(encoding="utf-8"))
    data["sections"].insert(0, {"id": "BAD", "category": "roses_mono", "price_above": 500000})
    bad = tmp_path / "bad_rules.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(RulesError, match="price_above"):
        load_rules(bad)
    assert "price" not in " ".join(MATCHERS)


@pytest.mark.parametrize("break_it, message", [
    (lambda d: d["sections"].insert(0, {"id": "S01", "category": "roses_mono",
                                        "title_any": ["x"]}), "duplicate rule id"),
    (lambda d: d["sections"].insert(0, {"id": "NEW", "category": "ghost_category",
                                        "title_any": ["x"]}), "unknown category"),
    (lambda d: d["sections"].insert(0, {"id": "NEW", "category": "roses_mono"}), "matches nothing"),
    (lambda d: d.pop("flower_lexicon"), "missing 'flower_lexicon'"),
])
def test_malformed_rules_are_refused(tmp_path, break_it, message):
    data = json.loads(config.CATEGORY_RULES_FILE.read_text(encoding="utf-8"))
    break_it(data)
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(RulesError, match=message):
        load_rules(path)


# ---------------------------------------------------------------------------
# Flower types in a title (also the basis of the mono/mixed split)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title, expected", [
    ("Белые розы", ("rose",)),
    ("25 красных роз", ("rose",)),
    ("Розовое сердце", ()),                       # "розовое" = pink, not a rose
    ("Розы и лилии", ("lily", "rose")),
    ("Букет из тюльпанов", ("tulip",)),
    ("Нежный флёр", ()),                          # poetic name, composition unknown
    ("Акция розы красные 101 шт", ("rose",)),
])
def test_flower_types_in_title(rules, title, expected):
    assert flower_types_in(title, rules.flower_lexicon) == expected


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("title, site_category, url, category, rule_id", [
    # Single-flower-type section or title -> roses and mono-bouquets
    ("Акция розы красные 101 шт", None, "https://loveflowers.uz/product/aktsiya-rozy-krasnye-101-sht",
     "roses_mono", "S06"),
    ("101 роза", None, "https://pro-buket.uz/c/rozy/101-roza/", "roses_mono", "S04"),
    ("Нежность", "rozy", "https://loveflowers.uz/product/nezhnost", "roses_mono", "S04"),
    ("Белые розы", "bukety", "https://uzflora.com/product/belye-rozy/", "roses_mono", "S05"),
    # Two or more named types -> mixed
    ("Розы и лилии", "bukety", "https://uzflora.com/product/rozy-i-lilii/", "mixed_bouquets", "S05"),
    # Bouquet section, nothing said about the flowers -> composition unknown, never guessed
    ("Нежный флёр", "8-marta,bukety", "https://uzflora.com/product/nezhnyj-flyor/",
     "bouquets_unspecified", "S05"),
    # A Secret channel caption: no section slug at all, the word "букеты" is the only type evidence
    ("Прекрасные букеты для любимой", None, None, "bouquets_unspecified", "S05"),
    ("Изящная композиция с тюльпанами и пионами", None, None, "mixed_bouquets", "S05"),
    ("Фата-моргана", "czvetochnye-kompoziczii", "https://uzflora.com/product/fata-morgana/",
     "bouquets_unspecified", "S05"),
    # Boxes and baskets
    ("Нежность в коробке", None, "https://loveflowers.uz/product/nezhnost-v-korobke",
     "boxes_baskets", "S01"),
    ("Корзина с розами", "bukety", "https://uzflora.com/product/korzina-s-rozami/",
     "boxes_baskets", "S01"),
    # Potted plants
    ("Орхидея фаленопсис", "rasteniya", "https://uzflora.com/product/orhideya-falenopsis/",
     "potted_plants", "S02"),
    ("Спатифиллум", None, "https://uzflora.com/product/spatifillum/", "potted_plants", "S02"),
    # Edible and berry sets
    ("Клубника в шоколаде", None, "https://kamilas.uz/product/klubnika-v-shokolade",
     "edible_sets", "S03"),
    ("Фруктовые ассорти", "podarki", "https://uzflora.com/product/fruktovye-assorti/",
     "edible_sets", "S03"),
    # Out of scope: balloons and add-ons
    ("Воздушный поцелуй", "vozdushnye-shary", "https://uzflora.com/product/vozdushnyj-poczeluj/",
     "out_of_scope", "X01"),
    ("Гелиевые шары", "bukety", "https://uzflora.com/product/gelievye-shary/", "out_of_scope", "X01"),
    ("Стеклянная ваза", "k-buketu", "https://uzflora.com/product/cteklyannaya-vaza/",
     "out_of_scope", "X02"),
    ("Торт Raffaello", "k-buketu", "https://uzflora.com/product/tort-raffaello/",
     "out_of_scope", "X02"),
    # Nothing to go on -> unclassified (counted, not dropped)
    ("Мужская забота", "podarki", "https://uzflora.com/product/muzhskaya-zabota/",
     "unclassified", "none"),
])
def test_classify(rules, title, site_category, url, category, rule_id):
    c = classify(title, url, site_category, rules)
    assert (c.category, c.rule_id) == (category, rule_id), c.evidence


def test_exclusions_win_over_sections(rules):
    """A balloon listed in the bouquet section is out of scope, not a bouquet."""
    c = classify("Воздушные шары", "bukety", "https://uzflora.com/product/shary/", rules)
    assert c.category == "out_of_scope" and c.rule_id == "X01"


def test_price_band_and_occasion_sections_are_not_signals(rules):
    """'nedorogie-czvety' (cheap flowers) is a price band and '8-marta' an occasion: neither may
    decide a category, so a poetic title in those sections stays unclassified."""
    c = classify("Своевременность", "nedorogie-czvety,8-marta",
                 "https://uzflora.com/product/svoevremennost/", rules)
    assert c.category == "unclassified"


def test_product_slug_is_not_a_section(rules):
    """Only the section part of a URL is evidence: the product slug just repeats the title, and
    reading it as a section labelled mixed bouquets as mono ones."""
    c = classify("Розы и лилии", "https://uzflora.com/product/rozy-i-lilii/", "bukety", rules)
    assert (c.category, c.rule_id) == ("mixed_bouquets", "S05")


def test_query_string_cannot_change_the_category(rules):
    plain = classify("Нежность", "rozy", "https://loveflowers.uz/product/nezhnost", rules)
    with_query = classify("Нежность", "rozy",
                          "https://loveflowers.uz/product/nezhnost?currency=UZS&sort=price", rules)
    assert plain == with_query


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def test_classify_listings_stores_every_listing_once_and_is_idempotent(market_db, rules):
    run = add_run(market_db)
    fetch = add_fetch(market_db, run)
    ids = [add_listing(market_db, run, "Белые розы", site_category="bukety", slug="a"),
           add_listing(market_db, run, "Орхидея фаленопсис", site_category="rasteniya", slug="b"),
           add_listing(market_db, run, "Мужская забота", site_category="podarki", slug="c")]
    for listing in ids:
        add_observation(market_db, listing, run, fetch)

    first = classify_listings(market_db, rules)
    assert sum(first.values()) == 3                       # nothing dropped
    assert first["roses_mono"] == first["potted_plants"] == first["unclassified"] == 1

    second = classify_listings(market_db, rules)           # re-run: same rows, no duplicates
    assert second == first
    assert market_db.execute("SELECT COUNT(*) FROM listing_categories").fetchone()[0] == 3
    assert market_db.execute("SELECT COUNT(*) FROM category_rule_sets").fetchone()[0] == 1


def test_rules_version_cannot_be_reused_for_different_rules(market_db, rules):
    register_rules(market_db, rules)
    edited = type(rules)(**{**rules.__dict__, "sha256": "f" * 64})
    with pytest.raises(RulesError, match="bump rules_version"):
        register_rules(market_db, edited)


def test_coverage_counts_distinct_listings_not_observations(market_db, rules):
    dev_run, assessed_run = add_run(market_db, purpose="test"), add_run(market_db, purpose="test")
    fetch_a, fetch_b = add_fetch(market_db, dev_run), add_fetch(market_db, assessed_run)
    listing = add_listing(market_db, dev_run, "Белые розы", site_category="bukety")
    add_observation(market_db, listing, dev_run, fetch_a, price=300000)
    add_observation(market_db, listing, assessed_run, fetch_b, price=320000)  # same product, 2 runs

    classify_listings(market_db, rules)
    rows = coverage_rows(market_db, rules.version)
    assert rows == [{"operator": "UZFLORA", "is_own_shop": 0, "category": "roses_mono",
                     "n_listings": 1}]
    assert coverage_rows(market_db, rules.version, purpose="dev") == []
