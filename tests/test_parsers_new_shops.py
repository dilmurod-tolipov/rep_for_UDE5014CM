"""Parsers for the three competitor groups added after uzflora, tested against real page fragments.

The fixtures in `tests/fixtures/*_real.html` are trimmed copies of pages actually fetched from the
shops (date and source URL in each file's first comment), with order links and phone numbers removed.
Testing against real markup is the point: the synthetic fixtures used earlier could not have caught
a currency switcher or a JavaScript-built catalogue."""
from pathlib import Path

import pytest

from priceintel.collect.parsers import get_parser, kamilas, loveflowers, probuket
from priceintel.collect.validate import ValidItem, validate

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# pro-buket.uz: price shown in three currencies, UZS must be the one collected
# ---------------------------------------------------------------------------

def test_probuket_reads_uzs_not_usd_or_rub():
    result = probuket.parse(fixture("probuket_catalog_real.html"), "https://pro-buket.uz/catalog/")
    assert len(result.items) == 3
    item = next(i for i in result.items if "роз" in (i.title or ""))
    assert item.currency == "UZS"
    checked = validate(item, "pro-buket.uz")
    assert isinstance(checked, ValidItem), checked
    # 1 300 578 сум, not $114.5 or 8 974 ₽
    assert checked.price_uzs > 100_000
    assert checked.url.startswith("https://pro-buket.uz/c/all/p/")


def test_probuket_keeps_the_old_price_and_the_shops_section():
    result = probuket.parse(fixture("probuket_catalog_real.html"), "https://pro-buket.uz/catalog/")
    on_sale = [validate(i, "pro-buket.uz") for i in result.items if i.old_price_text]
    assert on_sale, "the fixture should contain at least one discounted card"
    for item in on_sale:
        assert isinstance(item, ValidItem), item
        assert item.old_price_uzs > item.price_uzs
    assert any(i.site_category for i in result.items)
    assert any(i.availability == "in_stock" for i in result.items)


# ---------------------------------------------------------------------------
# loveflowers.uz: WooCommerce cards, "from" prices, pagination
# ---------------------------------------------------------------------------

def test_loveflowers_reads_cards_and_follows_pagination():
    result = loveflowers.parse(fixture("loveflowers_shop_real.html"), "https://loveflowers.uz/shop/")
    assert len(result.items) == 3
    assert result.next_url == "https://loveflowers.uz/shop/page/2/"
    for item in result.items:
        assert item.title and item.url.startswith("https://loveflowers.uz/product/")
        assert isinstance(validate(item, "loveflowers.uz"), ValidItem)


# ---------------------------------------------------------------------------
# kamilas.uz: sitemap -> product pages -> schema.org Product
# ---------------------------------------------------------------------------

def test_kamilas_sitemap_yields_only_product_pages():
    """The sitemap also lists /en/ translations of the same bouquets; collecting them would count
    every product twice (and they carry no price), so they must be filtered out."""
    result = kamilas.parse(fixture("kamilas_sitemap_real.xml"), "https://kamilas.uz/sitemap-0.xml")
    assert result.items == []
    assert result.extra_urls == ["https://kamilas.uz/product/buket-lazurnyj-bereg/",
                                 "https://kamilas.uz/product/buket-barhatnaya-malina/"]


def test_kamilas_product_page_gives_price_category_and_availability():
    result = kamilas.parse(fixture("kamilas_product_real.html"),
                           "https://kamilas.uz/product/buket-lazurnyj-bereg/")
    assert len(result.items) == 1
    item = result.items[0]
    assert (item.currency, item.availability, item.site_category) == ("UZS", "in_stock", "Букеты")
    checked = validate(item, "kamilas.uz")
    assert isinstance(checked, ValidItem), checked
    assert checked.price_uzs == 615000


@pytest.mark.parametrize("code", ["uzflora", "probuket", "loveflowers", "kamilas"])
def test_every_active_competitor_group_has_a_parser(code):
    parser = get_parser(code)
    assert parser.START_PATHS and callable(parser.parse)
