"""The price-position comparison, and its uncertainty.

This is the approved estimand (ADR-004, ADR-008, `docs/analysis_plan.md`). For one category and one
competitor group::

    difference_pct = 100 * (median Secret price / median competitor price - 1)

reported with the median difference in UZS. A difference in log prices is never reported as a
percentage. A comparison is **displayed** only when both sides have at least ``min_items`` distinct
items; otherwise it is stored as ``insufficient_evidence`` with both counts, so an absent figure is
visible rather than missing.

**The bootstrap**, exactly as approved:

* B = 5,000 replicates within each category;
* whole **products** are resampled, so every observation of a product stays with it - the products
  are already summarised to one price each by the pipeline, which is where that happens;
* in each replicate the **Secret sample is drawn once and reused** across every competitor
  comparison, so the pooled figure keeps the dependence the comparisons share;
* each competitor group is resampled independently;
* 95% **percentile** intervals;
* no bootstrap over the four businesses: with four groups it would say nothing about the market.

The interval therefore describes the uncertainty of a median **within the four sampled operator
groups and the collection window**. It is not a confidence interval for the Tashkent market, and the
report says so next to every interval.

**Pooling.** Per-group comparisons are the primary output. The pooled row (`operator_group = 'ALL'`)
is the **unweighted mean of the per-group percentages**, so LOVEFLOWERS_NET does not outweigh
KAMILAS because it has more products.

Secret's offers come from `reference_offers` (the channel export, ADR-007, ADR-010) and never from the
scraped data. Until that export is imported, every comparison is stored as insufficient evidence
with `n_secret_offers = 0`, which is the honest state of the analysis rather than a blank page.
"""
import statistics
from dataclasses import dataclass

import numpy as np

from priceintel.db import transaction

BOOTSTRAP_REPLICATES = 5_000
MIN_ITEMS = 10
RANDOM_SEED = 20261109      # the first day of the approved window: a fixed, documented seed


@dataclass(frozen=True)
class Comparison:
    category: str
    operator_group: str
    n_products: int
    n_secret_offers: int
    competitor_median_uzs: int | None
    secret_median_uzs: int | None
    difference_uzs: int | None
    difference_pct: float | None
    ci_low_pct: float | None
    ci_high_pct: float | None
    evidence: str
    note: str | None = None


def _median(values) -> float | None:
    return float(np.median(values)) if len(values) else None


def full_coverage_days(conn, purpose: str) -> list[str]:
    """Dates on which at least one run reached every operator group.

    The Module Leader's question of 26 November 2026: do the category comparisons change when they
    are restricted to days with coverage from all four groups? On such a day every group is present
    in that day's data, so a missing source cannot tilt a category median."""
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT substr(started_at, 1, 10) FROM scrape_runs"
        " WHERE purpose = ? AND shops_expected > 0 AND shops_collected = shops_expected"
        " ORDER BY 1", (purpose,))]


def _median_prices_on_days(conn, purpose: str, days: list[str]) -> dict[int, float]:
    """Each listing's median regular price, computed only from observations made on those days.

    The price rule is the pipeline's: a regular price is the old price where a sale is shown and the
    shown price otherwise, and starting prices ("от") are not regular prices."""
    if not days:
        return {}
    marks = ", ".join("?" * len(days))
    rows = conn.execute(
        f"""SELECT o.listing_id, COALESCE(o.old_price_uzs, o.price_uzs) AS regular
            FROM price_observations o
            JOIN scrape_runs r ON r.run_id = o.run_id
            WHERE r.purpose = ? AND o.is_from_price = 0
              AND substr(o.observed_at, 1, 10) IN ({marks})""", (purpose, *days)).fetchall()
    by_listing: dict[int, list[float]] = {}
    for r in rows:
        by_listing.setdefault(r["listing_id"], []).append(float(r["regular"]))
    return {listing: float(statistics.median(prices)) for listing, prices in by_listing.items()}


