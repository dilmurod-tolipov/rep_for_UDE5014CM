"""Robustness checks: does the answer survive a defensible change to how it was produced?

The brief asks for at least three "meaningful robustness or sensitivity investigations", and the
approved plan names them. Each check re-runs **the same comparison and the same test** on a
deliberately different subset, so a difference in the result is a property of the data rather than of
the method:

1. **Leave one operator group out**, in turn. If one shop's catalogue drives the finding, the finding
   is about that shop and not about the market.
2. **Exclude flagged outliers.** They are kept in the main dataset on purpose; this check asks what
   the answer would be without them.
3. **First half against second half of the collection window.** Prices move; a result that only holds
   in one half is a seasonal observation, not a price position.
4. **Only stated price units.** Products whose per-stem or per-item status was inferred rather than
   stated by the shop are dropped.
5. **Only days when every operator group reported.** Eleven runs in the window lost a group, so a
   category median could in principle be set by whichever shops happened to answer that day. This
   check recomputes every product's median from the observations made on full-coverage days only.
   Asked for by the Module Leader on 26 November 2026, who called it "the most useful check for
   your conclusions".
6. **Exclude uncertain Secret matches** - reposts grouped by caption at a different price (ADR-008).
   It runs once Secret's export is imported.

Each check stores its results under its own `variant`, beside the main one, so the report can show
them together instead of asserting that nothing changed.
"""
from dataclasses import dataclass

import numpy as np

from priceintel.analysis import comparison
from priceintel.analysis.hypothesis import groups_differ_within_category


@dataclass(frozen=True)
class CheckOutcome:
    variant: str
    description: str
    n_products: int
    categories_tested: int
    categories_significant: int
    median_shift_pct: float | None    # how far the per-group percentages moved from the main run
    note: str


def _significant(prices) -> tuple[int, int]:
    results = groups_differ_within_category(prices)
    tested = [r for r in results if r.p_adjusted is not None]
    return len(tested), sum(1 for r in tested if r.p_adjusted < 0.05)


def run_all(conn, pipeline_run_id: int, *, window_start: str, window_end: str,
            replicates: int = 1_000) -> list[CheckOutcome]:
    """Every check, stored and summarised. Fewer bootstrap replicates than the main run by default:
    these are comparisons of comparisons, and 1,000 is enough to see a shift."""
    main_prices = comparison.competitor_prices(conn, pipeline_run_id)
    main_tested, main_significant = _significant(main_prices)
    main_medians = {key: float(np.median(v)) for key, v in main_prices.items()}
    outcomes: list[CheckOutcome] = []

    def shift(prices) -> float | None:
        """Median absolute change in a group's category median, as a percentage of the main run."""
        changes = [abs(float(np.median(v)) / main_medians[key] - 1.0) * 100.0
                   for key, v in prices.items() if key in main_medians and main_medians[key]]
        return float(np.median(changes)) if changes else None

    groups = sorted({g for _, g in main_prices})
    for group in groups:
        variant = f"drop_{group.lower()}"
        prices = comparison.competitor_prices(conn, pipeline_run_id, drop_group=group)
        comparison.run_comparison(conn, pipeline_run_id, variant=variant, replicates=replicates,
                                  drop_group=group)
        tested, significant = _significant(prices)
        outcomes.append(CheckOutcome(
            variant, f"leave out {group}", sum(len(v) for v in prices.values()), tested,
            significant, shift(prices),
            f"{significant} of {tested} categories still differ across the remaining groups "
            f"(main run: {main_significant} of {main_tested})"))

    prices = comparison.competitor_prices(conn, pipeline_run_id, exclude_outliers=True)
    comparison.run_comparison(conn, pipeline_run_id, variant="no_outliers", replicates=replicates,
                              exclude_outliers=True)
    tested, significant = _significant(prices)
    outcomes.append(CheckOutcome(
        "no_outliers", "exclude flagged outliers", sum(len(v) for v in prices.values()), tested,
        significant, shift(prices),
        f"{significant} of {tested} categories differ without the outliers "
        f"(main run: {main_significant} of {main_tested})"))

    midpoint = _midpoint(window_start, window_end)
    for variant, kwargs, label in (
            ("first_half", {"first_seen_before": midpoint}, f"products first seen before {midpoint}"),
            ("second_half", {"first_seen_from": midpoint}, f"products first seen from {midpoint}")):
        prices = comparison.competitor_prices(conn, pipeline_run_id, **kwargs)
        if not prices:
            outcomes.append(CheckOutcome(variant, label, 0, 0, 0, None, "no products in this half"))
            continue
        comparison.run_comparison(conn, pipeline_run_id, variant=variant, replicates=replicates,
                                  **kwargs)
        tested, significant = _significant(prices)
        outcomes.append(CheckOutcome(
            variant, label, sum(len(v) for v in prices.values()), tested, significant,
            shift(prices),
            f"{significant} of {tested} categories differ in this half of the window"))

    # The Module Leader's check (26 November 2026): 11 of the window's runs lost an operator group,
    # so do the category comparisons change when only the days with all four groups are used?
    # Prices are recomputed from those days' observations, not merely filtered.
    prices = comparison.competitor_prices(conn, pipeline_run_id, full_coverage_only=True)
    days = comparison.full_coverage_days(
        conn, conn.execute("SELECT purpose FROM pipeline_runs WHERE pipeline_run_id = ?",
                           (pipeline_run_id,)).fetchone()[0])
    if not prices:
        outcomes.append(CheckOutcome("full_coverage_days", "only days when every group reported",
                                     0, 0, 0, None, "no products were seen on such a day"))
    else:
        comparison.run_comparison(conn, pipeline_run_id, variant="full_coverage_days",
                                  replicates=replicates, full_coverage_only=True)
        tested, significant = _significant(prices)
        kept = sum(len(v) for v in prices.values())
        dropped = sum(len(v) for v in main_prices.values()) - kept
        outcomes.append(CheckOutcome(
            "full_coverage_days", "only days when every group reported", kept, tested, significant,
            shift(prices),
            f"{significant} of {tested} categories differ using only the {len(days)} day(s) on "
            f"which every operator group reported (main run: {main_significant} of {main_tested}); "
            f"{dropped} product(s) were never seen on such a day, and the rest were re-priced from "
            f"those days' observations alone"))

    prices = comparison.competitor_prices(conn, pipeline_run_id, only_stated_units=True)
    comparison.run_comparison(conn, pipeline_run_id, variant="stated_units_only",
                              replicates=replicates, only_stated_units=True)
    tested, significant = _significant(prices)
    outcomes.append(CheckOutcome(
        "stated_units_only", "only products whose price unit the shop stated",
        sum(len(v) for v in prices.values()), tested, significant, shift(prices),
        f"{significant} of {tested} categories differ when inferred price units are dropped"))
    return outcomes


def _midpoint(window_start: str, window_end: str) -> str:
    from datetime import date, timedelta
    start = date.fromisoformat(window_start)
    end = date.fromisoformat(window_end)
    return (start + timedelta(days=(end - start).days // 2)).isoformat()
