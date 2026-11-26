"""Everything the dashboard reads, from both databases.

The dashboard never writes. It reads `market_intel` (collected competitor data, categories, quality
checks, Secret's reference offers) and `secret_shop` (the shop's own operational tables), and runs the
cross-database integrity check so a broken link between them is visible on the page rather than
discovered in the report.

The five stakeholder queries are not duplicated here: the pages run the same `.sql` files from
`sql/queries/` that the command line runs, so a number on a page and a number in the report come from
one source. The functions below are the chart-shaped aggregations that have no stakeholder query of
their own (a price distribution, a daily series).
"""
from dataclasses import dataclass, field

from priceintel import config
from priceintel.queries import available, question_of, run


@dataclass(frozen=True)
class Selection:
    """The validated user input of a page. Invalid input never reaches a query."""
    purpose: str = "assessed"
    rules_version: str = ""
    min_items: int = 10
    category: str = ""
    limit: int = 20

    def as_params(self) -> dict:
        return {"purpose": self.purpose, "rules_version": self.rules_version,
                "min_items": self.min_items, "limit": self.limit}


@dataclass
class Databases:
    market: object
    secret: object | None = None
    queries: dict = field(default_factory=dict)

    @classmethod
    def open(cls, market_path, secret_path=None):
        from priceintel.db import connect
        from pathlib import Path
        market = connect(market_path)
        secret = connect(secret_path) if secret_path and Path(secret_path).exists() else None
        return cls(market, secret, available(config.QUERIES_DIR))

    def query(self, name: str, selection: Selection):
        """Run one of the stakeholder queries and return (question, columns, rows)."""
        path = self.queries[name]
        columns, rows = run(self.market, path, selection.as_params())
        return question_of(path), columns, rows


def purposes(conn) -> list[str]:
    """Which purposes actually have data, so the page offers real choices only."""
    found = [r[0] for r in conn.execute(
        "SELECT DISTINCT purpose FROM scrape_runs ORDER BY purpose")]
    return found or ["assessed"]


def rules_versions(conn) -> list[str]:
    return [r[0] for r in conn.execute(
        "SELECT rules_version FROM category_rule_sets ORDER BY registered_at DESC")]


def categories(conn, rules_version: str) -> list[str]:
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT category FROM listing_categories WHERE rules_version = ?"
        " ORDER BY category", (rules_version,))]


def headline(conn, selection: Selection) -> dict:
    """The numbers at the top of the overview page."""
    one = lambda sql, params=(): (conn.execute(sql, params).fetchone() or [0])[0] or 0
    return {
        "products": one("""SELECT COUNT(DISTINCT l.listing_id) FROM listings l
                           JOIN shops s ON s.shop_id = l.shop_id
                           WHERE s.is_own_shop = 0 AND EXISTS (
                               SELECT 1 FROM price_observations o JOIN scrape_runs r
                               ON r.run_id = o.run_id
                               WHERE o.listing_id = l.listing_id AND r.purpose = ?)""",
                       (selection.purpose,)),
        "observations": one("""SELECT COUNT(*) FROM price_observations o
                               JOIN scrape_runs r ON r.run_id = o.run_id WHERE r.purpose = ?""",
                            (selection.purpose,)),
        "runs": one("SELECT COUNT(*) FROM scrape_runs WHERE purpose = ?", (selection.purpose,)),
        "groups": one("""SELECT COUNT(DISTINCT s.operator_group) FROM shops s
                         WHERE s.is_active = 1 AND s.is_own_shop = 0"""),
        "secret_offers": one("SELECT COUNT(*) FROM v_reference_distinct_offers"),
        "quarantined": one("""SELECT COUNT(*) FROM rejected_records rr
                              JOIN scrape_runs r ON r.run_id = rr.run_id WHERE r.purpose = ?""",
                           (selection.purpose,)),
        "newest": conn.execute("""SELECT MAX(o.observed_at) FROM price_observations o
                                  JOIN scrape_runs r ON r.run_id = o.run_id
                                  WHERE r.purpose = ?""", (selection.purpose,)).fetchone()[0],
    }


