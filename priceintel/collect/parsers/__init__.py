"""One parser per shop layout. Each module provides ``START_PATHS`` and
``parse(html, page_url) -> PageResult``. Parsers only extract; validation happens later."""
from dataclasses import dataclass

from priceintel.collect.validate import RawItem


@dataclass
class PageResult:
    items: list[RawItem]
    next_url: str | None


def get_parser(shop_code: str):
    from priceintel.collect.parsers import uzflora
    registry = {"uzflora": uzflora}
    if shop_code not in registry:
        raise KeyError(f"no parser for shop {shop_code!r} yet")
    return registry[shop_code]
