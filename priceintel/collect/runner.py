"""One collection run: robots check -> fetch pages -> parse -> validate -> persist with provenance.

Run outcome (approved definition): a run succeeds when at least 80% of requested catalogue
pages returned HTTP 200 and parsed (>= 1 product). Some pages OK = 'partial'; none = 'failed'.
"""
import json
import platform
import sqlite3
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from priceintel import __version__
from priceintel.collect.http import AGENT_TOKEN, FetchAttempt, Fetcher, utc_now
from priceintel.collect.parsers import get_parser
from priceintel.collect.robots import RobotsRules, parse_robots
from priceintel.collect.validate import Rejection, validate
from priceintel.db import transaction
from priceintel.gitinfo import git_state

SUCCESS_THRESHOLD = 0.8
MAX_PAGES_PER_SHOP = 60


class CollectError(RuntimeError):
    pass


@dataclass
class RunSummary:
    run_id: int
    status: str = "running"
    pages_requested: int = 0
    pages_ok: int = 0
    observations_saved: int = 0
    duplicates_skipped: int = 0
    records_rejected: int = 0
    robots_skipped: int = 0
    errors: list[str] = field(default_factory=list)


def _path_and_query(url: str) -> str:
    p = urlsplit(url)
    return (p.path or "/") + (f"?{p.query}" if p.query else "")


def _log_attempts(conn, run_id, shop_id, attempts: list[FetchAttempt], parse_ok=None,
                  items_found=None) -> int:
    """Insert every attempt into fetch_log; parse results go on the final attempt. Returns its id."""
    fetch_id = None
    for i, a in enumerate(attempts):
        final = i == len(attempts) - 1
        fetch_id = conn.execute(
            "INSERT INTO fetch_log (run_id, shop_id, url, requested_at, attempt, robots_allowed,"
            " http_status, elapsed_ms, bytes, content_sha256, parse_ok, items_found, error)"
            " VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, shop_id, a.url, a.requested_at, a.attempt, a.status, a.elapsed_ms,
             len(a.body) if a.body is not None else None, a.sha256,
             parse_ok if final else None, items_found if final else None, a.error),
        ).lastrowid
    return fetch_id


def _log_robots_refusal(conn, run_id, shop_id, url, now) -> None:
    conn.execute(
        "INSERT INTO fetch_log (run_id, shop_id, url, requested_at, robots_allowed, error)"
        " VALUES (?, ?, ?, ?, 0, 'skipped: disallowed by robots.txt')",
        (run_id, shop_id, url, now()),
    )


def _load_robots(conn, run_id, shop, fetcher: Fetcher) -> RobotsRules:
    url = shop["base_url"].rstrip("/") + "/robots.txt"
    attempts = fetcher.get(url, shop["crawl_delay_s"])
    final = attempts[-1]
    with transaction(conn):
        _log_attempts(conn, run_id, shop["shop_id"], attempts)
    if final.status == 200:
        return parse_robots(final.text, AGENT_TOKEN)
    if final.status in (404, 410):
        return RobotsRules.allow_everything()
    return RobotsRules.deny_everything()  # cannot read robots.txt -> do not crawl


def _store_item(conn, run_id, fetch_id, shop_id, item, observed_at) -> bool:
    """Upsert the listing and add one observation. Returns False if already seen in this run."""
    listing_id = conn.execute(
        "INSERT INTO listings (shop_id, url, external_id, site_category, first_seen_run_id,"
        " first_seen_at, last_seen_at, last_title) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT (shop_id, url) DO UPDATE SET last_seen_at = excluded.last_seen_at,"
        " last_title = excluded.last_title,"
        " external_id = COALESCE(excluded.external_id, listings.external_id),"
        " site_category = COALESCE(excluded.site_category, listings.site_category)"
        " RETURNING listing_id",
        (shop_id, item.url, item.external_id, item.site_category, run_id, observed_at,
         observed_at, item.title),
    ).fetchone()[0]
    cur = conn.execute(
        "INSERT INTO price_observations (listing_id, run_id, fetch_id, observed_at, source_type,"
        " title, price_uzs, old_price_uzs, is_from_price, availability, raw_price_text)"
        " VALUES (?, ?, ?, ?, 'scrape', ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT (listing_id, run_id) DO NOTHING",
        (listing_id, run_id, fetch_id, observed_at, item.title, item.price_uzs, item.old_price_uzs,
         int(item.is_from_price), item.availability, item.raw_price_text),
    )
    return cur.rowcount == 1


def _with_query(url: str, query: str | None) -> str:
    """Append a parser's fixed query (e.g. currency=UZS) if the URL does not already carry it."""
    if not query or query in urlsplit(url).query:
        return url
    return url + ("&" if urlsplit(url).query else "?") + query