def product_prices(conn, selection: Selection) -> list[float]:
    """One regular price per competitor product in the selected category: the data behind the
    distribution chart. Repeated observations are collapsed by taking each product's median."""
    sql = """
        WITH observation AS (
            SELECT l.listing_id, COALESCE(o.old_price_uzs, o.price_uzs) AS price_uzs
            FROM price_observations o
            JOIN listings    l ON l.listing_id = o.listing_id
            JOIN shops       s ON s.shop_id    = l.shop_id
            JOIN scrape_runs r ON r.run_id     = o.run_id
            JOIN listing_categories c ON c.listing_id = l.listing_id
                                     AND c.rules_version = :rules_version
            WHERE o.source_type = 'scrape' AND o.is_from_price = 0
              AND s.is_own_shop = 0 AND r.purpose = :purpose
              AND (:category = '' OR c.category = :category)),
        ranked AS (
            SELECT listing_id, price_uzs,
                   ROW_NUMBER() OVER (PARTITION BY listing_id ORDER BY price_uzs) rn,
                   COUNT(*)     OVER (PARTITION BY listing_id) n
            FROM observation)
        SELECT AVG(price_uzs) FROM ranked WHERE rn IN ((n + 1) / 2, (n + 2) / 2)
        GROUP BY listing_id"""
    return [r[0] for r in conn.execute(sql, {"rules_version": selection.rules_version,
                                             "purpose": selection.purpose,
                                             "category": selection.category})]


def median_price_by_group(conn, selection: Selection) -> tuple[list[str], dict[str, list[float]]]:
    """Median regular price per category and operator group, for the grouped-bar chart."""
    sql = """
        WITH product AS (
            SELECT l.listing_id, s.operator_group, c.category,
                   MAX(COALESCE(o.old_price_uzs, o.price_uzs)) AS price_uzs
            FROM price_observations o
            JOIN listings    l ON l.listing_id = o.listing_id
            JOIN shops       s ON s.shop_id    = l.shop_id
            JOIN scrape_runs r ON r.run_id     = o.run_id
            JOIN listing_categories c ON c.listing_id = l.listing_id
                                     AND c.rules_version = :rules_version
            WHERE o.source_type = 'scrape' AND o.is_from_price = 0
              AND s.is_own_shop = 0 AND r.purpose = :purpose
              AND c.category NOT IN ('out_of_scope', 'unclassified')
            GROUP BY l.listing_id, s.operator_group, c.category),
        ranked AS (
            SELECT category, operator_group, price_uzs,
                   ROW_NUMBER() OVER (PARTITION BY category, operator_group ORDER BY price_uzs) rn,
                   COUNT(*)     OVER (PARTITION BY category, operator_group) n
            FROM product)
        SELECT category, operator_group, CAST(AVG(price_uzs) AS INTEGER) AS median_price
        FROM ranked WHERE rn IN ((n + 1) / 2, (n + 2) / 2)
        GROUP BY category, operator_group ORDER BY category, operator_group"""
    rows = conn.execute(sql, {"rules_version": selection.rules_version,
                              "purpose": selection.purpose}).fetchall()
    cats = sorted({r["category"] for r in rows})
    series: dict[str, list[float]] = {}
    for r in rows:
        series.setdefault(r["operator_group"], [0.0] * len(cats))
    for r in rows:
        series[r["operator_group"]][cats.index(r["category"])] = float(r["median_price"])
    return cats, series


