"""Exploratory analysis: the figures, written as standalone SVG files.

The brief asks for "purposeful exploratory analysis using appropriate statistics, comparisons and
clearly labelled visualisations", at least five of them. Each figure here answers a question the
owner would ask, and the module writes them to `docs/analysis/figures/` so the report can include
them and the dashboard can serve the same drawings - one implementation, not two.

No plotting library: the charts are the inline-SVG primitives the dashboard already uses, which keeps
the project's dependency list to what the analysis genuinely needs.

The five figures:

1. **Products per category and operator group** - what the evidence actually covers, and where it is
   thin. Read it before any price figure.
2. **Median price by category and group** - the comparison the whole project is about, in one view.
3. **Price distribution by category** - prices are strongly right-skewed, which is why every method
   here is rank-based or resampled rather than mean-and-standard-deviation.
4. **Observations per day** - the collection itself, including the days a source was missing.
5. **Price spread within each category** - how far apart the groups are, which is the answer to
   "which categories warrant further investigation".
6. **Share of products on sale** - discounting differs sharply by shop and changes what "the price"
   of a catalogue means.
"""
from pathlib import Path

import numpy as np

from priceintel.web import charts

FIGURE_STYLE = """
:root { --bg: #fbfaf8; --panel: #ffffff; --ink: #1c1b19; --muted: #6b6762; --line: #e6e1db;
        --c1: #7d4f9c; --c2: #3f7f8f; --c3: #b07a3c; --c4: #8c6f5e; --c5: #5a7a4f;
        --up: #a33f5b; --down: #3f7f8f; }
.chart-title { font-size: 13px; fill: var(--ink); font-weight: 600; }
.tick, .axis-label { font-size: 11px; fill: var(--muted); }
.axis { stroke: var(--line); } .grid { stroke: var(--line); stroke-dasharray: 2 3; }
.muted-text { font-size: 13px; fill: var(--muted); }
"""


def _write(directory: Path, name: str, svg: str, caption: str) -> Path:
    """A standalone SVG: the dashboard's CSS variables are inlined so the file stands on its own in
    the report."""
    path = directory / f"{name}.svg"
    svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
    svg = svg.replace(">", f"><style>{FIGURE_STYLE}</style>"
                           f"<desc>{caption}</desc>", 1)
    path.write_text(svg, encoding="utf-8")
    return path


def coverage(conn, pipeline_run_id: int) -> tuple[list[str], dict[str, list[float]]]:
    rows = conn.execute("""
        SELECT category, operator_group, COUNT(*) AS n
        FROM analysis_products WHERE pipeline_run_id = ? AND included = 1
        GROUP BY category, operator_group ORDER BY category, operator_group""",
        (pipeline_run_id,)).fetchall()
    categories = sorted({r["category"] for r in rows})
    series: dict[str, list[float]] = {}
    for r in rows:
        series.setdefault(r["operator_group"], [0.0] * len(categories))
    for r in rows:
        series[r["operator_group"]][categories.index(r["category"])] = float(r["n"])
    return categories, series


def median_prices(conn, pipeline_run_id: int) -> tuple[list[str], dict[str, list[float]]]:
    rows = conn.execute("""
        WITH ranked AS (
            SELECT category, operator_group, regular_price_uzs,
                   ROW_NUMBER() OVER (PARTITION BY category, operator_group
                                      ORDER BY regular_price_uzs) rn,
                   COUNT(*) OVER (PARTITION BY category, operator_group) n
            FROM analysis_products WHERE pipeline_run_id = ? AND included = 1)
        SELECT category, operator_group, AVG(regular_price_uzs) AS median_price
        FROM ranked WHERE rn IN ((n + 1) / 2, (n + 2) / 2)
        GROUP BY category, operator_group ORDER BY category, operator_group""",
        (pipeline_run_id,)).fetchall()
    categories = sorted({r["category"] for r in rows})
    series: dict[str, list[float]] = {}
    for r in rows:
        series.setdefault(r["operator_group"], [0.0] * len(categories))
    for r in rows:
        series[r["operator_group"]][categories.index(r["category"])] = float(r["median_price"])
    return categories, series


