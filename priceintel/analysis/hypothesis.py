"""The testable statistical questions, their assumption checks and their effect sizes.

Two questions, both answered with the data this system collected:

**Q1 - answerable now.** *Within a category, do the four operator groups advertise the same price
level?* H0: the price distributions of the groups in that category are the same; H1: at least one
group's prices are systematically higher or lower. This is the question behind "which categories
warrant further investigation": a category where competitors agree closely is a thin market to argue
about, and one where they diverge is where a price position actually matters.

**Q2 - the approved hypothesis, pending Secret's export.** *Is Secret's median advertised price equal
to a competitor group's median in the same category?* H0: the percentage difference is zero. It is
tested by permutation once the owner's export is imported (ADR-007); until then it is recorded as
insufficient evidence rather than left out, so the report shows the state of the evidence.

**Why these methods.**

* *Kruskal-Wallis* for Q1: prices are strongly right-skewed and the groups have very different sizes,
  so a one-way ANOVA's normality and equal-variance assumptions do not hold. Kruskal-Wallis assumes
  only independent samples and ordinal data.
* *Permutation* for the pairwise comparisons and for Q2: it needs no distributional assumption at
  all - the null distribution is built by relabelling the data that was actually collected. With a
  median difference as the statistic, it tests exactly the quantity the report quotes.
* *Holm* correction across the categories tested, because testing five categories at 5% each would
  find a "difference" about a quarter of the time by chance alone.

**What is deliberately not claimed.** Kruskal-Wallis detects stochastic dominance, not a difference
in medians, unless the distributions have a similar shape; the shape check is recorded with every
test and the conclusion is worded accordingly. Nothing here establishes that equivalent bouquets are
priced differently: these are the observed assortments of four shops in one window.
"""
import json
from dataclasses import dataclass

import numpy as np
from scipy import stats

from priceintel.db import transaction

MIN_PER_GROUP = 10
PERMUTATIONS = 10_000
RANDOM_SEED = 20261109


@dataclass(frozen=True)
class TestResult:
    question: str
    scope: str
    method: str
    statistic: float | None
    p_value: float | None
    p_adjusted: float | None
    effect_name: str | None
    effect_size: float | None
    effect_ci_low: float | None
    effect_ci_high: float | None
    n_groups: int
    n_observations: int
    assumptions: str
    conclusion: str