def daily_collection(conn, selection: Selection) -> tuple[list[str], dict[str, list[float]]]:
    """Observations saved and page success rate per day: is the collector alive and healthy?"""
    rows = conn.execute("""
        SELECT substr(started_at, 1, 10) AS day,
               SUM(observations_saved)   AS observations,
               CASE WHEN SUM(pages_requested) = 0 THEN 0
                    ELSE ROUND(100.0 * SUM(pages_ok) / SUM(pages_requested), 1) END AS page_pct
        FROM scrape_runs WHERE purpose = ? GROUP BY day ORDER BY day""",
        (selection.purpose,)).fetchall()
    labels = [r["day"] for r in rows]
    return labels, {"observations saved": [float(r["observations"] or 0) for r in rows],
                    "page success %": [float(r["page_pct"] or 0) for r in rows]}


def quality_results(conn, selection: Selection) -> list[dict]:
    return [dict(r) for r in conn.execute(
        "SELECT check_name, measured, threshold, unit, status, detail, run_at"
        " FROM v_data_quality_latest WHERE purpose = ? ORDER BY status DESC, check_name",
        (selection.purpose,))]


def secret_shop_state(databases: Databases) -> dict:
    """What the operational database holds. Shown so the dashboard is visibly connected to both."""
    if databases.secret is None:
        return {"available": False}
    tables = ("categories", "products", "product_price_history", "clients", "addresses", "orders",
              "order_items", "payments", "admin_users")
    counts: dict[str, int] = {}
    # Secret's operational rows are synthetic fixtures (the shop has no ordering system), so the
    # page reports how many of each table's rows are declared synthetic. A count of invented orders
    # shown without that column would read as real trade.
    synthetic: dict[str, int] = {}
    for table in tables:
        exists = databases.secret.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone()
        if not exists:
            continue
        counts[table] = databases.secret.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        columns = {r["name"] for r in databases.secret.execute(f'PRAGMA table_info("{table}")')}
        if "is_synthetic" in columns:
            synthetic[table] = databases.secret.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE is_synthetic = 1').fetchone()[0]
        elif table == "order_items":                      # inherits its order's declaration
            synthetic[table] = databases.secret.execute(
                "SELECT COUNT(*) FROM order_items i JOIN orders o ON o.order_id = i.order_id"
                " WHERE o.is_synthetic = 1").fetchone()[0]
        elif table == "product_price_history":
            synthetic[table] = databases.secret.execute(
                "SELECT COUNT(*) FROM product_price_history h JOIN products p"
                " ON p.product_id = h.product_id WHERE p.is_synthetic = 1").fetchone()[0]
    return {"available": True, "counts": counts, "synthetic": synthetic}


def integrity(databases: Databases) -> list[str]:
    """The cross-database check, run live on the page."""
    if databases.secret is None:
        return ["secret_shop database not found: cross-database check not run"]
    from priceintel.integrity import cross_db_orphans
    return cross_db_orphans(databases.market, databases.secret)


# ---------------------------------------------------------------------------
# The analysis: what the pipeline and `analyse` produced (Checkpoint 4)
# ---------------------------------------------------------------------------

def latest_analysis(conn, selection: Selection) -> dict | None:
    """The newest dataset build for this purpose, with the stage counts that produced it."""
    row = conn.execute(
        "SELECT * FROM pipeline_runs WHERE purpose = ? ORDER BY pipeline_run_id DESC LIMIT 1",
        (selection.purpose,)).fetchone()
    return dict(row) if row else None


def comparison_rows(conn, pipeline_run_id: int, variant: str = "main") -> list[dict]:
    return [dict(r) for r in conn.execute(
        "SELECT * FROM comparison_results WHERE pipeline_run_id = ? AND variant = ?"
        " ORDER BY category, operator_group", (pipeline_run_id, variant))]


def hypothesis_rows(conn, pipeline_run_id: int) -> list[dict]:
    return [dict(r) for r in conn.execute(
        "SELECT * FROM hypothesis_tests WHERE pipeline_run_id = ?"
        " ORDER BY method, scope", (pipeline_run_id,))]


