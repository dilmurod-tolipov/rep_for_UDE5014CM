"""The dashboard's pages: HTML, the JSON API, and the validation of user input.

Routing is a pure function (``render``) that takes a path and the query parameters and returns a
``Response``. No sockets, no globals: the HTTP server in ``app.py`` only turns requests into those
two arguments, which means every page and every validation rule is unit-testable
(``tests/test_dashboard.py``).

Input handling follows one rule: **a value that is not understood is refused with a message, never
silently replaced by a default.** `?purpose=secret` returns 400 and says which purposes exist, rather
than quietly showing assessed data. The only values accepted are the ones the database actually
offers, which also keeps user input away from SQL - purposes, rules versions and categories are
checked against lists read from the database, and every query is parameterised.
"""
from dataclasses import dataclass
from html import escape

from priceintel.web import charts
from priceintel.web.data import (
    Databases,
    Selection,
    categories,
    daily_collection,
    headline,
    integrity,
    median_price_by_group,
    product_prices,
    purposes,
    quality_results,
    rules_versions,
    secret_shop_state,
)

PAGES = (("/", "Overview"), ("/price-position", "Price position"), ("/coverage", "Coverage"),
         ("/changes", "Price changes"), ("/market", "Market and discounts"),
         ("/quality", "Data quality"))

STYLE = """
:root {
  --bg: #fbfaf8; --panel: #ffffff; --ink: #1c1b19; --muted: #6b6762; --line: #e6e1db;
  --c1: #7d4f9c; --c2: #3f7f8f; --c3: #b07a3c; --c4: #8c6f5e; --c5: #5a7a4f;
  --up: #a33f5b; --down: #3f7f8f; --pass: #3f7f5b; --warn: #b07a3c; --fail: #a33f5b;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #17161a; --panel: #1f1e23; --ink: #ece9e4; --muted: #a09a93; --line: #322f36;
    --c1: #b48ad0; --c2: #74b4c2; --c3: #d6a765; --c4: #bfa08c; --c5: #93b885;
    --up: #e0859a; --down: #74b4c2; --pass: #7fc49a; --warn: #d6a765; --fail: #e0859a;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
       font: 15px/1.5 "Segoe UI", system-ui, -apple-system, sans-serif; }
header { border-bottom: 1px solid var(--line); background: var(--panel); }
.wrap { max-width: 1040px; margin: 0 auto; padding: 0 16px; }
h1 { font-size: 19px; margin: 14px 0 4px; }
h2 { font-size: 16px; margin: 26px 0 8px; }
nav a { display: inline-block; padding: 8px 12px 10px; color: var(--muted);
        text-decoration: none; border-bottom: 2px solid transparent; }
nav a.on, nav a:hover { color: var(--ink); border-bottom-color: var(--c1); }
.sub { color: var(--muted); font-size: 13px; margin: 0 0 12px; }
form.controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-end;
                background: var(--panel); border: 1px solid var(--line); border-radius: 8px;
                padding: 12px; margin: 16px 0; }
label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 3px; }
select, input[type=number] { padding: 6px 8px; border: 1px solid var(--line); border-radius: 6px;
                             background: var(--bg); color: var(--ink); font: inherit; }
button { padding: 7px 14px; border: 0; border-radius: 6px; background: var(--c1); color: #fff;
         font: inherit; cursor: pointer; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 12px; }
.card .n { font-size: 24px; font-weight: 600; }
.card .k { font-size: 12px; color: var(--muted); }
.panel { background: var(--panel); border: 1px solid var(--line); border-radius: 8px;
         padding: 14px; margin: 12px 0; overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; padding: 6px 10px 6px 0; border-bottom: 1px solid var(--line);
         white-space: nowrap; }
th { color: var(--muted); font-weight: 600; }
td.num, th.num { text-align: right; }
.chart { width: 100%; height: auto; }
.chart-title { font-size: 13px; fill: var(--ink); font-weight: 600; }
.tick { font-size: 11px; fill: var(--muted); }
.axis-label { font-size: 11px; fill: var(--muted); }
.axis { stroke: var(--line); stroke-width: 1; }
.grid { stroke: var(--line); stroke-width: 1; stroke-dasharray: 2 3; }
.muted-text { font-size: 13px; fill: var(--muted); }
.pill { font-size: 11px; padding: 2px 8px; border-radius: 10px; color: #fff; }
.pass { background: var(--pass); } .warn { background: var(--warn); } .fail { background: var(--fail); }
.note { color: var(--muted); font-size: 13px; }
.error { border-left: 3px solid var(--fail); padding-left: 12px; }
footer { color: var(--muted); font-size: 12px; margin: 30px 0 40px; }
@media (max-width: 620px) { nav a { padding: 8px 8px 10px; } .card .n { font-size: 20px; } }
"""


