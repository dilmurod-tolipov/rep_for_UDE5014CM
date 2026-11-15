"""loveflowers.uz - the canonical domain of the LOVEFLOWERS_NET operator group (ADR-001).

WooCommerce on a custom theme. The theme was **redesigned around 13 November 2026**, four days into
the assessed collection window, and the group contributed nothing to five runs until it was noticed
on 16 November. Both layouts are read, because the earlier fixture is the evidence for the data
already collected and must keep parsing:

* old (to 2026-11-12): ``div.tovar`` > ``h2`` + ``p.price``, one page per section;
* new (from 2026-11-13): ``article.tovar[data-product]`` > ``a.card-link`` > ``h3`` + ``p.price``,
  with a ``div.desc`` composition line and **paginated sections** (``a.page-numbers.next``).

Sale prices appear as ``<del>old</del><ins>new</ins>`` inside ``p.price`` in both layouts, and most
cards show a starting price ("от 550 000 сум"): 38 of 56 on the first bouquet page. The validator
marks those ``is_from_price`` and the pipeline keeps them as lower bounds rather than prices.

The new design paginates: the bouquet section alone runs to 19 pages. The runner's queue is
breadth-first across the seven start paths, so the per-shop page cap spreads evenly over the sections
instead of exhausting itself on the first one.

Only this domain is collected. dostavka-cvetov365.uz, dostavka-cvetov24.uz and ultraflowers.uz serve
the same catalogue under the same terms and are registered as mirrors, which an automated test
enforces (`test_source_groups.py`), so mirrored listings cannot inflate the product counts.

robots.txt (checked 2026-10-17, re-checked 2026-11-16): `/*?` and admin paths disallowed; the shop's
user agreement asks that quoted material link back to the site, and every record stores its source
URL.
"""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from priceintel.collect.parsers import PageResult
from priceintel.collect.validate import RawItem

# /shop/ lists everything but builds its grid with admin-ajax.php, which robots.txt disallows
# (/wp-admin/ and /*?). The section pages render their products in the HTML, so the collector reads
# those - one request each, and the section slug becomes the listing's site_category.
# Promotion sections (/tcat/aktsii-rozy/, /tcat/topsale/) are left out on purpose: they repeat
# products from the sections below and group them by price, which categories must not depend on.
START_PATHS = ["/tcat/bukety/", "/tcat/rozy/", "/tcat/tyulpany/", "/tcat/tsvety-v-korobke/",
               "/tcat/korziny-s-tsvetami/", "/tcat/tsvety-raznye/", "/tcat/podarki/"]
SECTION = re.compile(r"/tcat/([a-z0-9-]+)")
CARD = "article.tovar, div.tovar"           # new layout, then the old one


def _text(el) -> str | None:
    return el.get_text(" ", strip=True) if el is not None else None


def parse(html: str, page_url: str) -> PageResult:
    soup = BeautifulSoup(html, "html.parser")
    section = SECTION.search(page_url)
    items = []
    for card in soup.select(CARD):
        link = card.select_one("a[href*='/product/']")
        price_box = card.select_one("p.price")
        old_el = price_box.select_one("del") if price_box else None
        new_el = price_box.select_one("ins") if price_box else None
        # New layout for a discounted card:
        #   <del>690 000 сум</del> <span class="from">от</span> <span class="amount">550 000 сум</span>
        # The current price is the amount, not the whole box - reading the box text gave
        # "690 000 сум от 550 000 сум −20%", whose first number is the OLD price, so every
        # discounted card was quarantined as old_price_not_above_price. The "от" marker is kept
        # with the amount, because "от 550 000 сум" is what the shop actually advertises.
        if new_el is None and price_box is not None:
            amount = price_box.select_one("span.amount")
            from_marker = price_box.select_one("span.from")
            if amount is not None:
                new_el = amount
                if from_marker is not None:
                    current_text = f"{_text(from_marker)} {_text(amount)}"
                else:
                    current_text = _text(amount)
            else:
                current_text = _text(price_box)
        else:
            current_text = _text(new_el) if new_el is not None else _text(price_box)
        title = card.select_one("h3") or card.select_one("h2")
        # The composition line ("Состав: розы — 15 шт") arrived with the new design and is the
        # source of the stem-count feature; the old layout has none.
        desc = card.select_one(".desc")
        external_id = card.get("data-product")
        if external_id is None:
            cart = card.select_one("[data-product_id]")
            external_id = cart.get("data-product_id") if cart else None
        items.append(RawItem(
            url=urljoin(page_url, link["href"]) if link and link.get("href") else None,
            title=_text(title) or _text(link),
            price_text=current_text,
            old_price_text=_text(old_el),
            currency=_text(price_box.select_one(".woocommerce-Price-currencySymbol"))
            if price_box else None,
            availability="unknown",          # the card does not state stock; the product page does
            external_id=external_id,
            site_category=section.group(1) if section else None,
            variant_label=None,              # one price per card on the section pages
            composition_text=_text(desc),
        ))
    nxt = soup.select_one("a.page-numbers.next, a.next.page-numbers")
    return PageResult(items, urljoin(page_url, nxt["href"]) if nxt and nxt.get("href") else None)