def competitor_prices(conn, pipeline_run_id: int, *, exclude_outliers: bool = False,
                      only_stated_units: bool = False,
                      first_seen_before: str | None = None,
                      first_seen_from: str | None = None,
                      full_coverage_only: bool = False,
                      drop_group: str | None = None) -> dict[tuple[str, str], list[float]]:
    """Included products as {(category, operator_group): [regular prices]}.

    The keyword arguments are the robustness checks: each one re-runs the same comparison on a
    deliberately different subset, rather than on a different method. `full_coverage_only` is the
    exception in one respect: it does not merely drop products, it recomputes each product's median
    from the observations made on full-coverage days, because that is the price the shops showed on
    the days when every group was being read."""
    sql = ["SELECT category, operator_group, regular_price_uzs, is_outlier, price_unit,"
           "       first_observed_at, listing_id",
           "FROM analysis_products",
           "WHERE pipeline_run_id = :run AND included = 1"]
    params: dict = {"run": pipeline_run_id}
    if exclude_outliers:
        sql.append("AND is_outlier = 0")
    if drop_group:
        sql.append("AND operator_group <> :drop_group")
        params["drop_group"] = drop_group
    if first_seen_before:
        sql.append("AND first_observed_at < :before")
        params["before"] = first_seen_before
    if first_seen_from:
        sql.append("AND first_observed_at >= :from_date")
        params["from_date"] = first_seen_from
    rows = conn.execute("\n".join(sql), params).fetchall()

    on_full_days: dict[int, float] = {}
    if full_coverage_only:
        purpose = conn.execute("SELECT purpose FROM pipeline_runs WHERE pipeline_run_id = ?",
                               (pipeline_run_id,)).fetchone()[0]
        on_full_days = _median_prices_on_days(conn, purpose, full_coverage_days(conn, purpose))

    prices: dict[tuple[str, str], list[float]] = {}
    for r in rows:
        if full_coverage_only and r["listing_id"] not in on_full_days:
            continue        # never seen on a day when every group reported
        if only_stated_units:
            # The robustness check that drops products whose price unit was inferred rather than
            # stated by the shop.
            feature = conn.execute(
                "SELECT evidence FROM listing_features WHERE listing_id = ?"
                " ORDER BY computed_at DESC LIMIT 1", (r["listing_id"],)).fetchone()
            if feature is not None and feature["evidence"] != "stated":
                continue
        price = (on_full_days[r["listing_id"]] if full_coverage_only
                 else float(r["regular_price_uzs"]))
        prices.setdefault((r["category"], r["operator_group"]), []).append(price)
    return prices


def secret_prices(conn, *, window_start: str | None = None, window_end: str | None = None,
                  exclude_uncertain: bool = False) -> dict[str, list[float]]:
    """Secret's distinct offers per category, reposts already collapsed by the view."""
    sql = ["SELECT category, price_uzs, match_confidence FROM v_reference_distinct_offers",
           "WHERE category IS NOT NULL AND category NOT IN ('unclassified', 'out_of_scope')"]
    params: dict = {}
    if window_start:
        sql.append("AND first_published_at >= :start")
        params["start"] = window_start
    if window_end:
        sql.append("AND first_published_at <= :end")
        params["end"] = window_end + "T23:59:59Z"
    rows = conn.execute("\n".join(sql), params).fetchall()
    prices: dict[str, list[float]] = {}
    for r in rows:
        if exclude_uncertain and r["match_confidence"] == "uncertain":
            continue
        prices.setdefault(r["category"], []).append(float(r["price_uzs"]))
    return prices