@dataclass
class Response:
    body: str
    status: int = 200
    content_type: str = "text/html; charset=utf-8"


class BadInput(ValueError):
    """User input that is not understood; answered with 400 and an explanation."""


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def _int(params: dict, name: str, default: int, low: int, high: int) -> int:
    raw = params.get(name, [""])[0] or ""
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise BadInput(f"{name} must be a whole number, not {raw!r}")
    if not low <= value <= high:
        raise BadInput(f"{name} must be between {low} and {high}, not {value}")
    return value


def _choice(params: dict, name: str, options: list[str], default: str) -> str:
    raw = params.get(name, [""])[0] or ""
    if not raw:
        return default
    if raw not in options:
        raise BadInput(f"{name}={raw!r} is not available; choose one of: {', '.join(options)}")
    return raw


def selection_from(params: dict, db: Databases) -> Selection:
    available_purposes = purposes(db.market)
    versions = rules_versions(db.market) or [""]
    purpose = _choice(params, "purpose", available_purposes,
                      "assessed" if "assessed" in available_purposes else available_purposes[0])
    rules_version = _choice(params, "rules", versions, versions[0])
    category = _choice(params, "category", [""] + categories(db.market, rules_version), "")
    return Selection(purpose=purpose, rules_version=rules_version,
                     min_items=_int(params, "min_items", 10, 1, 1000),
                     category=category,
                     limit=_int(params, "limit", 20, 1, 500))


# ---------------------------------------------------------------------------
# HTML building blocks
# ---------------------------------------------------------------------------

def _controls(path: str, db: Databases, sel: Selection, *, with_category=False,
              with_min_items=False, with_limit=False) -> str:
    def options(values, chosen, blank=None):
        out = [f'<option value=""{" selected" if chosen == "" else ""}>{escape(blank)}</option>'] \
            if blank else []
        out += [f'<option value="{escape(v)}"{" selected" if v == chosen else ""}>{escape(v)}</option>'
                for v in values]
        return "".join(out)

    bits = [f'<form class="controls" method="get" action="{escape(path)}">',
            '<div><label for="purpose">Data</label>'
            f'<select id="purpose" name="purpose">{options(purposes(db.market), sel.purpose)}'
            '</select></div>',
            '<div><label for="rules">Category rules</label>'
            f'<select id="rules" name="rules">{options(rules_versions(db.market), sel.rules_version)}'
            '</select></div>']
    if with_category:
        bits.append('<div><label for="category">Category</label><select id="category" '
                    f'name="category">{options(categories(db.market, sel.rules_version), sel.category, "all categories")}'
                    '</select></div>')
    if with_min_items:
        bits.append('<div><label for="min_items">Minimum items to display</label>'
                    f'<input id="min_items" type="number" name="min_items" min="1" max="1000" '
                    f'value="{sel.min_items}"></div>')
    if with_limit:
        bits.append('<div><label for="limit">Rows</label>'
                    f'<input id="limit" type="number" name="limit" min="1" max="500" '
                    f'value="{sel.limit}"></div>')
    bits.append('<button type="submit">Update</button></form>')
    return "".join(bits)


