"""kamilas.uz - catalogue pages are built in the browser, so the sitemap is used instead.

The catalogue page (https://kamilas.uz/catalog/) renders only four cards in the HTML and loads the
rest with JavaScript, which this project does not execute. Rather than run a headless browser for one
shop, the collector follows the route the shop publishes for crawlers: `robots.txt` names
`sitemap-index.xml`, which lists `sitemap-0.xml`, which lists every product page. Each product page
carries a schema.org Product block with the price in UZS, so one request per product gives a complete,
machine-readable record:

    {"@type": "Product", "name": "Букет «Лазурный берег»", "category": "Букеты",
     "offers": {"priceCurrency": "UZS", "price": 615000, "availability": ".../InStock"}}

The sitemap pages return no products of their own; they return ``extra_urls``, which the runner adds
to the queue (one request every `crawl_delay_s` seconds, like any other page).

Cost: one request per product per run instead of one per catalogue page. With ~100 products and a 5 s
delay that is about 9 minutes per run, which the twice-daily schedule absorbs; `--max-pages` caps it.

robots.txt (checked 2026-10-29): `User-agent: *` / `Allow: /`, no Crawl-delay (the shop registry's
5 s applies).
"""
import json
import re
import warnings
from urllib.parse import urljoin

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from priceintel.collect.parsers import PageResult
from priceintel.collect.validate import RawItem

START_PATHS = ["/sitemap-index.xml"]
# Only the Russian product pages. The sitemap also lists /en/product/<slug>/ translations of the
# same bouquets, which carry no price in their Product block and would otherwise count twice.
PRODUCT_PATH = re.compile(r"^https://[^/]+/product/[^/]+/?$")
AVAILABILITY = {"instock": "in_stock", "outofstock": "out_of_stock",
                "soldout": "out_of_stock", "discontinued": "out_of_stock"}


def _sitemap_urls(soup: BeautifulSoup) -> list[str]:
    return [loc.get_text(strip=True) for loc in soup.find_all("loc") if loc.get_text(strip=True)]


def _products(soup: BeautifulSoup) -> list[dict]:
    """Every schema.org Product block on the page, whether or not it sits in an @graph."""
    found = []
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for node in (data.get("@graph", [data]) if isinstance(data, dict) else data):
            if isinstance(node, dict) and node.get("@type") == "Product":
                found.append(node)
    return found


def parse(html: str, page_url: str) -> PageResult:
    # html.parser reads the sitemap XML well enough for <loc> elements, and avoids depending on
    # lxml; bs4's "this is XML" warning is therefore expected here and not a defect.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
        soup = BeautifulSoup(html, "html.parser")

    if "<sitemapindex" in html or "<urlset" in html:
        urls = _sitemap_urls(soup)
        # A sitemap index points at further sitemaps; a urlset points at pages. Keep product pages.
        return PageResult([], None,
                          extra_urls=[u for u in urls
                                      if u.endswith(".xml") or PRODUCT_PATH.match(u)])

    items = []
    for product in _products(soup):
        offer = product.get("offers") or {}
        if isinstance(offer, list):
            offer = offer[0] if offer else {}
        availability = str(offer.get("availability", "")).rsplit("/", 1)[-1].lower()
        price = offer.get("price")
        items.append(RawItem(
            url=urljoin(page_url, product.get("url") or page_url),
            title=product.get("name"),
            price_text=None if price is None else str(price),
            old_price_text=None,
            currency=offer.get("priceCurrency"),
            availability=AVAILABILITY.get(availability, "unknown"),
            external_id=None,
            site_category=product.get("category"),
        ))
    return PageResult(items, None)