def holm(p_values: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values, in the order given. Chosen over Bonferroni because it is
    uniformly more powerful and needs no extra assumption."""
    m = len(p_values)
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        value = (m - rank) * p_values[i]
        running = max(running, min(value, 1.0))   # enforce monotonicity
        adjusted[i] = running
    return adjusted


def probability_of_superiority(a: np.ndarray, b: np.ndarray) -> float:
    """P(a random product from `a` costs more than one from `b`), ties counted as a half.

    Reported instead of a rank-biserial correlation because it is the same information in words the
    owner can use: "about 7 times in 10, this shop's bouquet is the dearer one"."""
    comparisons = a[:, None] - b[None, :]
    return float((np.sum(comparisons > 0) + 0.5 * np.sum(comparisons == 0)) / comparisons.size)


def _shape_note(samples: list[np.ndarray]) -> str:
    """Kruskal-Wallis only speaks about medians when the distributions have a similar shape."""
    skews = [float(stats.skew(s)) for s in samples if len(s) > 2]
    spread = [float(stats.iqr(s) / np.median(s)) if np.median(s) else 0.0 for s in samples]
    similar = max(spread) - min(spread) < 0.5 if spread else False
    return (f"skewness {', '.join(f'{s:.1f}' for s in skews)}; "
            f"IQR/median {', '.join(f'{s:.2f}' for s in spread)}; "
            f"{'shapes comparable, so the test can be read as about medians' if similar else 'shapes differ, so the test is read as stochastic dominance, not a median difference'}")


def permutation_median_difference(a: np.ndarray, b: np.ndarray, *, permutations: int = PERMUTATIONS,
                                  seed: int = RANDOM_SEED) -> tuple[float, float]:
    """(observed median difference, two-sided p-value) under the null that the labels are
    exchangeable. No distributional assumption: the null is built from the collected data."""
    rng = np.random.default_rng(seed)
    observed = float(np.median(a) - np.median(b))
    pooled = np.concatenate([a, b])
    n_a = len(a)
    count = 0
    for _ in range(permutations):
        rng.shuffle(pooled)
        if abs(float(np.median(pooled[:n_a]) - np.median(pooled[n_a:]))) >= abs(observed):
            count += 1
    # Add-one smoothing: a p-value from a finite number of permutations is never exactly zero.
    return observed, (count + 1) / (permutations + 1)


def groups_differ_within_category(prices: dict[tuple[str, str], list[float]], *,
                                  min_per_group: int = MIN_PER_GROUP) -> list[TestResult]:
    """Q1, one test per category, with Holm correction across the categories tested."""
    question = ("Within a category, do the four operator groups advertise the same price level? "
                "H0: their price distributions are the same.")
    categories = sorted({c for c, _ in prices})
    raw: list[tuple[str, float, float, list[np.ndarray], list[str]]] = []
    results: list[TestResult] = []

    for category in categories:
        groups = sorted(g for c, g in prices if c == category)
        samples = [np.array(prices[(category, g)], dtype=float) for g in groups]
        usable = [(g, s) for g, s in zip(groups, samples) if len(s) >= min_per_group]
        if len(usable) < 2:
            results.append(TestResult(
                question, category, "kruskal_wallis", None, None, None, None, None, None, None,
                len(usable), int(sum(len(s) for _, s in usable)),
                f"needs at least two groups with {min_per_group} products; "
                f"{len(usable)} qualified",
                "insufficient evidence: not enough groups in this category"))
            continue
        names = [g for g, _ in usable]
        data = [s for _, s in usable]
        statistic, p_value = stats.kruskal(*data)
        # Epsilon-squared: the share of rank variance explained by the group, 0 to 1.
        n = sum(len(s) for s in data)
        epsilon_squared = float((statistic - len(data) + 1) / (n - len(data))) if n > len(data) else 0.0
        raw.append((category, float(statistic), float(p_value), data, names))

    adjusted = holm([p for _, _, p, _, _ in raw]) if raw else []
    for (category, statistic, p_value, data, names), p_adj in zip(raw, adjusted):
        n = int(sum(len(s) for s in data))
        epsilon_squared = float((statistic - len(data) + 1) / (n - len(data)))
        significant = p_adj < 0.05
        assumptions = (f"independent products (one price per distinct listing, mirrors excluded); "
                       f"group sizes {', '.join(f'{name}={len(s)}' for name, s in zip(names, data))}; "
                       + _shape_note(data))
        conclusion = (
            f"{'Reject' if significant else 'Do not reject'} H0 at 5% after Holm correction "
            f"(p={p_value:.4f}, adjusted {p_adj:.4f}). "
            + (f"The groups do not price this category alike; "
               f"{names[int(np.argmax([np.median(s) for s in data]))]} is the dearest and "
               f"{names[int(np.argmin([np.median(s) for s in data]))]} the cheapest by median."
               if significant else
               "No evidence that the groups price this category differently."))
        results.append(TestResult(
            question, category, "kruskal_wallis", statistic, p_value, p_adj,
            "epsilon_squared", epsilon_squared, None, None, len(data), n, assumptions, conclusion))
    return results


def pairwise_within_category(prices: dict[tuple[str, str], list[float]], category: str, *,
                             min_per_group: int = MIN_PER_GROUP,
                             permutations: int = PERMUTATIONS) -> list[TestResult]:
    """Which pair of groups differs, by a permutation test on the median difference."""
    question = (f"In {category}, does one operator group advertise higher prices than another? "
                f"H0: the median difference between the pair is zero.")
    groups = sorted(g for c, g in prices if c == category
                    and len(prices[(c, g)]) >= min_per_group)
    pairs, p_values = [], []
    for i, first in enumerate(groups):
        for second in groups[i + 1:]:
            a = np.array(prices[(category, first)], dtype=float)
            b = np.array(prices[(category, second)], dtype=float)
            difference, p_value = permutation_median_difference(a, b, permutations=permutations)
            pairs.append((first, second, a, b, difference))
            p_values.append(p_value)

    adjusted = holm(p_values) if p_values else []
    results = []
    for (first, second, a, b, difference), p_value, p_adj in zip(pairs, p_values, adjusted):
        superiority = probability_of_superiority(a, b)
        results.append(TestResult(
            question, f"{category}: {first} vs {second}", "permutation_median_difference",
            difference, p_value, p_adj, "probability_of_superiority", superiority, None, None,
            2, len(a) + len(b),
            f"exchangeability under H0; {first}={len(a)} products, {second}={len(b)} products; "
            f"{permutations:,} permutations",
            f"median difference {difference:,.0f} UZS "
            f"({'significant' if p_adj < 0.05 else 'not significant'} after Holm, "
            f"adjusted p={p_adj:.4f}); a {first} product is dearer than a {second} one "
            f"{superiority:.0%} of the time"))
    return results


def secret_versus_group(secret: list[float], competitor: list[float], category: str, group: str, *,
                        min_items: int = MIN_PER_GROUP,
                        permutations: int = PERMUTATIONS) -> TestResult:
    """Q2, the approved hypothesis. Reported as insufficient evidence until the export is imported."""
    question = (f"Is Secret's median advertised price equal to {group}'s in {category}? "
                f"H0: 100 x (Secret median / {group} median - 1) = 0.")
    if len(secret) < min_items or len(competitor) < min_items:
        return TestResult(
            question, f"{category}: SECRET vs {group}", "permutation_median_difference",
            None, None, None, None, None, None, None, 2, len(secret) + len(competitor),
            f"needs {min_items} items on each side; Secret={len(secret)}, {group}={len(competitor)}",
            "insufficient evidence: Secret's offers are imported from the owner's export after the "
            "collection window closes (ADR-007)")
    a, b = np.array(secret, dtype=float), np.array(competitor, dtype=float)
    difference, p_value = permutation_median_difference(a, b, permutations=permutations)
    pct = 100.0 * (float(np.median(a)) / float(np.median(b)) - 1.0)
    return TestResult(
        question, f"{category}: SECRET vs {group}", "permutation_median_difference", difference,
        p_value, p_value, "percentage_difference", pct, None, None, 2, len(a) + len(b),
        f"exchangeability under H0; Secret={len(a)} offers, {group}={len(b)} products; "
        f"{permutations:,} permutations",
        f"Secret's median is {pct:+.1f}% against {group} "
        f"({'significant' if p_value < 0.05 else 'not significant'} at 5%, p={p_value:.4f}). "
        f"This compares the observed assortments, not equivalent bouquets.")


def store(conn, pipeline_run_id: int, results: list[TestResult]) -> int:
    with transaction(conn):
        conn.execute("DELETE FROM hypothesis_tests WHERE pipeline_run_id = ?", (pipeline_run_id,))
        for r in results:
            conn.execute(
                "INSERT INTO hypothesis_tests (pipeline_run_id, question, scope, method, statistic,"
                " p_value, p_adjusted, effect_name, effect_size, effect_ci_low, effect_ci_high,"
                " n_groups, n_observations, assumptions, conclusion)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (pipeline_run_id, r.question, r.scope, r.method, r.statistic, r.p_value,
                 r.p_adjusted, r.effect_name, r.effect_size, r.effect_ci_low, r.effect_ci_high,
                 r.n_groups, r.n_observations, r.assumptions, r.conclusion))
    return len(results)
