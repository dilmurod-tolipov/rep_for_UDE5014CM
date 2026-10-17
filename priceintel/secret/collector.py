"""Collect Secret's current prices from its public Telegram channel into secret_shop.

One run reads the channel preview page by page (newest first) until posts are older than
``since_days``. Every post still visible gets a dated price observation, so a bouquet that stays
on sale is observed again in every run (fresh, dated observations, as the proposal requires)."""
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from priceintel import __version__
from priceintel.collect.http import AGENT_TOKEN, FetchAttempt, Fetcher, utc_now
from priceintel.collect.robots import RobotsRules, parse_robots
from priceintel.collect.runner import SUCCESS_THRESHOLD, CollectError
from priceintel.collect.validate import Rejection
from priceintel.db import transaction
from priceintel.gitinfo import git_state
from priceintel.secret.extract import clean_caption, extract_price, title_of
from priceintel.secret.telegram import parse_channel_page

MAX_PAGES = 30


@dataclass
class SecretRunSummary:
    run_id: int
    status: str = "running"
    pages_requested: int = 0
    pages_ok: int = 0
    prices_saved: int = 0
    posts_rejected: int = 0
    posts_too_old: int = 0
    errors: list[str] = field(default_factory=list)


def _log(conn, run_id, channel_id, attempts: list[FetchAttempt], parse_ok=None, items=None) -> int:
    fid = None
    for i, a in enumerate(attempts):
        final = i == len(attempts) - 1
        fid = conn.execute(
            "INSERT INTO source_fetches (run_id, channel_id, url, requested_at, attempt, http_status,"
            " elapsed_ms, bytes, content_sha256, parse_ok, items_found, error)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, channel_id, a.url, a.requested_at, a.attempt, a.status, a.elapsed_ms,
             len(a.body) if a.body is not None else None, a.sha256,
             parse_ok if final else None, items if final else None, a.error)).lastrowid
    return fid


def _robots(conn, run_id, channel, fetcher) -> RobotsRules:
    p = urlsplit(channel["preview_url"])
    attempts = fetcher.get(f"{p.scheme}://{p.netloc}/robots.txt", channel["crawl_delay_s"])
    with transaction(conn):
        _log(conn, run_id, channel["channel_id"], attempts)
    final = attempts[-1]
    if final.status == 200:
        return parse_robots(final.text, AGENT_TOKEN)
    if final.status in (404, 410):
        return RobotsRules.allow_everything()
    return RobotsRules.deny_everything()


def _reject(conn, run_id, fetch_id, post, rejection: Rejection, at: str) -> None:
    conn.execute(
        "INSERT INTO rejected_posts (run_id, fetch_id, post_url, rejected_at, rule, detail, raw_payload)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (run_id, fetch_id, post.post_url, at, rejection.rule, rejection.detail,
         json.dumps({"post_url": post.post_url, "published_at": post.published_at,
                     "text": clean_caption(post.text)}, ensure_ascii=False)))


def _save(conn, run_id, fetch_id, channel_id, post, price, raw, observed_at) -> bool:
    caption = clean_caption(post.text)
    product_id = conn.execute(
        "INSERT INTO products (channel_id, post_url, post_id, published_at, title, caption,"
        " first_seen_run_id, last_seen_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT (post_url) DO UPDATE SET last_seen_at = excluded.last_seen_at,"
        " title = excluded.title, caption = excluded.caption RETURNING product_id",
        (channel_id, post.post_url, post.post_id, post.published_at, title_of(caption, post.post_id),
         caption, run_id, observed_at)).fetchone()[0]
    cur = conn.execute(
        "INSERT INTO product_price_history (product_id, run_id, fetch_id, observed_at, price_uzs,"
        " raw_price_text, method, entered_by) VALUES (?, ?, ?, ?, ?, ?, 'telegram_collector', 'collector')"
        " ON CONFLICT (product_id, run_id) DO NOTHING",
        (product_id, run_id, fetch_id, observed_at, price, raw))
    return cur.rowcount == 1


def collect_secret(conn: sqlite3.Connection, channel_code: str = "secret_flowersuz",
                   since_days: int = 14, purpose: str = "dev", triggered_by: str = "manual",
                   fetcher: Fetcher | None = None, max_pages: int = MAX_PAGES,
                   git: tuple[str, bool] | None = None, now: datetime | None = None) -> SecretRunSummary:
    fetcher = fetcher or Fetcher()
    commit, dirty = git or git_state()
    if purpose == "assessed" and (dirty or commit == "unknown"):
        raise CollectError("assessed runs need committed, unmodified code: commit your changes first")
    channel = conn.execute("SELECT * FROM source_channels WHERE code = ? AND is_active = 1",
                           (channel_code,)).fetchone()
    if channel is None:
        raise CollectError(f"no active channel {channel_code!r}")
    cutoff = ((now or datetime.now(timezone.utc)) - timedelta(days=since_days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    run_id = conn.execute(
        "INSERT INTO collection_runs (purpose, triggered_by, started_at, git_commit, git_dirty,"
        " collector_version, since_days) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (purpose, triggered_by, utc_now(), commit, int(dirty), __version__, since_days)).lastrowid
    s = SecretRunSummary(run_id)
    fatal = None
    try:
        rules = _robots(conn, run_id, channel, fetcher)
        url, seen = channel["preview_url"], set()
        while url and url not in seen and s.pages_requested < max_pages:
            seen.add(url)
            p = urlsplit(url)
            if not rules.allowed(p.path + (f"?{p.query}" if p.query else "")):
                s.errors.append(f"robots.txt disallows {url}")
                break
            attempts = fetcher.get(url, channel["crawl_delay_s"])
            s.pages_requested += 1
            final = attempts[-1]
            posts, older, err = [], None, None
            if final.ok:
                try:
                    posts, older = parse_channel_page(final.text, url)
                    if not posts:
                        err = "no posts found on page (layout changed?)"
                except Exception as e:
                    err = f"parser error: {type(e).__name__}: {e}"
            ok = final.ok and err is None
            reached_cutoff = False
            with transaction(conn):
                fid = _log(conn, run_id, channel["channel_id"], attempts,
                           int(ok) if final.ok else None, len(posts) if final.ok else None)
                for post in posts:
                    if post.published_at < cutoff:
                        s.posts_too_old += 1
                        reached_cutoff = True
                        continue
                    r = extract_price(post.text)
                    if isinstance(r, Rejection):
                        _reject(conn, run_id, fid, post, r, final.requested_at)
                        s.posts_rejected += 1
                    elif _save(conn, run_id, fid, channel["channel_id"], post, r[0], r[1],
                               final.requested_at):
                        s.prices_saved += 1
            if ok:
                s.pages_ok += 1
                url = None if reached_cutoff else older
            else:
                s.errors.append(f"{url}: {err or final.error or f'HTTP {final.status}'}")
                url = None
    except Exception as e:
        fatal = f"{type(e).__name__}: {e}"
        s.errors.append(fatal)
    finally:
        if fatal or s.pages_requested == 0:
            s.status = "failed"
        elif s.pages_ok / s.pages_requested >= SUCCESS_THRESHOLD:
            s.status = "success"
        else:
            s.status = "partial" if s.pages_ok else "failed"
        conn.execute(
            "UPDATE collection_runs SET finished_at = ?, status = ?, pages_requested = ?, pages_ok = ?,"
            " prices_saved = ?, posts_rejected = ?, error_message = ? WHERE run_id = ?",
            (utc_now(), s.status, s.pages_requested, s.pages_ok, s.prices_saved, s.posts_rejected,
             "; ".join(s.errors)[:2000] or None, run_id))
    return s