def _table(columns: list[str], rows: list[tuple], *, highlight: str = "") -> str:
    if not rows:
        return '<p class="note">No rows for this selection.</p>'
    numeric = [all(isinstance(r[i], (int, float)) or r[i] is None for r in rows)
               for i in range(len(columns))]
    head = "".join(f'<th class="{"num" if numeric[i] else ""}">{escape(c.replace("_", " "))}</th>'
                   for i, c in enumerate(columns))
    body = []
    for row in rows:
        cells = []
        for i, value in enumerate(row):
            text = "" if value is None else (f"{value:,}" if isinstance(value, int) else str(value))
            if highlight and columns[i] == highlight:
                klass = {"displayed": "pass", "pass": "pass", "warn": "warn",
                         "fail": "fail"}.get(str(value), "warn")
                text = f'<span class="pill {klass}">{escape(str(value))}</span>'
            else:
                text = escape(text)
            cells.append(f'<td class="{"num" if numeric[i] else ""}">{text}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (f'<div class="panel"><table><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def _spread(values: list[float]) -> str:
    """Minimum, quartiles, median and maximum under a distribution chart.

    A histogram of one skewed category can look like a single bar, which says little; the numbers
    below it say how wide the range really is. On the development data this is how the per-stem rose
    listings (about 18,000 UZS) became visible beside whole bouquets costing millions."""
    if not values:
        return ""
    ordered = sorted(values)
    def at(fraction):
        return ordered[min(int(fraction * (len(ordered) - 1)), len(ordered) - 1)]
    stats = (("min", ordered[0]), ("25%", at(0.25)), ("median", at(0.5)), ("75%", at(0.75)),
             ("max", ordered[-1]))
    cells = " &nbsp;·&nbsp; ".join(f"{label} <strong>{value:,.0f}</strong>" for label, value in stats)
    return f'<p class="note">UZS: {cells}</p>'


def _page(path: str, title: str, subtitle: str, body: str, *, status: int = 200) -> Response:
    nav = "".join(f'<a href="{escape(href)}"{" class=\"on\"" if href == path else ""}>'
                  f'{escape(label)}</a>' for href, label in PAGES)
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{escape(title)} - Secret price intelligence</title>'
            f'<style>{STYLE}</style></head><body>'
            f'<header><div class="wrap"><h1>Competitive price intelligence - Secret, Tashkent</h1>'
            f'<nav>{nav}</nav></div></header><main class="wrap">'
            f'<h2>{escape(title)}</h2><p class="sub">{subtitle}</p>{body}'
            f'<footer>Data collected by this project\'s own scrapers. Secret\'s own offers are '
            f'reference data, imported from the owner\'s export, and are never used in any model. '
            f'Figures describe the sampled shops and window only.</footer>'
            f'</main></body></html>')
    return Response(html, status)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def page_overview(db: Databases, sel: Selection) -> Response:
    h = headline(db.market, sel)
    cards = "".join(
        f'<div class="card"><div class="n">{value:,}</div><div class="k">{escape(label)}</div></div>'
        for label, value in (("distinct competitor products", h["products"]),
                             ("price observations", h["observations"]),
                             ("collection runs", h["runs"]),
                             ("operator groups", h["groups"]),
                             ("Secret reference offers", h["secret_offers"]),
                             ("records quarantined", h["quarantined"])))
    labels, series = daily_collection(db.market, sel)
    cats, medians = median_price_by_group(db.market, sel)
    state = secret_shop_state(db)
    problems = integrity(db)
    shop_rows = "".join(f"<tr><td>{escape(t)}</td><td class='num'>{n:,}</td></tr>"
                        for t, n in state.get("counts", {}).items())
    body = (f'{_controls("/", db, sel)}'
            f'<div class="cards">{cards}</div>'
            f'<p class="note">Newest observation: {escape(str(h["newest"] or "none yet"))}. '
            f'Showing <strong>{escape(sel.purpose)}</strong> data under category rules '
            f'<strong>{escape(sel.rules_version)}</strong>.</p>'
            # Two charts, not one: observations and a percentage share no axis, and drawing them
            # together would flatten the success rate against a much larger count.
            f'<div class="panel">{charts.line_chart(labels, {"observations saved": series["observations saved"]}, title="Observations saved per day", value_label="observations")}</div>'
            f'<div class="panel">{charts.line_chart(labels, {"page success %": series["page success %"]}, title="Pages fetched and parsed per day", value_label="% of requested pages")}</div>'
            f'<div class="panel">{charts.grouped_bars(cats, medians, title="Median regular price by category and operator group", value_label="UZS")}</div>'
            f'<h2>Both databases</h2>'
            f'<div class="panel"><p class="note">market_intel holds the collected market data; '
            f'secret_shop holds the shop\'s own operational tables. The cross-database check below '
            f'runs on every page load, because SQLite cannot enforce a foreign key between two '
            f'files.</p>'
            + (f'<table><thead><tr><th>secret_shop table</th><th class="num">rows</th></tr></thead>'
               f'<tbody>{shop_rows}</tbody></table>' if shop_rows else
               '<p class="note">secret_shop database not found.</p>')
            + ('<p class="note"><span class="pill pass">cross-database check OK</span></p>'
               if not problems else
               '<p class="error">' + "<br>".join(escape(p) for p in problems) + '</p>')
            + '</div>')
    return _page("/", "Overview", "Is the system collecting, and what does the market look like?",
                 body)