def compare(competitor: dict[tuple[str, str], list[float]], secret: dict[str, list[float]], *,
            min_items: int = MIN_ITEMS, replicates: int = BOOTSTRAP_REPLICATES,
            seed: int = RANDOM_SEED) -> list[Comparison]:
    """Every category and group, with bootstrap intervals where both sides have enough items."""
    rng = np.random.default_rng(seed)
    results: list[Comparison] = []

    for category in sorted({c for c, _ in competitor}):
        groups = sorted(g for c, g in competitor if c == category)
        secret_sample = np.array(secret.get(category, []), dtype=float)
        # One resample of Secret per replicate, reused across this category's groups (ADR-008).
        if len(secret_sample) >= min_items:
            secret_draws = rng.choice(secret_sample, size=(replicates, len(secret_sample)),
                                      replace=True)
            secret_medians = np.median(secret_draws, axis=1)
        else:
            secret_medians = None

        per_group_pct: list[float] = []
        per_group_boot: list[np.ndarray] = []
        for group in groups:
            prices = np.array(competitor[(category, group)], dtype=float)
            n_products, n_offers = len(prices), len(secret_sample)
            competitor_median = _median(prices)
            secret_median = _median(secret_sample)
            enough = n_products >= min_items and n_offers >= min_items

            difference_uzs = difference_pct = ci_low = ci_high = None
            if competitor_median and secret_median:
                difference_uzs = int(round(secret_median - competitor_median))
                difference_pct = 100.0 * (secret_median / competitor_median - 1.0)
            if enough and secret_medians is not None:
                draws = rng.choice(prices, size=(replicates, n_products), replace=True)
                competitor_medians = np.median(draws, axis=1)
                pct = 100.0 * (secret_medians / competitor_medians - 1.0)
                ci_low, ci_high = (float(x) for x in np.percentile(pct, [2.5, 97.5]))
                per_group_pct.append(difference_pct)
                per_group_boot.append(pct)

            results.append(Comparison(
                category, group, n_products, n_offers,
                None if competitor_median is None else int(round(competitor_median)),
                None if secret_median is None else int(round(secret_median)),
                difference_uzs, difference_pct, ci_low, ci_high,
                "displayed" if enough else "insufficient_evidence",
                None if enough else
                f"needs {min_items} of each: {n_products} products, {n_offers} Secret offers"))

        if per_group_pct:
            # Pooled: the unweighted mean of the per-group percentages, bootstrapped the same way,
            # so the largest catalogue cannot dominate.
            pooled = float(np.mean(per_group_pct))
            pooled_draws = np.mean(np.vstack(per_group_boot), axis=0)
            low, high = (float(x) for x in np.percentile(pooled_draws, [2.5, 97.5]))
            results.append(Comparison(
                category, "ALL", sum(len(competitor[(category, g)]) for g in groups),
                len(secret_sample), None, None, None, pooled, low, high, "displayed",
                f"unweighted mean of {len(per_group_pct)} group comparisons"))
    return results


def store(conn, pipeline_run_id: int, results: list[Comparison], *, variant: str = "main",
          replicates: int = BOOTSTRAP_REPLICATES) -> int:
    """Record the results so a figure in the report can be traced to the build that produced it."""
    with transaction(conn):
        conn.execute("DELETE FROM comparison_results WHERE pipeline_run_id = ? AND variant = ?",
                     (pipeline_run_id, variant))
        for r in results:
            conn.execute(
                "INSERT INTO comparison_results (pipeline_run_id, variant, category,"
                " operator_group, n_products, n_secret_offers, competitor_median_uzs,"
                " secret_median_uzs, difference_uzs, difference_pct, ci_low_pct, ci_high_pct,"
                " bootstrap_replicates, evidence, note)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (pipeline_run_id, variant, r.category, r.operator_group, r.n_products,
                 r.n_secret_offers, r.competitor_median_uzs, r.secret_median_uzs, r.difference_uzs,
                 r.difference_pct, r.ci_low_pct, r.ci_high_pct, replicates, r.evidence, r.note))
    return len(results)


def run_comparison(conn, pipeline_run_id: int, *, min_items: int = MIN_ITEMS,
                   replicates: int = BOOTSTRAP_REPLICATES, variant: str = "main",
                   **subset) -> list[Comparison]:
    """Build both sides from the database, compare, and store the result."""
    competitor = competitor_prices(conn, pipeline_run_id, **subset)
    secret = secret_prices(conn)
    results = compare(competitor, secret, min_items=min_items, replicates=replicates)
    store(conn, pipeline_run_id, results, variant=variant, replicates=replicates)
    return results