def write_figures(conn, pipeline_run_id: int, directory: Path | str) -> list[Path]:
    """Write every figure and return the paths, in the order the report uses them."""
    out = Path(directory)
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    categories, counts = coverage(conn, pipeline_run_id)
    written.append(_write(out, "01_coverage", charts.grouped_bars(
        categories, counts, title="Figure 1. Usable products per category and operator group",
        value_label="products", height=320),
        "How much evidence each comparison rests on, before any price is shown."))

    categories, medians = median_prices(conn, pipeline_run_id)
    written.append(_write(out, "02_median_price", charts.grouped_bars(
        categories, medians, title="Figure 2. Median regular price by category and operator group",
        value_label="UZS", height=320),
        "The price-position comparison in one view; bars are medians of distinct products."))

    prices = [float(r[0]) for r in conn.execute(
        "SELECT regular_price_uzs FROM analysis_products WHERE pipeline_run_id = ? AND included = 1",
        (pipeline_run_id,))]
    written.append(_write(out, "03_price_distribution", charts.histogram(
        prices, title="Figure 3. Distribution of regular prices (all usable products)",
        value_label="UZS", bins=24),
        "Strongly right-skewed, which is why the analysis uses rank-based and resampled methods."))

    days = conn.execute("""
        SELECT substr(o.observed_at, 1, 10) AS day, s.operator_group, COUNT(*) AS n
        FROM price_observations o
        JOIN listings l ON l.listing_id = o.listing_id
        JOIN shops s ON s.shop_id = l.shop_id
        JOIN scrape_runs r ON r.run_id = o.run_id
        WHERE r.purpose = (SELECT purpose FROM pipeline_runs WHERE pipeline_run_id = ?)
        GROUP BY day, s.operator_group ORDER BY day""", (pipeline_run_id,)).fetchall()
    labels = sorted({r["day"] for r in days})
    series: dict[str, list[float]] = {}
    for r in days:
        series.setdefault(r["operator_group"], [0.0] * len(labels))
    for r in days:
        series[r["operator_group"]][labels.index(r["day"])] = float(r["n"])
    written.append(_write(out, "04_collection_by_day", charts.line_chart(
        labels, series, title="Figure 4. Observations per day by operator group",
        value_label="observations", height=300),
        "The collection itself: a line that drops to zero is a source that stopped reporting."))

    spread_labels, spread_values = [], []
    for category in sorted({c for c, _ in zip(categories, categories)} | set(categories)):
        group_medians = [v[categories.index(category)] for v in medians.values()
                         if v[categories.index(category)] > 0]
        if len(group_medians) >= 2:
            spread_labels.append(category)
            spread_values.append(100.0 * (max(group_medians) / min(group_medians) - 1.0))
    written.append(_write(out, "05_price_spread", charts.bar_chart(
        spread_labels, spread_values,
        title="Figure 5. How far apart the groups are, per category",
        value_label="% between the dearest and cheapest group median"),
        "Where competitors disagree most about price is where a price position matters most."))

    sale = conn.execute("""
        SELECT operator_group,
               ROUND(100.0 * SUM(days_on_sale > 0) / COUNT(*), 1) AS pct
        FROM analysis_products WHERE pipeline_run_id = ? AND included = 1
        GROUP BY operator_group ORDER BY pct DESC""", (pipeline_run_id,)).fetchall()
    written.append(_write(out, "06_discounting", charts.bar_chart(
        [r["operator_group"] for r in sale], [float(r["pct"]) for r in sale],
        title="Figure 6. Share of products seen on sale, by operator group",
        value_label="% of products"),
        "Discounting differs sharply by shop, which changes what 'the price' of a catalogue means."))
    return written


def summary_statistics(conn, pipeline_run_id: int) -> list[dict]:
    """The table that goes beside the figures: per category and group, with the spread."""
    rows = conn.execute("""
        SELECT category, operator_group, COUNT(*) AS n_products,
               MIN(regular_price_uzs) AS min_uzs,
               MAX(regular_price_uzs) AS max_uzs,
               CAST(AVG(regular_price_uzs) AS INTEGER) AS mean_uzs,
               SUM(is_outlier) AS outliers,
               SUM(stem_count IS NOT NULL) AS with_stem_count
        FROM analysis_products WHERE pipeline_run_id = ? AND included = 1
        GROUP BY category, operator_group ORDER BY category, operator_group""",
        (pipeline_run_id,)).fetchall()
    out = []
    for r in rows:
        prices = [float(p[0]) for p in conn.execute(
            "SELECT regular_price_uzs FROM analysis_products WHERE pipeline_run_id = ?"
            " AND included = 1 AND category = ? AND operator_group = ?",
            (pipeline_run_id, r["category"], r["operator_group"]))]
        row = dict(r)
        row["median_uzs"] = int(np.median(prices))
        row["iqr_uzs"] = int(np.percentile(prices, 75) - np.percentile(prices, 25))
        out.append(row)
    return out
