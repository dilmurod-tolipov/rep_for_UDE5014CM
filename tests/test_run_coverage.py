"""A run that loses an operator group is not a successful run.

Found four days into the approved window: loveflowers.uz did not answer its robots.txt within the
timeout on five of the first seven assessed runs. The collector correctly refused to crawl a shop
whose robots.txt it could not read — but the run still reported `success`, because the skipped shop's
pages were never requested and the page success rate stayed at 100%. The approved success rate was
therefore measuring the wrong thing."""
import pytest

from priceintel.collect.http import FetchAttempt
from priceintel.collect.runner import ROBOTS_ATTEMPTS, collect
from tests.conftest import FAKE_COMMIT

ROBOTS = "User-agent: *\nAllow: /\n"
CARD = """
<li class="uz-product-card product instock product_cat-bukety">
  <span class="product-price">250 000 <span class="woocommerce-Price-currencySymbol">UZS</span></span>
  <a class="product-name" href="https://uzflora.com/product/test-bouquet/">Букет «Тест»</a>
</li>
"""


class ScriptedFetcher:
    """Answers each URL from a script; records what was asked for."""

    def __init__(self, responses: dict, timeout_s: float = 30):
        self.responses = responses
        self.timeout_s = timeout_s
        self.requested: list[str] = []
        self.now = lambda: "2026-11-13T06:00:00Z"

    def get(self, url, min_delay_s, *, max_attempts=None, backoff_s=None):
        self.requested.append(url)
        body, status, error = self.responses.get(url, ("", 404, None))
        tries = max_attempts or 3
        if status is None:            # a network failure is retried to the limit
            return [FetchAttempt(url, self.now(), n, None, None, 1, error) for n in range(1, tries + 1)]
        return [FetchAttempt(url, self.now(), 1, status, body.encode("utf-8"), 1, None)]


def responses_for(*, uzflora_robots=True, loveflowers_robots=True):
    out = {}
    for host, ok in (("uzflora.com", uzflora_robots), ("loveflowers.uz", loveflowers_robots)):
        out[f"https://{host}/robots.txt"] = ((ROBOTS, 200, None) if ok else
                                             ("", None, "ReadTimeout: too slow"))
    out["https://uzflora.com/shop/?currency=UZS"] = (f"<ul>{CARD}</ul>", 200, None)
    for path in ("bukety", "rozy", "tyulpany", "tsvety-v-korobke", "korziny-s-tsvetami",
                 "tsvety-raznye", "podarki"):
        out[f"https://loveflowers.uz/tcat/{path}/"] = (
            '<div class="tovar"><a href="https://loveflowers.uz/product/x/"><h2>Букет «Т»</h2>'
            '<p class="price">300 000 <span class="woocommerce-Price-currencySymbol">сум</span>'
            "</p></a></div>", 200, None)
    return out


def run_two_shops(conn, **kw):
    fetcher = ScriptedFetcher(responses_for(**kw))
    summary = collect(conn, ["uzflora", "loveflowers"], purpose="test", fetcher=fetcher,
                      git=(FAKE_COMMIT, False))
    return summary, fetcher


def test_a_run_that_reaches_every_group_is_successful(market_db):
    summary, _ = run_two_shops(market_db)
    assert summary.status == "success"
    assert (summary.shops_collected, summary.shops_expected) == (2, 2)
    row = market_db.execute("SELECT shops_collected, shops_expected, status FROM scrape_runs"
                            " WHERE run_id = ?", (summary.run_id,)).fetchone()
    assert (row["shops_collected"], row["shops_expected"], row["status"]) == (2, 2, "success")


def test_a_lost_group_makes_the_run_partial_not_successful(market_db):
    """The defect this test exists for: before the fix this run reported success."""
    summary, _ = run_two_shops(market_db, loveflowers_robots=False)
    assert summary.shops_collected == 1 and summary.shops_expected == 2
    assert summary.status == "partial", "a run missing an operator group is not successful"
    assert any("no records collected" in e for e in summary.errors)
    assert summary.pages_ok == summary.pages_requested, (
        "the pages that were requested all succeeded - which is why the page rate alone was "
        "not enough to notice the loss")


def test_an_unreadable_robots_file_is_retried_harder_than_a_page(market_db):
    """robots.txt gates a whole shop, so it gets more attempts than an ordinary page."""
    _, fetcher = run_two_shops(market_db, loveflowers_robots=False)
    attempts = market_db.execute(
        "SELECT COUNT(*) FROM fetch_log WHERE url = 'https://loveflowers.uz/robots.txt'").fetchone()[0]
    assert attempts == ROBOTS_ATTEMPTS >= 5


def test_the_shop_is_still_not_crawled_when_robots_cannot_be_read(market_db):
    """Politeness is not traded for coverage: an unreadable robots.txt still means no crawling."""
    _, fetcher = run_two_shops(market_db, loveflowers_robots=False)
    assert not any("/tcat/" in url for url in fetcher.requested)
    skipped = market_db.execute(
        "SELECT COUNT(*) FROM fetch_log WHERE robots_allowed = 0").fetchone()[0]
    assert skipped >= 1


def test_coverage_view_names_the_missing_group(market_db):
    """The view lists every active group with no observations in that run. The scheduled runs always
    target all four groups, so for them the list is exactly what was lost; this test targets two
    shops, so the two it never asked for are listed as well."""
    summary, _ = run_two_shops(market_db, loveflowers_robots=False)
    row = market_db.execute("SELECT groups_missing FROM v_run_coverage WHERE run_id = ?",
                            (summary.run_id,)).fetchone()
    missing = set(row["groups_missing"].split(", "))
    assert "LOVEFLOWERS_NET" in missing
    assert "UZFLORA" not in missing          # it was collected


@pytest.mark.parametrize("kw, expected", [
    ({}, "success"),
    ({"loveflowers_robots": False}, "partial"),
    ({"uzflora_robots": False, "loveflowers_robots": False}, "failed"),
])
def test_run_status_reflects_coverage(market_db, kw, expected):
    summary, _ = run_two_shops(market_db, **kw)
    assert summary.status == expected
