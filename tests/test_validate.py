"""Validation rules: valid records pass, every invalid kind is rejected with a named rule."""
import pytest

from priceintel.collect.validate import RawItem, Rejection, ValidItem, parse_price, validate

HOST = "uzflora.com"


def item(**kw):
    base = dict(url="https://uzflora.com/product/roses-25/", title="25 red roses",
                price_text="450,000 UZS", currency="UZS", availability="in_stock")
    return RawItem(**{**base, **kw})


@pytest.mark.parametrize("text, expected", [
    ("115,000 UZS", (115000, False)),
    ("115 000 сум", (115000, False)),
    ("115 000 сум", (115000, False)),
    ("от 22 000 сум", (22000, True)),
    ("150 000 – 300 000", (150000, True)),
    ("1,250,000.00 UZS", (1250000, False)),
    ("Цена по запросу", None),
    ("", None),
])
def test_parse_price(text, expected):
    assert parse_price(text) == expected


def test_valid_item_is_normalised():
    v = validate(item(url="https://UZFLORA.com/product/roses-25/?utm_source=x#top",
                      old_price_text="500,000 UZS"), HOST)
    assert isinstance(v, ValidItem)
    assert v.url == "https://uzflora.com/product/roses-25/"
    assert (v.price_uzs, v.old_price_uzs, v.is_from_price) == (450000, 500000, False)


@pytest.mark.parametrize("kw, rule", [
    ({"url": None}, "missing_url"),
    ({"url": "https://evil.example/product/x/"}, "foreign_host"),
    ({"title": "   "}, "missing_title"),
    ({"price_text": None}, "missing_price"),
    ({"currency": "USD", "price_text": "35 USD"}, "currency_not_uzs"),
    ({"price_text": "Цена по запросу"}, "unparseable_price"),
    ({"price_text": "0 UZS"}, "price_out_of_range"),
    ({"price_text": "900,000,000 UZS"}, "price_out_of_range"),
    ({"old_price_text": "400,000 UZS"}, "old_price_not_above_price"),
])
def test_invalid_items_are_rejected_with_rule(kw, rule):
    r = validate(item(**kw), HOST)
    assert isinstance(r, Rejection) and r.rule == rule


def test_boundary_prices():
    assert isinstance(validate(item(price_text="5,000 UZS"), HOST), ValidItem)       # minimum allowed
    assert isinstance(validate(item(price_text="4,999 UZS"), HOST), Rejection)
    assert isinstance(validate(item(url="https://www.uzflora.com/product/a/"), HOST), ValidItem)