def model_rows(conn, pipeline_run_id: int) -> list[dict]:
    """Pooled metrics per model and scope (fold -1 is the figure over all folds)."""
    return [dict(r) for r in conn.execute("""
        SELECT r.model_name, r.split_kind, m.scope, m.metric, m.value
        FROM model_runs r JOIN model_metrics m ON m.model_run_id = r.model_run_id
        WHERE r.pipeline_run_id = ? AND m.fold = -1
        ORDER BY m.scope, r.model_name, m.metric""", (pipeline_run_id,))]


def robustness_variants(conn, pipeline_run_id: int) -> list[dict]:
    """How many comparisons each robustness variant could display, beside the main run."""
    return [dict(r) for r in conn.execute("""
        SELECT variant,
               COUNT(*)                                        AS rows_stored,
               SUM(evidence = 'displayed')                     AS displayed,
               COUNT(DISTINCT category)                        AS categories
        FROM comparison_results WHERE pipeline_run_id = ?
        GROUP BY variant ORDER BY (variant = 'main') DESC, variant""", (pipeline_run_id,))]


def decision_table(conn, pipeline_run_id: int, min_items: int = 10) -> list[dict]:
    """The decision-support output: where the sampled shops disagree most about price.

    Only groups with at least ``min_items`` usable products take part, the same minimum the approved
    plan applies to every displayed comparison. Without it the ranking is set by whichever category
    happens to contain one expensive product: the first version of this table sent the owner to
    potted plants on a 3,948% spread, which was one PROBUKET plant at 1.8M UZS against loveflowers'
    45,000.

    Categories that cannot clear the minimum are returned too, marked ``insufficient_evidence``, so
    they are visibly absent rather than silently missing.
    """
    rows = conn.execute("""
        WITH ranked AS (
            SELECT category, operator_group, regular_price_uzs,
                   ROW_NUMBER() OVER (PARTITION BY category, operator_group
                                      ORDER BY regular_price_uzs) rn,
                   COUNT(*)     OVER (PARTITION BY category, operator_group) n
            FROM analysis_products WHERE pipeline_run_id = :run AND included = 1),
        medians AS (
            SELECT category, operator_group, AVG(regular_price_uzs) AS median_price, MAX(n) AS n
            FROM ranked WHERE rn IN ((n + 1) / 2, (n + 2) / 2)
            GROUP BY category, operator_group),
        eligible AS (SELECT * FROM medians WHERE n >= :min_items)
        SELECT m.category,
               (SELECT COUNT(*) FROM eligible e WHERE e.category = m.category) AS groups_compared,
               (SELECT GROUP_CONCAT(e.operator_group, ', ') FROM eligible e
                WHERE e.category = m.category)                                 AS groups,
               (SELECT SUM(e.n) FROM eligible e WHERE e.category = m.category) AS products,
               (SELECT CAST(MIN(e.median_price) AS INTEGER) FROM eligible e
                WHERE e.category = m.category)                                 AS cheapest_uzs,
               (SELECT CAST(MAX(e.median_price) AS INTEGER) FROM eligible e
                WHERE e.category = m.category)                                 AS dearest_uzs,
               COUNT(*)                                                        AS groups_present
        FROM medians m GROUP BY m.category""", {"run": pipeline_run_id,
                                                "min_items": min_items}).fetchall()
    out = []
    for r in rows:
        row = dict(r)
        if (row["groups_compared"] or 0) >= 2 and row["cheapest_uzs"]:
            row["spread_pct"] = round(100.0 * (row["dearest_uzs"] / row["cheapest_uzs"] - 1), 1)
            row["evidence"] = "displayed"
        else:
            row["spread_pct"] = None
            row["evidence"] = "insufficient_evidence"
            row["note"] = (f"needs two groups with {min_items} usable products; "
                           f"{row['groups_compared'] or 0} of {row['groups_present']} qualify")
        out.append(row)
    out.sort(key=lambda r: (r["evidence"] != "displayed", -(r["spread_pct"] or 0)))
    return out
