"""uzflora.com (WooCommerce, custom 'uz-product-card' theme).

Card layout (2026-10-17):
  <li class="uz-product-card product post-1001 instock product_cat-bukety ...">
    <span class="product-price"> [<del>old</del><ins>new</ins> | price] <span ...currencySymbol>UZS</span>
    <a class="product-name" href="https://uzflora.com/product/...">Title</a>
Pagination: <a class="next page-numbers" href=".../shop/page/2/">
"""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from priceintel.collect.parsers import PageResult
from priceintel.collect.validate import RawItem

START_PATHS = ["/shop/"]
# The WOOCS currency switcher shows USD to visitors outside Uzbekistan (seen from GitHub's runners,
# 2026-10-17). Forcing UZS returns exactly the prices a local customer sees (verified: identical to a
# run from Tashkent). UZS is the shop's base currency; robots.txt allows query strings here.
QUERY = "currency=UZS"


def _text(el) -> str | None:
    return el.get_text(" ", strip=True) if el is not None else None


def parse(html: str, page_url: str) -> PageResult:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for card in soup.select("li.uz-product-card"):
        classes = card.get("class", [])
        link = card.select_one("a.product-name")
        price_box = card.select_one(".product-price")
        old_el = price_box.select_one("del") if price_box else None
        new_el = price_box.select_one("ins") if price_box else None
        currency_el = price_box.select_one(".woocommerce-Price-currencySymbol") if price_box else None
        if "instock" in classes:
            availability = "in_stock"
        elif "outofstock" in classes:
            availability = "out_of_stock"
        else:
            availability = "unknown"
        post_id = next((m.group(1) for c in classes if (m := re.fullmatch(r"post-(\d+)", c))), None)
        cats = sorted(c.removeprefix("product_cat-") for c in classes if c.startswith("product_cat-"))
        items.append(RawItem(
            url=urljoin(page_url, link["href"]) if link and link.get("href") else None,
            title=_text(link),
            price_text=_text(new_el) if new_el is not None else _text(price_box),
            old_price_text=_text(old_el),
            currency=_text(currency_el),
            availability=availability,
            external_id=post_id,
            site_category=",".join(cats) or None,
        ))
    nxt = soup.select_one("a.next.page-numbers")
    return PageResult(items, urljoin(page_url, nxt["href"]) if nxt and nxt.get("href") else None)