def page_price_position(db: Databases, sel: Selection) -> Response:
    question, columns, rows = db.query("01_price_position_by_category", sel)
    shown = [r for r in rows if r[columns.index("evidence")] == "displayed"]
    chart = charts.bar_chart(
        [f"{r[columns.index('category')]} / {r[columns.index('operator_group')]}" for r in shown],
        [float(r[columns.index("difference_pct")]) for r in shown],
        title="Secret's median price against each competitor group",
        value_label="% difference", diverging=True)
    body = (f'{_controls("/price-position", db, sel, with_min_items=True)}'
            f'<p class="note">{escape(question)} A row is only drawn when both sides have at least '
            f'{sel.min_items} items; the table shows every pair with its counts, so an absent bar is '
            f'visible as insufficient evidence rather than missing.</p>'
            f'<div class="panel">{chart}</div>'
            f'{_table(columns, rows, highlight="evidence")}'
            f'<p class="note">Positive means Secret advertises higher. Differences may reflect '
            f'bouquet size, composition or presentation, so they do not show that equivalent '
            f'bouquets are over- or under-priced.</p>')
    return _page("/price-position", "Price position",
                 "100 × (Secret median ÷ competitor median − 1), per category and operator group",
                 body)


def page_coverage(db: Databases, sel: Selection) -> Response:
    question, columns, rows = db.query("02_category_coverage", sel)
    prices = product_prices(db.market, sel)
    title = (f"Price distribution - {sel.category}" if sel.category
             else "Price distribution - all categories")
    body = (f'{_controls("/coverage", db, sel, with_category=True, with_min_items=True)}'
            f'<p class="note">{escape(question)}</p>'
            f'{_table(columns, rows, highlight="verdict")}'
            f'<div class="panel">{charts.histogram(prices, title=title, value_label="regular price, UZS")}'
            f'{_spread(prices)}</div>'
            f'<p class="note">{len(prices):,} distinct products in this selection, each counted once '
            f'at its median regular price. Listings showing only a "from" price are excluded. The '
            f'axis is linear and the data is not trimmed, so a single-stem listing priced beside '
            f'whole bouquets is visible as the long tail it is rather than hidden by a log scale.</p>')
    return _page("/coverage", "Coverage",
                 "What is there enough evidence to compare, and how are prices spread?", body)


def page_changes(db: Databases, sel: Selection) -> Response:
    question, columns, rows = db.query("03_price_changes", sel)
    chart = charts.bar_chart(
        [str(r[columns.index("product")])[:28] for r in rows[:12]],
        [float(r[columns.index("change_pct")]) for r in rows[:12]],
        title="Largest price moves", value_label="% change", diverging=True)
    body = (f'{_controls("/changes", db, sel, with_limit=True)}'
            f'<p class="note">{escape(question)} Each row compares a listing\'s newest price with '
            f'the previous observation of the same listing, so nothing here is a new product.</p>'
            f'<div class="panel">{chart}</div>{_table(columns, rows)}')
    return _page("/changes", "Price changes", "What moved, and by how much?", body)


