"""Turn a Secret channel caption into (title, cleaned caption, price) or a named rejection.

Secret writes prices as 'Стоимость: 2.890.000'. Only a labelled price is accepted, so phone numbers
in the caption can never be mistaken for a price. Contact lines are removed before storage."""
import re

from priceintel.collect.validate import MAX_PRICE_UZS, MIN_PRICE_UZS, Rejection, parse_price

PRICE_LABEL = re.compile(
    r"(?:стоимость|цена|все\s+по|narxi|narx|price)[ \t]*[:\-–—]?[ \t]*(\d[\d   .,]*\d|\d)",
    re.IGNORECASE)  # no line breaks inside a number: '1.590.000\n2 варианта' must not merge
CONTACT_LINE = re.compile(r"(\+?998|@\w|t\.me/|https?://|\b\d{2}\s?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b)")


def clean_caption(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln and not CONTACT_LINE.search(ln))


def title_of(caption: str, post_id: int) -> str:
    for ln in caption.splitlines():
        if ln.strip() and not PRICE_LABEL.search(ln):
            return ln.strip()[:200]
    return f"Post {post_id}"


def extract_price(text: str) -> tuple[int, str] | Rejection:
    found = [(m.group(0).strip(), parse_price(m.group(1))) for m in PRICE_LABEL.finditer(text)]
    found = [(raw, p[0]) for raw, p in found if p is not None]
    if not found:
        return Rejection("no_price", "no labelled price (e.g. 'Стоимость: ...') in the caption")
    values = {v for _, v in found}
    if len(values) > 1:
        return Rejection("multiple_prices", f"several prices {sorted(values)}; cannot tell which applies")
    raw, price = found[0]
    if not MIN_PRICE_UZS <= price <= MAX_PRICE_UZS:
        return Rejection("price_out_of_range", f"{price} UZS outside {MIN_PRICE_UZS}-{MAX_PRICE_UZS}")
    return price, raw
