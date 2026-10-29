"""Data-quality checks over the stored data, with their results recorded in the database.

Each check is one question about the dataset as a whole, with a measured value, a threshold and a
status. They are deliberately about *fitness for the planned analysis*, not about taste:

* ``products_collected`` and ``runs_completed`` - progress against the approved data target.
* ``run_success_rate`` - the approved definition of a successful run (>= 80% of pages), against the
  95% promised in the proposal.
* ``quarantine_rate`` - how much of what was parsed had to be rejected. A rising rate is usually a
  parser breaking after a site redesign, which is the failure this project is most exposed to.
* ``unclassified_rate`` - products no category rule matched: they are excluded from the analysis, so
  a high rate narrows what can be said.
* ``freshness_days`` - the age of the newest observation, so a silently dead scheduler is visible.
* ``price_outlier_rate`` - prices more than 10x the category median; not removed here, only counted,
  because the robustness checks examine them deliberately.
* ``duplicate_observations`` - must be 0: the UNIQUE (listing_id, run_id) constraint should make a
  duplicate impossible, and this check proves the constraint is doing its job.
* ``orphan_observations`` - must be 0: every observation needs a listing, a run and (for scrapes) a
  fetch, which is the provenance promise.

A check that fails does not stop collection; it is evidence, and the report explains what was done
about it.
"""
from dataclasses import dataclass

from priceintel.db import transaction

TARGET_PRODUCTS = 300          # approved minimum data target
TARGET_RUNS = 50               # completed runs in the 28-day window
TARGET_SUCCESS_RATE = 95.0     # percent of runs that must be successful
MAX_QUARANTINE_RATE = 5.0      # percent of parsed records
MAX_UNCLASSIFIED_RATE = 25.0   # percent of products
MAX_FRESHNESS_DAYS = 1.0       # newest observation should be from the last day
MAX_OUTLIER_RATE = 2.0         # percent of products above 10x their category median


@dataclass(frozen=True)
class CheckResult:
    check_name: str
    scope: str
    measured: float
    threshold: float | None
    unit: str
    status: str
    detail: str | None = None


def _status(measured: float, threshold: float | None, *, higher_is_better: bool,
            warn_margin: float = 0.2) -> str:
    """'pass' when the threshold is met; 'warn' when it is close; 'fail' otherwise."""
    if threshold is None:
        return "pass"
    if higher_is_better:
        if measured >= threshold:
            return "pass"
        return "warn" if measured >= threshold * (1 - warn_margin) else "fail"
    if measured <= threshold:
        return "pass"
    return "warn" if measured <= threshold * (1 + warn_margin) else "fail"


def _scalar(conn, sql, params=()):
    row = conn.execute(sql, params).fetchone()
    return row[0] if row and row[0] is not None else 0


