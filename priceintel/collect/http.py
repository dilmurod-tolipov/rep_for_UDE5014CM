"""Polite HTTP fetching: identified user agent, per-host delay, bounded retries.

Every attempt is returned as a ``FetchAttempt`` so the caller can log each one in
``fetch_log`` (failed attempts are evidence too)."""
import hashlib
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

import requests

from priceintel import __version__

USER_AGENT = (f"Mozilla/5.0 (compatible; SecretPriceResearchBot/{__version__}; "
              "student project UDE5014CM; +https://github.com/dilmurod-tolipov/rep_for_UDE5014CM)")
AGENT_TOKEN = "SecretPriceResearchBot"
RETRY_STATUSES = {429, 500, 502, 503, 504}


@dataclass
class FetchAttempt:
    url: str
    requested_at: str
    attempt: int
    status: int | None
    body: bytes | None
    elapsed_ms: int
    error: str | None

    @property
    def ok(self) -> bool:
        return self.status == 200 and self.body is not None

    @property
    def sha256(self) -> str | None:
        return hashlib.sha256(self.body).hexdigest() if self.body is not None else None

    @property
    def text(self) -> str:
        return (self.body or b"").decode("utf-8", "replace")


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Fetcher:
    def __init__(self, session: requests.Session | None = None, max_attempts: int = 3,
                 backoff_s: tuple[float, ...] = (10, 30), timeout_s: float = 30,
                 sleep=time.sleep, clock=time.monotonic, now=utc_now):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT,
                                     "Accept-Language": "ru,uz;q=0.8,en;q=0.5"})
        self.max_attempts = max_attempts
        self.backoff_s = backoff_s
        self.timeout_s = timeout_s
        self.sleep, self.clock, self.now = sleep, clock, now
        self._last_request: dict[str, float] = {}

    def _wait_for_host(self, host: str, min_delay_s: float) -> None:
        last = self._last_request.get(host)
        if last is not None:
            remaining = min_delay_s - (self.clock() - last)
            if remaining > 0:
                self.sleep(remaining)
        self._last_request[host] = self.clock()

    def get(self, url: str, min_delay_s: float) -> list[FetchAttempt]:
        """Fetch ``url``; retry network errors, 429 and 5xx. Returns all attempts, last one final."""
        host = urlsplit(url).hostname or ""
        attempts: list[FetchAttempt] = []
        for n in range(1, self.max_attempts + 1):
            if n > 1:
                self.sleep(self.backoff_s[min(n - 2, len(self.backoff_s) - 1)])
            self._wait_for_host(host, min_delay_s)
            requested_at, t0 = self.now(), self.clock()
            try:
                resp = self.session.get(url, timeout=self.timeout_s, allow_redirects=True)
                a = FetchAttempt(url, requested_at, n, resp.status_code, resp.content,
                                 int((self.clock() - t0) * 1000), None)
            except requests.RequestException as e:
                a = FetchAttempt(url, requested_at, n, None, None,
                                 int((self.clock() - t0) * 1000), f"{type(e).__name__}: {e}"[:500])
            attempts.append(a)
            if a.status is not None and a.status not in RETRY_STATUSES:
                break
        return attempts
