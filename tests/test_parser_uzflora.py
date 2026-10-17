"""uzflora parser against a synthetic page that mimics the real layout."""
from pathlib import Path

from priceintel.collect.parsers import uzflora

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_cards_sale_prices_stock_and_next_link():
    page = (FIXTURES / "uzflora_page1_synthetic.html").read_text(encoding="utf-8")
    result = uzflora.parse(page, "https://uzflora.com/shop/")
    assert len(result.items) == 3
    roses, box, plant = result.items
    assert roses.title == "Test 25 red roses" and roses.price_text.startswith("450,000")
    assert roses.currency == "UZS" and roses.availability == "in_stock"
    assert roses.external_id == "9001" and roses.site_category == "bukety"
    assert box.price_text.startswith("560,000") and box.old_price_text.startswith("700,000")
    assert box.availability == "out_of_stock"
    assert box.site_category == "czvetochnye-kompoziczii,podarki"
    assert plant.price_text == ""          # parser extracts; the validator will reject it
    assert result.next_url == "https://uzflora.com/shop/page/2/"


def test_last_page_has_no_next_link():
    page = (FIXTURES / "uzflora_page2_synthetic.html").read_text(encoding="utf-8")
    assert uzflora.parse(page, "https://uzflora.com/shop/page/2/").next_url is None


def test_page_without_cards_returns_no_items():
    assert uzflora.parse("<html><body>maintenance</body></html>", "https://uzflora.com/shop/").items == []
