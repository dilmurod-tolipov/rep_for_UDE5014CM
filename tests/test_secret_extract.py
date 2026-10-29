"""Caption parsing for Secret's offers: labelled price only, contacts removed, ambiguous posts
rejected. The channel-page parser these rules were first written for was removed on 2026-10-29;
the same functions now serve the owner-provided export (`priceintel/reference/offers.py`)."""
from pathlib import Path

import pytest

from priceintel.collect.validate import Rejection
from priceintel.secret.extract import clean_caption, extract_price, title_of

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("text, price", [
    ("Особенная красота 💜\n\nСтоимость: 2.890.000🤍", 2890000),
    ("Стоимость:4.100.000 🤍", 4100000),
    ("Тюльпаны\nСтоимость: 750 000 сум", 750000),
    ("Narxi: 1 200 000 so'm", 1200000),
    ("Стоимость: 1.590.000\n2 варианта упаковки", 1590000),   # next line must not merge into the number
    ("Воздушные букеты из гортензии🤍\nВсе по: 1.250.000🤍", 1250000),  # found in dev run 1 (was missed)
])
def test_labelled_price_is_extracted(text, price):
    assert extract_price(text)[0] == price


@pytest.mark.parametrize("text, rule", [
    ("Акция дня!\n📞 +998 90 000 00 00", "no_price"),              # phone number is not a price
    ("Стоимость: 2.890.000\nЦена: 3.100.000", "multiple_prices"),
    ("Стоимость: 500", "price_out_of_range"),
])
def test_ambiguous_or_missing_prices_are_rejected(text, rule):
    r = extract_price(text)
    assert isinstance(r, Rejection) and r.rule == rule


def test_contact_lines_are_removed_and_title_taken_from_first_line():
    text = "Нежные пионы 🎀\n\nСтоимость: 1.180.000\n📞 +998 90 000 00 00\n📲 @shop_contact\nhttps://t.me/x"
    cleaned = clean_caption(text)
    assert "+998" not in cleaned and "@" not in cleaned and "t.me" not in cleaned
    assert title_of(cleaned, 1) == "Нежные пионы 🎀"
    assert title_of("Стоимость: 1.000.000", 7) == "Post 7"
