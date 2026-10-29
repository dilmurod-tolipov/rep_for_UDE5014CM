"""pro-buket.uz (WordPress/WooCommerce with a custom catalogue theme).

Card layout (checked 2026-10-29 on https://pro-buket.uz/catalog/):

    <div class="pr-bl" data-cat="rozy" data-id="7837">
      <div class="h-3"><a href="/c/all/p/rozy-buket-iz-15-rozovye-v-korobke/">15 розовых роз в коробке</a>
      <div class="pr-status pr-status--on">В наличии</div>
      <div class="price">    <span class="pay_arr" data-pay="UZS" data-val="1300578">1 300 578 сум</span> ...
      <div class="price-old"><span class="pay_arr" data-pay="UZS" data-val="1995961">...

The shop shows the same price in UZS, USD and RUB and switches with JavaScript, so the UZS figure
is taken from the ``data-pay="UZS"`` span rather than from whichever currency the page renders
first. ``data-val`` holds the plain number, which avoids re-parsing thousand separators.

robots.txt (checked 2026-10-29): Crawl-delay 5; `/*?*` (so no query strings), `/all/`, `/search/`,
`/articles/`, `/c/nedorogie-cvety/` and `/c/voshititelnye-bukety/` are disallowed. Product URLs are
`/c/all/p/<slug>/`, which does not start with `/all/`, so they are allowed; the catalogue page
itself carries no query string. The robots rules are enforced by the runner for every URL.
"""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from priceintel.collect.parsers import PageResult
from priceintel.collect.validate import RawItem

START_PATHS = ["/catalog/"]


def _uzs(box) -> str | None:
    """The UZS amount of a price block, from the currency-tagged span."""
    if box is None:
        return None
    span = box.select_one('.pay_arr[data-pay="UZS"]')
    if span is None:
        return None
    value = (span.get("data-val") or "").strip()
    return value or span.get_text(" ", strip=True)


def parse(html: str, page_url: str) -> PageResult:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for card in soup.select("div.pr-bl"):
        link = card.select_one(".h-3 a[href]") or card.select_one("a.pr-url[href]")
        status = card.select_one(".pr-status")
        status_text = status.get_text(" ", strip=True).lower() if status else ""
        if "нет" in status_text:
            availability = "out_of_stock"
        elif "налич" in status_text:
            availability = "in_stock"
        else:
            availability = "unknown"
        items.append(RawItem(
            url=urljoin(page_url, link["href"]) if link else None,
            title=link.get_text(" ", strip=True) if link else None,
            price_text=_uzs(card.select_one(".price")),
            old_price_text=_uzs(card.select_one(".price-old")),
            currency="UZS" if card.select_one('.price .pay_arr[data-pay="UZS"]') else None,
            availability=availability,
            external_id=card.get("data-id"),
            site_category=card.get("data-cat"),
        ))
    # Pagination: "/catalog/page/2/" style links, if the theme renders them.
    nxt = soup.select_one("a.next.page-numbers, a.next")
    next_url = urljoin(page_url, nxt["href"]) if nxt and nxt.get("href") else None
    if next_url and not re.search(r"/page/\d+/", next_url):
        next_url = None     # not a pagination link, ignore it
    return PageResult(items, next_url)
