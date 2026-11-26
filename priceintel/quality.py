"""Data-quality checks over the stored data, with their results recorded in the database.

Each check is one question about the dataset as a whole, with a measured value, a threshold and a
status. They are deliberately about *fitness for the planned analysis*, not about taste:

* ``products_collected`` and ``runs_completed`` - progress against the approved data target.
* ``run_success_rate`` - the approved definition of a successful run (>= 80% of pages), against the
  95% promised in the proposal. Measured over the runs that **started**.
* ``scheduled_slot_completion`` - the same question measured the way the Module Leader directed on
  26 November 2026: against **every scheduled run, including any that never started**. The schedule
  is two slots a day (`SCHEDULE_UTC_HOURS`), so the denominator is every elapsed slot in the
  approved window and a slot with no run at all counts as a failure. This is the figure objective O1
  is judged on; `run_success_rate` is kept beside it because the difference between the two is
  exactly the number of runs GitHub never started.
* ``consecutive_complete_runs`` - the current streak of runs that reached every operator group.
  Reported, with no threshold: after the two defects of the first week were fixed, the streak is the
  evidence that they stayed fixed, and the Module Leader asked for it to be reported separately
  rather than folded into the rate.
* ``quarantine_rate`` - how much of what was parsed had to be rejected. A rising rate is usually a
  parser breaking after a site redesign, which is the failure this project is most exposed to.
* ``unclassified_rate`` - products no category rule matched: they are excluded from the analysis, so
  a high rate narrows what can be said.
* ``freshness_days`` - the age of the newest observation, so a silently dead scheduler is visible.
* ``group_freshness_days`` - the same, **per operator group**. The overall figure cannot catch a
  single source going quiet: when loveflowers.uz redesigned its theme on 13 November 2026 its parser
  returned nothing for five runs while the other three groups kept the overall freshness green. One
  row per group, so a missing source fails its own check.
* ``price_outlier_rate`` - prices more than 10x the category median; not removed here, only counted,
  because the robustness checks examine them deliberately.
* ``duplicate_observations`` - must be 0: the UNIQUE (listing_id, run_id) constraint should make a
  duplicate impossible, and this check proves the constraint is doing its job.
* ``orphan_observations`` - must be 0: every observation needs a listing, a run and (for scrapes) a
  fetch, which is the provenance promise.

A check that fails does not stop collection; it is evidence, and the report explains what was done
about it.
"""
import datetime as dt
from dataclasses import dataclass

from priceintel import config
from priceintel.db import transaction

# The collection schedule, from .github/workflows/collect.yml (`cron: "17 3,15 * * *"`). One
# definition, so the workflow and the measure of it cannot drift apart.
SCHEDULE_UTC_HOURS = (3, 15)
SCHEDULE_UTC_MINUTE = 17
SLOT_HOURS = 12

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


def scheduled_slots(window_start: str, window_end: str) -> list[dt.datetime]:
    """Every scheduled collection time in the approved window, from the workflow's own cron.

    The window is given in Asia/Tashkent dates (UTC+5), which is how the Module Leader set it, so a
    slot belongs to the window when its local date does."""
    local = dt.timezone(dt.timedelta(hours=5))
    first = dt.date.fromisoformat(window_start)
    last = dt.date.fromisoformat(window_end)
    slots = []
    day = first - dt.timedelta(days=1)          # a 15:17Z slot falls on the next local date
    while day <= last:
        for hour in SCHEDULE_UTC_HOURS:
            slot = dt.datetime(day.year, day.month, day.day, hour, SCHEDULE_UTC_MINUTE,
                               tzinfo=dt.timezone.utc)
            if first <= slot.astimezone(local).date() <= last:
                slots.append(slot)
        day += dt.timedelta(days=1)
    return sorted(slots)


def _schedule_checks(conn, purpose: str) -> list[CheckResult]:
    """O1 measured against every scheduled run, including the ones that never started."""
    rows = conn.execute(
        "SELECT started_at, shops_expected, shops_collected FROM scrape_runs"
        " WHERE purpose = ? ORDER BY started_at", (purpose,)).fetchall()
    if not rows:
        return []
    started = [(dt.datetime.fromisoformat(r["started_at"].replace("Z", "+00:00")),
                bool(r["shops_expected"]) and r["shops_collected"] == r["shops_expected"])
               for r in rows]
    latest = max(when for when, _ in started)

    slots = scheduled_slots(config.APPROVED_WINDOW_START, config.APPROVED_WINDOW_END)
    span = dt.timedelta(hours=SLOT_HOURS)
    elapsed = [s for s in slots if s + span <= latest]
    complete = never_started = 0
    for slot in elapsed:
        inside = [full for when, full in started if slot <= when < slot + span]
        if not inside:
            never_started += 1
        elif any(inside):
            complete += 1
    rate = 100.0 * complete / len(elapsed) if elapsed else 0.0

    streak = 0
    for _, full in reversed(started):
        if not full:
            break
        streak += 1

    return [
        CheckResult("scheduled_slot_completion", "all", round(rate, 1), TARGET_SUCCESS_RATE,
                    "percent", _status(rate, TARGET_SUCCESS_RATE, higher_is_better=True),
                    f"{complete} of {len(elapsed)} elapsed scheduled slots reached every operator "
                    f"group; {never_started} slot(s) never started at all "
                    f"({len(slots)} slots in the approved window)"),
        # No threshold: this one is reported, not judged. The schema allows pass/warn/fail only.
        CheckResult("consecutive_complete_runs", "all", streak, None, "count", "pass",
                    f"reported, not judged: the most recent {streak} run(s) reached every "
                    f"operator group"),
    ]


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
                               f"{ok} of {runs} runs that started"))

    results.extend(_schedule_checks(conn, purpose))

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

    for group, newest_at in conn.execute("""
            SELECT s.operator_group,
                   (SELECT MAX(o.observed_at) FROM price_observations o
                    JOIN listings l ON l.listing_id = o.listing_id
                    JOIN scrape_runs r ON r.run_id = o.run_id
                    WHERE l.shop_id = s.shop_id AND r.purpose = ?) AS newest_at
            FROM shops s WHERE s.is_active = 1 AND s.is_own_shop = 0
            ORDER BY s.operator_group""", (purpose,)):
        group_age = _scalar(conn, "SELECT ROUND(julianday('now') - julianday(?), 2)",
                            (newest_at,)) if newest_at else 999.0
        results.append(CheckResult(
            "group_freshness_days", group, group_age, MAX_FRESHNESS_DAYS, "days",
            _status(group_age, MAX_FRESHNESS_DAYS, higher_is_better=False),
            f"newest observation from this group: {newest_at or 'none in this dataset'}"))

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
