"""loveflowers.uz - the canonical domain of the LOVEFLOWERS_NET operator group (ADR-001).

WooCommerce on a custom theme. Card layout (fixture saved 2026-10-17, re-checked 2026-10-29):

    <div class="tovar col-md-3 col-sm-4">
      <a class="woocommerce-loop-product__link" href="https://loveflowers.uz/product/<slug>/">
        <h2>Торт Ягодно-творожный</h2>
        <p class="price"><span class="amount"><bdi>320,000 <span class="currencySymbol">сум</span></bdi></span>
      <a class="add_to_cart_button" data-product_id="49006">

Sale prices appear as <del>old</del><ins>new</ins> inside the same `p.price`, and many listings show
a starting price ("от 22 000 сум") or a range; the validator flags both as `is_from_price`, so a
"from" price is never compared as if it were the price of a specific bouquet.

Only this domain is collected. dostavka-cvetov365.uz, dostavka-cvetov24.uz and ultraflowers.uz serve
the same catalogue under the same terms and are registered as mirrors, which an automated test
enforces (`test_source_groups.py`), so mirrored listings cannot inflate the product counts.

robots.txt (checked 2026-10-17): `/*?` and admin paths disallowed; the shop's user agreement asks
that quoted material link back to the site, and every record stores its source URL.
"""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from priceintel.collect.parsers import PageResult
from priceintel.collect.validate import RawItem

# /shop/ lists everything but now builds its grid with admin-ajax.php, which robots.txt disallows
# (/wp-admin/ and /*?). The section pages still render their products in the HTML, so the collector
# reads those instead - one request each, and the section slug becomes the listing's site_category.
# Promotion sections (/tcat/aktsii-rozy/, /tcat/topsale/) are left out on purpose: they repeat
# products from the sections below and group them by price, which categories must not depend on.
START_PATHS = ["/tcat/bukety/", "/tcat/rozy/", "/tcat/tyulpany/", "/tcat/tsvety-v-korobke/",
               "/tcat/korziny-s-tsvetami/", "/tcat/tsvety-raznye/", "/tcat/podarki/"]
SECTION = re.compile(r"/tcat/([a-z0-9-]+)")


def _text(el) -> str | None:
    return el.get_text(" ", strip=True) if el is not None else None


def parse(html: str, page_url: str) -> PageResult:
    soup = BeautifulSoup(html, "html.parser")
    section = SECTION.search(page_url)
    items = []
    for card in soup.select("div.tovar"):
        link = card.select_one("a[href*='/product/']")
        price_box = card.select_one("p.price")
        old_el = price_box.select_one("del") if price_box else None
        new_el = price_box.select_one("ins") if price_box else None
        cart = card.select_one("[data-product_id]")
        currency = price_box.select_one(".woocommerce-Price-currencySymbol") if price_box else None
        items.append(RawItem(
            url=urljoin(page_url, link["href"]) if link and link.get("href") else None,
            title=_text(card.select_one("h2")) or _text(link),
            price_text=_text(new_el) if new_el is not None else _text(price_box),
            old_price_text=_text(old_el),
            currency=_text(currency),
            availability="unknown",          # the card does not state stock; the product page does
            external_id=cart.get("data-product_id") if cart else None,
            site_category=section.group(1) if section else None,
        ))
    nxt = soup.select_one("a.next.page-numbers")
    return PageResult(items, urljoin(page_url, nxt["href"]) if nxt and nxt.get("href") else None)