def run_checks(conn, *, purpose: str = "assessed", rules_version: str | None = None,
               store: bool = True) -> list[CheckResult]:
    """Run every check and (by default) record the results in ``data_quality_checks``."""
    results: list[CheckResult] = []

    products = _scalar(conn, """
        SELECT COUNT(DISTINCT l.listing_id) FROM listings l
        JOIN shops s ON s.shop_id = l.shop_id
        WHERE s.is_own_shop = 0
          AND EXISTS (SELECT 1 FROM price_observations o JOIN scrape_runs r ON r.run_id = o.run_id
                      WHERE o.listing_id = l.listing_id AND r.purpose = ?)""", (purpose,))
    results.append(CheckResult("products_collected", "all", products, TARGET_PRODUCTS, "count",
                               _status(products, TARGET_PRODUCTS, higher_is_better=True),
                               "distinct competitor products, mirrors excluded by design"))

    runs = _scalar(conn, "SELECT COUNT(*) FROM scrape_runs WHERE purpose = ? AND finished_at"
                         " IS NOT NULL", (purpose,))
    results.append(CheckResult("runs_completed", "all", runs, TARGET_RUNS, "count",
                               _status(runs, TARGET_RUNS, higher_is_better=True)))

    ok = _scalar(conn, "SELECT COUNT(*) FROM scrape_runs WHERE purpose = ? AND status = 'success'",
                 (purpose,))
    rate = 100.0 * ok / runs if runs else 0.0
    results.append(CheckResult("run_success_rate", "all", round(rate, 1), TARGET_SUCCESS_RATE,
                               "percent", _status(rate, TARGET_SUCCESS_RATE, higher_is_better=True),
                               f"{ok} of {runs} runs"))

    saved = _scalar(conn, "SELECT SUM(observations_saved) FROM scrape_runs WHERE purpose = ?",
                    (purpose,))
    rejected = _scalar(conn, "SELECT SUM(records_rejected) FROM scrape_runs WHERE purpose = ?",
                       (purpose,))
    parsed = saved + rejected
    q_rate = 100.0 * rejected / parsed if parsed else 0.0
    top_rule = conn.execute("""
        SELECT rule, COUNT(*) n FROM rejected_records rr
        JOIN scrape_runs r ON r.run_id = rr.run_id
        WHERE r.purpose = ? GROUP BY rule ORDER BY n DESC LIMIT 1""", (purpose,)).fetchone()
    results.append(CheckResult("quarantine_rate", "all", round(q_rate, 1), MAX_QUARANTINE_RATE,
                               "percent", _status(q_rate, MAX_QUARANTINE_RATE,
                                                  higher_is_better=False),
                               f"{rejected} of {parsed} parsed records"
                               + (f"; most common rule: {top_rule['rule']} ({top_rule['n']})"
                                  if top_rule else "")))

    if rules_version:
        classified = _scalar(conn, """
            SELECT COUNT(*) FROM listing_categories c JOIN listings l ON l.listing_id = c.listing_id
            JOIN shops s ON s.shop_id = l.shop_id
            WHERE c.rules_version = ? AND s.is_own_shop = 0""", (rules_version,))
        unknown = _scalar(conn, """
            SELECT COUNT(*) FROM listing_categories c JOIN listings l ON l.listing_id = c.listing_id
            JOIN shops s ON s.shop_id = l.shop_id
            WHERE c.rules_version = ? AND s.is_own_shop = 0
              AND c.category IN ('unclassified', 'out_of_scope')""", (rules_version,))
        u_rate = 100.0 * unknown / classified if classified else 0.0
        results.append(CheckResult("unclassified_rate", "all", round(u_rate, 1),
                                   MAX_UNCLASSIFIED_RATE, "percent",
                                   _status(u_rate, MAX_UNCLASSIFIED_RATE, higher_is_better=False),
                                   f"{unknown} of {classified} products excluded by the rules"))

        outliers = _scalar(conn, """
            WITH product AS (
                SELECT l.listing_id, c.category, MAX(o.price_uzs) AS price_uzs
                FROM price_observations o
                JOIN listings l ON l.listing_id = o.listing_id
                JOIN shops    s ON s.shop_id    = l.shop_id
                JOIN scrape_runs r ON r.run_id  = o.run_id
                JOIN listing_categories c ON c.listing_id = l.listing_id
                                         AND c.rules_version = ?
                WHERE s.is_own_shop = 0 AND r.purpose = ?
                GROUP BY l.listing_id, c.category),
            ranked AS (
                SELECT category, price_uzs,
                       ROW_NUMBER() OVER (PARTITION BY category ORDER BY price_uzs) rn,
                       COUNT(*)     OVER (PARTITION BY category) n
                FROM product),
            med AS (
                SELECT category, AVG(price_uzs) AS median_price
                FROM ranked WHERE rn IN ((n + 1) / 2, (n + 2) / 2) GROUP BY category)
            SELECT COUNT(*) FROM product p JOIN med m ON m.category = p.category
            WHERE p.price_uzs > 10 * m.median_price""", (rules_version, purpose))
        o_rate = 100.0 * outliers / products if products else 0.0
        results.append(CheckResult("price_outlier_rate", "all", round(o_rate, 1), MAX_OUTLIER_RATE,
                                   "percent", _status(o_rate, MAX_OUTLIER_RATE,
                                                      higher_is_better=False),
                                   f"{outliers} products above 10x their category median; counted,"
                                   " not removed - the robustness checks handle them"))

    newest = conn.execute("""
        SELECT MAX(o.observed_at) FROM price_observations o
        JOIN scrape_runs r ON r.run_id = o.run_id WHERE r.purpose = ?""", (purpose,)).fetchone()[0]
    age = _scalar(conn, "SELECT ROUND(julianday('now') - julianday(?), 2)", (newest,)) if newest \
        else 999.0
    results.append(CheckResult("freshness_days", "all", age, MAX_FRESHNESS_DAYS, "days",
                               _status(age, MAX_FRESHNESS_DAYS, higher_is_better=False),
                               f"newest observation: {newest or 'none'}"))

    duplicates = _scalar(conn, """
        SELECT COUNT(*) FROM (SELECT listing_id, run_id FROM price_observations
                              GROUP BY listing_id, run_id HAVING COUNT(*) > 1)""")
    results.append(CheckResult("duplicate_observations", "all", duplicates, 0, "count",
                               _status(duplicates, 0, higher_is_better=False),
                               "UNIQUE (listing_id, run_id) should make this impossible"))

    orphans = _scalar(conn, """
        SELECT COUNT(*) FROM price_observations o
        LEFT JOIN listings    l ON l.listing_id = o.listing_id
        LEFT JOIN scrape_runs r ON r.run_id     = o.run_id
        LEFT JOIN fetch_log   f ON f.fetch_id   = o.fetch_id
        WHERE l.listing_id IS NULL OR r.run_id IS NULL
           OR (o.source_type = 'scrape' AND f.fetch_id IS NULL)""")
    results.append(CheckResult("orphan_observations", "all", orphans, 0, "count",
                               _status(orphans, 0, higher_is_better=False),
                               "every observation must trace to a listing, a run and its fetch"))

    if store:
        with transaction(conn):
            for r in results:
                conn.execute(
                    "INSERT INTO data_quality_checks (purpose, check_name, scope, measured,"
                    " threshold, unit, status, detail) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (purpose, r.check_name, r.scope, float(r.measured),
                     None if r.threshold is None else float(r.threshold), r.unit, r.status,
                     r.detail))
    return results
