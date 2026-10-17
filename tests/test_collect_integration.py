"""End-to-end collection run against a fake website (no network): fetch -> parse -> validate ->
persist with provenance -> retrieve. Uses the synthetic fixtures only."""
from pathlib import Path

import requests
from requests.adapters import BaseAdapter

from priceintel.collect.http import Fetcher
from priceintel.collect.runner import CollectError, collect

FIXTURES = Path(__file__).parent / "fixtures"
FAKE_GIT = ("1" * 40, False)


class FakeSite(BaseAdapter):
    """Serves canned responses; a list value is consumed one response per request."""

    def __init__(self, routes):
        super().__init__()
        self.routes, self.requests = routes, []

    def send(self, request, **kwargs):
        self.requests.append(request.url)
        route = self.routes.get(request.url, (404, "not found"))
        if isinstance(route, list):
            route = route.pop(0) if len(route) > 1 else route[0]
        status, body = route
        resp = requests.Response()
        resp.status_code, resp._content, resp.url, resp.request = status, body.encode("utf-8"), request.url, request
        return resp

    def close(self):
        pass


def make_fetcher(routes):
    session = requests.Session()
    site = FakeSite(routes)
    session.mount("https://", site)
    return Fetcher(session=session, sleep=lambda s: None), site


def uzflora_routes(robots="User-agent: *\nDisallow: /wp-admin/\n", page2=None):
    p1 = (FIXTURES / "uzflora_page1_synthetic.html").read_text(encoding="utf-8")
    p2 = (FIXTURES / "uzflora_page2_synthetic.html").read_text(encoding="utf-8")
    return {
        "https://uzflora.com/robots.txt": (200, robots),
        "https://uzflora.com/shop/?currency=UZS": (200, p1),
        "https://uzflora.com/shop/page/2/?currency=UZS": page2 if page2 is not None else (200, p2),
    }


def test_run_saves_valid_records_with_provenance_and_quarantines_invalid(market_db):
    fetcher, _ = make_fetcher(uzflora_routes())
    s = collect(market_db, ["uzflora"], purpose="dev", fetcher=fetcher, git=FAKE_GIT)

    assert s.status == "success" and (s.pages_ok, s.pages_requested) == (2, 2)
    # page 1: roses + box valid, plant without price rejected; page 2: USD rejected, roses duplicate
    assert (s.observations_saved, s.records_rejected, s.duplicates_skipped) == (2, 2, 1)

    rows = market_db.execute(
        "SELECT o.price_uzs, o.old_price_uzs, o.availability, f.url AS fetched, f.http_status,"
        " f.content_sha256, r.git_commit, r.purpose, l.site_category"
        " FROM price_observations o JOIN fetch_log f USING (fetch_id)"
        " JOIN scrape_runs r ON r.run_id = o.run_id JOIN listings l ON l.listing_id = o.listing_id"
        " ORDER BY o.price_uzs").fetchall()
    assert [(r["price_uzs"], r["old_price_uzs"]) for r in rows] == [(450000, None), (560000, 700000)]
    assert all(r["fetched"] == "https://uzflora.com/shop/?currency=UZS" and r["http_status"] == 200 for r in rows)
    assert all(len(r["content_sha256"]) == 64 and r["git_commit"] == "1" * 40 for r in rows)
    assert {r["site_category"] for r in rows} == {"bukety", "czvetochnye-kompoziczii,podarki"}

    rules = sorted(r[0] for r in market_db.execute("SELECT rule FROM rejected_records"))
    assert rules == ["currency_not_uzs", "missing_price"]

    latest = market_db.execute("SELECT shop, price_uzs FROM v_latest_prices ORDER BY price_uzs").fetchall()
    assert [(r["shop"], r["price_uzs"]) for r in latest] == [("uzflora", 450000), ("uzflora", 560000)]


def test_rerun_adds_observations_but_not_duplicate_listings(market_db):
    for _ in range(2):
        fetcher, _ = make_fetcher(uzflora_routes())
        collect(market_db, ["uzflora"], fetcher=fetcher, git=FAKE_GIT)
    q = lambda sql: market_db.execute(sql).fetchone()[0]
    assert q("SELECT COUNT(*) FROM listings") == 2
    assert q("SELECT COUNT(*) FROM price_observations") == 4
    assert q("SELECT COUNT(DISTINCT run_id) FROM price_observations") == 2


def test_server_error_is_retried_and_every_attempt_logged(market_db):
    p2 = (FIXTURES / "uzflora_page2_synthetic.html").read_text(encoding="utf-8")
    fetcher, site = make_fetcher(uzflora_routes(page2=[(503, "busy"), (200, p2)]))
    s = collect(market_db, ["uzflora"], fetcher=fetcher, git=FAKE_GIT)
    assert s.status == "success"
    attempts = market_db.execute(
        "SELECT attempt, http_status FROM fetch_log WHERE url LIKE '%/page/2/%' ORDER BY attempt").fetchall()
    assert [(a["attempt"], a["http_status"]) for a in attempts] == [(1, 503), (2, 200)]


def test_robots_disallowed_page_is_never_requested(market_db):
    fetcher, site = make_fetcher(uzflora_routes(robots="User-agent: *\nDisallow: /shop/page/\n"))
    s = collect(market_db, ["uzflora"], fetcher=fetcher, git=FAKE_GIT)
    assert not any("/shop/page/2/" in u for u in site.requests)
    assert s.robots_skipped == 1 and s.pages_requested == 1
    refused = market_db.execute("SELECT robots_allowed, http_status FROM fetch_log WHERE url LIKE '%/page/2/%'").fetchone()
    assert (refused["robots_allowed"], refused["http_status"]) == (0, None)


def test_unreachable_site_fails_the_run_without_crashing(market_db):
    fetcher, _ = make_fetcher({"https://uzflora.com/robots.txt": (500, "down")})
    s = collect(market_db, ["uzflora"], fetcher=fetcher, git=FAKE_GIT)
    assert s.status == "failed" and s.pages_requested == 0   # unreadable robots.txt -> do not crawl
    run = market_db.execute("SELECT status, finished_at FROM scrape_runs WHERE run_id = ?", (s.run_id,)).fetchone()
    assert run["status"] == "failed" and run["finished_at"] is not None


def test_assessed_run_refused_from_uncommitted_code_and_inactive_shop_refused(market_db):
    fetcher, _ = make_fetcher(uzflora_routes())
    for kwargs in ({"purpose": "assessed", "git": ("1" * 40, True)}, {"git": FAKE_GIT}):
        codes = ["uzflora"] if "purpose" in kwargs else ["fiori"]
        try:
            collect(market_db, codes, fetcher=fetcher, **kwargs)
            raise AssertionError("expected CollectError")
        except CollectError:
            pass
    assert market_db.execute("SELECT COUNT(*) FROM scrape_runs").fetchone()[0] == 0


def test_every_uzflora_request_forces_uzs_currency(market_db):
    """Regression for the probe finding: without currency=UZS, foreign IPs get USD prices."""
    fetcher, site = make_fetcher(uzflora_routes())
    collect(market_db, ["uzflora"], fetcher=fetcher, git=FAKE_GIT)
    pages = [u for u in site.requests if "/shop/" in u]
    assert pages and all(u.endswith("?currency=UZS") for u in pages)
