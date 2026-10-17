"""Dev reconnaissance for ADR-001: do the suspected network sites share a catalogue?

Fetches the first N catalogue pages of each site (>=6 s apart), extracts product URL
slugs and their first displayed price, and prints pairwise slug overlap and how many
shared products have the same price. Pages are cached in data/dev/recon/ (git-ignored).
This is NOT assessed collection; results only support the source-independence decision.

Usage:  python tools/recon/catalogue_overlap.py [pages]
"""
import html
import itertools
import pathlib
import re
import sys
import time
import urllib.request

UA = "Mozilla/5.0 (compatible; SecretPriceResearchBot/0.1; student project UDE5014CM)"
CACHE = pathlib.Path(__file__).resolve().parents[2] / "data" / "dev" / "recon"
NETWORK = ["loveflowers.uz", "dostavka-cvetov365.uz", "dostavka-cvetov24.uz", "ultraflowers.uz"]
PRICE = re.compile(r'woocommerce-Price-amount amount"><bdi>([\d,\s \.]+)')
PRODUCT_LINK = re.compile(r'href="https?://[^"/]+/product/([^"/]+)/"')


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def cards(page: str) -> dict[str, int | None]:
    """Map product slug -> first price shown after its link (None if not found)."""
    out: dict[str, int | None] = {}
    for m in PRODUCT_LINK.finditer(page):
        slug = m.group(1)
        if slug in out:
            continue
        p = PRICE.search(page, m.end(), m.end() + 3000)
        out[slug] = int(re.sub(r"\D", "", html.unescape(p.group(1)))) if p else None
    return out


def main(pages: int = 4) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    data: dict[str, dict[str, int | None]] = {}
    for site in NETWORK:
        found: dict[str, int | None] = {}
        for n in range(1, pages + 1):
            f = CACHE / f"{site}_p{n}.html"
            if not f.exists():
                f.write_text(fetch(f"https://{site}/shop/page/{n}/"), encoding="utf-8")
                time.sleep(6)
            found.update(cards(f.read_text(encoding="utf-8")))
        data[site] = found
        print(f"{site}: {len(found)} products on first {pages} pages")

    print("\npair | shared slugs / smaller catalogue | same price among shared")
    for a, b in itertools.combinations(NETWORK, 2):
        shared = set(data[a]) & set(data[b])
        same = sum(1 for k in shared if data[a][k] is not None and data[a][k] == data[b][k])
        print(f"{a:22} x {b:22} {len(shared):3}/{min(len(data[a]), len(data[b])):3}  same={same}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