def page_market(db: Databases, sel: Selection) -> Response:
    question, columns, rows = db.query("05_discounts_in_market", sel)
    chart = charts.bar_chart(
        [f"{r[columns.index('operator_group')]} / {r[columns.index('category')]}" for r in rows[:12]],
        [float(r[columns.index("on_sale_pct")] or 0) for r in rows[:12]],
        title="Share of products on sale", value_label="% of products")
    body = (f'{_controls("/market", db, sel)}'
            f'<p class="note">{escape(question)} Only the latest observation of each product is '
            f'used. Conditional promotions and delivery terms are recorded as flags, not folded into '
            f'a price.</p>'
            f'<div class="panel">{chart}</div>{_table(columns, rows)}')
    return _page("/market", "Market and discounts", "Who is discounting, and how deeply?", body)


def page_quality(db: Databases, sel: Selection) -> Response:
    results = quality_results(db.market, sel)
    question, columns, rows = db.query("04_collection_health", sel)
    if results:
        checks = "".join(
            f'<tr><td><span class="pill {escape(r["status"])}">{escape(r["status"])}</span></td>'
            f'<td>{escape(r["check_name"].replace("_", " "))}</td>'
            f'<td class="num">{r["measured"]:,.2f}</td>'
            f'<td class="num">{"" if r["threshold"] is None else f"{r['threshold']:,.2f}"}</td>'
            f'<td>{escape(r["unit"])}</td><td>{escape(r["detail"] or "")}</td></tr>'
            for r in results)
        checks_html = (f'<div class="panel"><table><thead><tr><th></th><th>check</th>'
                       f'<th class="num">measured</th><th class="num">threshold</th><th>unit</th>'
                       f'<th>detail</th></tr></thead><tbody>{checks}</tbody></table>'
                       f'<p class="note">Recorded {escape(results[0]["run_at"])}; re-run with '
                       f'<code>python -m priceintel quality</code>.</p></div>')
    else:
        checks_html = ('<p class="note">No checks recorded for this data yet. Run '
                       '<code>python -m priceintel quality</code>.</p>')
    body = (f'{_controls("/quality", db, sel)}{checks_html}'
            f'<h2>Collection health</h2><p class="note">{escape(question)}</p>'
            f'{_table(columns, rows)}')
    return _page("/quality", "Data quality",
                 "Is the dataset fit for the planned analysis, and is collection healthy?", body)


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

HANDLERS = {"/": page_overview, "/price-position": page_price_position, "/coverage": page_coverage,
            "/changes": page_changes, "/market": page_market, "/quality": page_quality}


def render(path: str, params: dict, db: Databases) -> Response:
    """Turn a path and query parameters into a response. The HTTP server does nothing else."""
    import json

    try:
        sel = selection_from(params, db)
    except BadInput as e:
        return _page(path, "Invalid input", "The request was not understood",
                     f'<p class="error">{escape(str(e))}</p>'
                     f'<p class="note"><a href="/">Back to the overview</a></p>', status=400)

    if path.startswith("/api/"):
        name = path[len("/api/"):].removesuffix(".json")
        matches = [k for k in db.queries if k == name or k.endswith(name)]
        if not matches:
            return Response(json.dumps({"error": f"unknown query {name!r}",
                                        "available": sorted(k for k in db.queries
                                                            if k[0].isdigit())}, indent=2),
                            404, "application/json; charset=utf-8")
        question, columns, rows = db.query(matches[0], sel)
        payload = {"query": matches[0], "question": question, "selection": sel.as_params(),
                   "columns": columns, "rows": [dict(zip(columns, r)) for r in rows]}
        return Response(json.dumps(payload, indent=2, ensure_ascii=False), 200,
                        "application/json; charset=utf-8")

    handler = HANDLERS.get(path)
    if handler is None:
        return _page(path, "Not found", "No such page",
                     '<p class="note"><a href="/">Back to the overview</a></p>', status=404)
    return handler(db, sel)
