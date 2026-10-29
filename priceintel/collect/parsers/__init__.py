"""One parser per shop layout. Each module provides ``START_PATHS`` and
``parse(html, page_url) -> PageResult``. Parsers only extract; validation happens later."""
from dataclasses import dataclass, field

from priceintel.collect.validate import RawItem


@dataclass
class PageResult:
    items: list[RawItem]
    next_url: str | None = None
    # Further pages this page points at, e.g. the product pages listed in a sitemap. A page that
    # yields only extra_urls (no items) still counts as parsed: see runner._collect_shop.
    extra_urls: list[str] = field(default_factory=list)


def get_parser(shop_code: str):
    from priceintel.collect.parsers import kamilas, loveflowers, probuket, uzflora
    registry = {"uzflora": uzflora, "probuket": probuket, "loveflowers": loveflowers,
                "kamilas": kamilas}
    if shop_code not in registry:
        raise KeyError(f"no parser for shop {shop_code!r} yet")
    return registry[shop_code]
