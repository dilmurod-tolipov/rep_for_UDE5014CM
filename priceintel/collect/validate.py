"""Validation of parsed product records before they are stored.

A record either becomes a ``ValidItem`` (stored as a price observation) or a ``Rejection``
(stored in ``rejected_records`` with the rule that failed). Nothing is silently dropped."""
import re
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

MIN_PRICE_UZS = 5_000        # below this is not a real bouquet/plant/gift price
MAX_PRICE_UZS = 50_000_000   # above this is almost certainly a parsing error
UZS_MARKERS = {"uzs", "сум", "so'm", "soʻm", "sum", "сўм"}
NUMBER = re.compile(r"\d[\d   ,.]*\d|\d")  # spaces allowed inside, line breaks not


@dataclass(frozen=True)
class RawItem:
    """What a parser extracted from one product card, before any checking."""
    url: str | None
    title: str | None
    price_text: str | None
    old_price_text: str | None = None
    currency: str | None = None
    availability: str = "unknown"
    external_id: str | None = None
    site_category: str | None = None


@dataclass(frozen=True)
class ValidItem:
    url: str
    title: str
    price_uzs: int
    old_price_uzs: int | None
    is_from_price: bool
    availability: str
    external_id: str | None
    site_category: str | None
    raw_price_text: str


@dataclass(frozen=True)
class Rejection:
    rule: str
    detail: str


def parse_price(text: str | None) -> tuple[int, bool] | None:
    """'115,000 UZS' -> (115000, False); 'от 22 000 сум' -> (22000, True);
    '150 000 – 300 000' -> (150000, True). Returns None if there is no number."""
    if not text:
        return None
    t = text.strip().lower()
    numbers = NUMBER.findall(t)
    if not numbers:
        return None
    is_from = t.startswith(("от", "from")) or len(numbers) > 1
    first = re.sub(r"[.,]\d{2}$", "", numbers[0].strip())  # drop a ".00" decimal tail
    return int(re.sub(r"\D", "", first)), is_from


def normalise_url(url: str) -> str:
    """https, lower-case host, no query string or fragment: one URL per product page."""
    p = urlsplit(url.strip())
    path = p.path or "/"
    return urlunsplit(("https", (p.hostname or "").lower(), path, "", ""))


def _same_site(host: str, shop_host: str) -> bool:
    strip = lambda h: h[4:] if h.startswith("www.") else h
    return strip(host.lower()) == strip(shop_host.lower())


def validate(item: RawItem, shop_host: str) -> ValidItem | Rejection:
    if not item.url:
        return Rejection("missing_url", "product card has no link")
    host = urlsplit(item.url).hostname or ""
    if not _same_site(host, shop_host):
        return Rejection("foreign_host", f"link points to {host!r}, not {shop_host!r}")
    title = " ".join((item.title or "").split())
    if not title:
        return Rejection("missing_title", "product has no title")
    if not item.price_text or not item.price_text.strip():
        return Rejection("missing_price", "product has no price")
    if item.currency and item.currency.strip().lower() not in UZS_MARKERS:
        return Rejection("currency_not_uzs", f"currency is {item.currency!r}")
    parsed = parse_price(item.price_text)
    if parsed is None:
        return Rejection("unparseable_price", f"no number in {item.price_text!r}")
    price, is_from = parsed
    if not MIN_PRICE_UZS <= price <= MAX_PRICE_UZS:
        return Rejection("price_out_of_range",
                         f"{price} UZS outside {MIN_PRICE_UZS}-{MAX_PRICE_UZS}")
    old = None
    if item.old_price_text:
        parsed_old = parse_price(item.old_price_text)
        if parsed_old is None or parsed_old[0] <= price:
            return Rejection("old_price_not_above_price",
                             f"old price {item.old_price_text!r} is not above {price}")
        old = parsed_old[0]
    availability = item.availability if item.availability in ("in_stock", "out_of_stock") else "unknown"
    return ValidItem(normalise_url(item.url), title, price, old, is_from, availability,
                     item.external_id, item.site_category, item.price_text.strip())
