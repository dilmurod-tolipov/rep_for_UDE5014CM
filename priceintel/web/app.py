"""The HTTP server: turns requests into ``views.render(path, params, db)`` and nothing more.

Built on the standard library's ``ThreadingHTTPServer`` so the project needs no web framework and a
marker can start the dashboard with nothing installed beyond the pinned dependencies.

Deliberate limits, since this is a local analysis tool and not a public service:

* it binds to 127.0.0.1 by default, so the dashboard is not exposed to the network;
* it answers GET and HEAD only - the dashboard never writes to the databases;
* each thread opens its own SQLite connections, because a connection must not be shared between
  threads; connections are read-only in effect (nothing here issues a write);
* an unexpected error returns a 500 page with the exception type, and the traceback goes to the
  console, so a failure is visible instead of silent.
"""
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from priceintel.web.data import Databases
from priceintel.web.views import render


class Handler(BaseHTTPRequestHandler):
    server_version = "priceintel-dashboard"
    market_path: Path
    secret_path: Path | None
    _local = threading.local()

    def databases(self) -> Databases:
        """One set of connections per thread (SQLite objects are not thread-safe)."""
        db = getattr(self._local, "db", None)
        if db is None:
            db = Databases.open(self.market_path, self.secret_path)
            self._local.db = db
        return db

    def do_GET(self):          # noqa: N802 - name fixed by BaseHTTPRequestHandler
        url = urlsplit(self.path)
        try:
            response = render(url.path, parse_qs(url.query), self.databases())
            body = response.body.encode("utf-8")
            status, content_type = response.status, response.content_type
        except Exception as e:                      # a bug must not take the server down
            traceback.print_exc()
            body = (f"<!doctype html><title>Server error</title><h1>500 - server error</h1>"
                    f"<p>{type(e).__name__}: {e}</p>").encode("utf-8")
            status, content_type = 500, "text/html; charset=utf-8"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):         # noqa: N802
        self.do_GET()

    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} {fmt % args}")


def make_server(market_path, secret_path=None, host: str = "127.0.0.1", port: int = 8000):
    """A server ready to ``serve_forever()``. Port 0 asks the OS for a free port (used by tests)."""
    handler = type("BoundHandler", (Handler,),
                   {"market_path": Path(market_path),
                    "secret_path": Path(secret_path) if secret_path else None})
    return ThreadingHTTPServer((host, port), handler)


def serve(market_path, secret_path=None, host: str = "127.0.0.1", port: int = 8000) -> int:
    server = make_server(market_path, secret_path, host, port)
    shown = f"http://{host}:{server.server_address[1]}/"
    print(f"dashboard on {shown}  (market: {market_path}, shop: {secret_path or 'not found'})")
    print("pages: /  /price-position  /coverage  /changes  /market  /quality")
    print("API:   /api/01_price_position_by_category.json  (any query name)")
    print("stop with Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
    return 0