def _collect_shop(conn, run_id, shop, fetcher: Fetcher, summary: RunSummary, max_pages: int) -> None:
    parser = get_parser(shop["code"])
    query = getattr(parser, "QUERY", None)
    rules = _load_robots(conn, run_id, shop, fetcher)
    delay = max(shop["crawl_delay_s"], rules.crawl_delay or 0)
    shop_host = urlsplit(shop["base_url"]).hostname
    queue = [_with_query(shop["base_url"].rstrip("/") + p, query) for p in parser.START_PATHS]
    seen: set[str] = set()
    pages = 0
    while queue and pages < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        if urlsplit(url).hostname != shop_host:
            summary.errors.append(f"{shop['code']}: refused off-site link {url}")
            continue
        if not rules.allowed(_path_and_query(url)):
            with transaction(conn):
                _log_robots_refusal(conn, run_id, shop["shop_id"], url, fetcher.now)
            summary.robots_skipped += 1
            continue
        attempts = fetcher.get(url, delay)
        pages += 1
        summary.pages_requested += 1
        final = attempts[-1]
        result, parse_error = None, None
        if final.ok:
            try:
                result = parser.parse(final.text, url)
                if not result.items and not result.extra_urls:
                    parse_error = "no products found on page (layout changed?)"
            except Exception as e:  # a parser bug must not lose the fetch evidence
                parse_error = f"parser error: {type(e).__name__}: {e}"
        parse_ok = int(result is not None and parse_error is None) if final.ok else None
        with transaction(conn):
            fetch_id = _log_attempts(conn, run_id, shop["shop_id"], attempts, parse_ok,
                                     len(result.items) if result else None)
            if parse_ok:
                for raw in result.items:
                    checked = validate(raw, shop_host)
                    if isinstance(checked, Rejection):
                        conn.execute(
                            "INSERT INTO rejected_records (run_id, fetch_id, shop_id, rejected_at,"
                            " rule, detail, raw_payload) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (run_id, fetch_id, shop["shop_id"], final.requested_at, checked.rule,
                             checked.detail, json.dumps(raw.__dict__, ensure_ascii=False)),
                        )
                        summary.records_rejected += 1
                    elif _store_item(conn, run_id, fetch_id, shop["shop_id"], checked,
                                     final.requested_at):
                        summary.observations_saved += 1
                    else:
                        summary.duplicates_skipped += 1
        if parse_ok:
            summary.pages_ok += 1
            if result.next_url:
                queue.append(_with_query(result.next_url, query))
            # Pages a sitemap or index points at (kamilas lists its products that way).
            queue.extend(_with_query(u, query) for u in result.extra_urls)
        else:
            reason = parse_error or final.error or f"HTTP {final.status}"
            summary.errors.append(f"{shop['code']}: {url}: {reason}")


def collect(conn: sqlite3.Connection, shop_codes: list[str], purpose: str = "dev",
            triggered_by: str = "manual", fetcher: Fetcher | None = None,
            max_pages: int = MAX_PAGES_PER_SHOP, git: tuple[str, bool] | None = None) -> RunSummary:
    fetcher = fetcher or Fetcher()
    commit, dirty = git or git_state()
    if purpose == "assessed" and (dirty or commit == "unknown"):
        raise CollectError("assessed runs need committed, unmodified code: commit your changes first")

    placeholders = ",".join("?" * len(shop_codes))
    shops = conn.execute(
        f"SELECT * FROM shops WHERE code IN ({placeholders}) AND is_active = 1 AND is_own_shop = 0",
        shop_codes).fetchall()
    missing = set(shop_codes) - {s["code"] for s in shops}
    if missing:
        raise CollectError(f"not an active competitor shop: {', '.join(sorted(missing))}")

    run_id = conn.execute(
        "INSERT INTO scrape_runs (kind, purpose, triggered_by, started_at, git_commit, git_dirty,"
        " scraper_version, runner_host) VALUES ('competitor_scrape', ?, ?, ?, ?, ?, ?, ?)",
        (purpose, triggered_by, utc_now(), commit, int(dirty), __version__, platform.node() or "unknown"),
    ).lastrowid
    summary = RunSummary(run_id)
    fatal = None
    try:
        for shop in shops:
            _collect_shop(conn, run_id, shop, fetcher, summary, max_pages)
    except Exception as e:
        fatal = f"{type(e).__name__}: {e}"
        summary.errors.append(fatal)
    finally:
        if fatal or summary.pages_requested == 0:
            summary.status = "failed"
        elif summary.pages_ok / summary.pages_requested >= SUCCESS_THRESHOLD:
            summary.status = "success"
        elif summary.pages_ok > 0:
            summary.status = "partial"
        else:
            summary.status = "failed"
        conn.execute(
            "UPDATE scrape_runs SET finished_at = ?, status = ?, pages_requested = ?, pages_ok = ?,"
            " observations_saved = ?, records_rejected = ?, error_message = ? WHERE run_id = ?",
            (utc_now(), summary.status, summary.pages_requested, summary.pages_ok,
             summary.observations_saved, summary.records_rejected,
             "; ".join(summary.errors)[:2000] or None, run_id),
        )
    return summary
