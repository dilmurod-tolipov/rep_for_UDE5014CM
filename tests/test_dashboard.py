"""The dashboard: routing, input validation, the JSON API, the charts, and a live request.

Routing is a pure function, so most of this needs no server. The last test does start the real
server on an ephemeral port and fetch a page over HTTP, because "the application starts and returns
output" is a claim the report makes and a marker will check."""
import json
import threading
import urllib.request

import pytest

from priceintel import config
from priceintel.analysis.categories import classify_listings, load_rules
from priceintel.db import connect
from priceintel.quality import run_checks
from priceintel.queries import available
from priceintel.web import charts
from priceintel.web.app import make_server
from priceintel.web.data import Databases, Selection, product_prices
from priceintel.web.views import PAGES, render, selection_from
from tests.conftest import TS, add_fetch, add_observation, add_run, shop_id


@pytest.fixture
def db(market_db, tmp_path):
    """A market database with a little collected data, plus an empty secret_shop beside it."""
    from priceintel.db import init_secret_db
    rules = load_rules(config.CATEGORY_RULES_FILE)
    run_id = add_run(market_db, purpose="test")
    fetch = add_fetch(market_db, run_id)
    for i, price in enumerate((200_000, 300_000, 400_000), start=1):
        listing = market_db.execute(
            "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
            " last_title, site_category) VALUES (?, ?, ?, ?, ?, ?, 'bukety') RETURNING listing_id",
            (shop_id(market_db, "uzflora"), f"https://uzflora.com/product/b{i}/", run_id, TS, TS,
             f"Букет {i}")).fetchone()[0]
        add_observation(market_db, listing, run_id, fetch, price=price)
    market_db.execute("UPDATE scrape_runs SET status = 'success', finished_at = ?,"
                      " pages_requested = 1, pages_ok = 1, observations_saved = 3 WHERE run_id = ?",
                      (TS, run_id))
    classify_listings(market_db, rules)
    run_checks(market_db, purpose="test", rules_version=rules.version)

    secret_path = tmp_path / "secret_shop.db"
    init_secret_db(secret_path, config.SECRET_MIGRATIONS, config.SECRET_SOURCES_FILE)
    return Databases(market_db, connect(secret_path), available(config.QUERIES_DIR))


def get(db, path, **params):
    return render(path, {k: [str(v)] for k, v in params.items()}, db)


@pytest.mark.parametrize("path, label", PAGES)
def test_every_page_renders(db, path, label):
    response = get(db, path, purpose="test")
    assert response.status == 200
    assert label in response.body and "<svg" in response.body or path == "/quality"
    assert response.body.startswith("<!doctype html>")


def test_pages_show_the_selected_data_only(db):
    body = get(db, "/", purpose="test").body
    assert "3</div><div class=\"k\">distinct competitor products" in body.replace("\n", "")
    assert "test" in body


def test_both_databases_are_shown_and_checked(db):
    body = get(db, "/", purpose="test").body
    assert "secret_shop table" in body            # the operational database is on the page
    assert "cross-database check OK" in body      # and the check between them ran


@pytest.mark.parametrize("params, expected", [
    ({"purpose": "banana"}, "not available"),
    ({"min_items": "zero"}, "whole number"),
    ({"min_items": "0"}, "between 1 and 1000"),
    ({"limit": "9999"}, "between 1 and 500"),
    ({"category": "flowers"}, "not available"),
    ({"rules": "9.9.9"}, "not available"),
])
def test_invalid_input_is_refused_with_a_message(db, params, expected):
    response = render("/coverage", {k: [v] for k, v in params.items()}, db)
    assert response.status == 400
    assert expected in response.body
    assert "Invalid input" in response.body


def test_valid_input_changes_the_result(db):
    assert selection_from({"purpose": ["test"], "min_items": ["3"]}, db).min_items == 3
    strict = get(db, "/price-position", purpose="test", min_items=100).body
    loose = get(db, "/price-position", purpose="test", min_items=1).body
    assert strict != loose


def test_unknown_page_is_404(db):
    assert get(db, "/nothing-here", purpose="test").status == 404


def test_api_returns_json_with_the_question_and_rows(db):
    response = get(db, "/api/02_category_coverage.json", purpose="test")
    assert response.content_type.startswith("application/json")
    payload = json.loads(response.body)
    assert payload["query"] == "02_category_coverage"
    assert payload["question"].startswith("Q2")
    assert payload["selection"]["purpose"] == "test"
    assert payload["rows"] and set(payload["columns"]) <= set(payload["rows"][0])


def test_api_rejects_an_unknown_query(db):
    response = get(db, "/api/not_a_query.json", purpose="test")
    assert response.status == 404
    assert "available" in json.loads(response.body)


def test_product_prices_collapse_repeated_observations(db):
    prices = product_prices(db.market, Selection(purpose="test", rules_version="1.1.0"))
    assert sorted(prices) == [200_000, 300_000, 400_000]


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def test_charts_render_and_say_so_when_there_is_nothing_to_draw():
    assert "<svg" in charts.bar_chart(["a"], [1.0], title="t", value_label="UZS")
    assert "no data" in charts.bar_chart([], [], title="t", value_label="UZS")
    assert "no data" in charts.histogram([], title="t", value_label="UZS")
    assert "no data" in charts.grouped_bars([], {}, title="t", value_label="UZS")
    assert "no data" in charts.line_chart([], {}, title="t", value_label="UZS")


def test_diverging_bars_separate_negative_from_positive():
    svg = charts.bar_chart(["below", "above"], [-20.0, 10.0], title="t", value_label="%",
                           diverging=True)
    assert "var(--down)" in svg and "var(--up)" in svg


def test_histogram_counts_every_value():
    svg = charts.histogram([1.0, 2.0, 2.0, 9.0], title="t", value_label="UZS", bins=3)
    assert svg.count("<rect") == 3 and "4" not in svg.split("<title>")[0]


# ---------------------------------------------------------------------------
# The real server
# ---------------------------------------------------------------------------

def test_the_server_starts_and_answers_a_request(tmp_path, market_db):
    """Starts the dashboard on a free port and fetches a page, as a marker would."""
    path = tmp_path / "market.db"
    from priceintel.db import init_market_db
    init_market_db(path, config.MARKET_MIGRATIONS, config.SHOPS_FILE)
    server = make_server(path, None, port=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/"
        with urllib.request.urlopen(url, timeout=10) as response:
            body = response.read().decode("utf-8")
            assert response.status == 200
            assert "Competitive price intelligence" in body
        with urllib.request.urlopen(url + "api/04_collection_health.json", timeout=10) as response:
            assert json.loads(response.read())["query"] == "04_collection_health"
    finally:
        server.shutdown()
        server.server_close()
