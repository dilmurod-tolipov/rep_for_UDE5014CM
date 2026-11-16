"""The statistical methods, checked against cases whose answer is known in advance.

A test that only runs the code proves nothing about a p-value. Each test here either uses data
constructed so that the right answer is known, or checks a property the method must have (a p-value
near 1 when the groups are identical, monotone Holm adjustment, a probability of superiority of 1
when one sample is entirely above the other)."""
import numpy as np
import pytest

from priceintel.analysis.hypothesis import (
    groups_differ_within_category,
    holm,
    pairwise_within_category,
    permutation_median_difference,
    probability_of_superiority,
    secret_versus_group,
    store,
)
from tests.conftest import add_run


# ---------------------------------------------------------------------------
# Multiple testing
# ---------------------------------------------------------------------------

def test_holm_matches_the_textbook_example():
    # Holm: sort ascending, multiply by (m - rank), enforce monotonicity.
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_holm_never_decreases_and_never_exceeds_one():
    adjusted = holm([0.2, 0.3, 0.9, 0.95])
    assert adjusted == sorted(adjusted)
    assert all(0 <= p <= 1 for p in adjusted)


def test_holm_leaves_a_single_test_alone():
    assert holm([0.042]) == pytest.approx([0.042])


# ---------------------------------------------------------------------------
# Effect size
# ---------------------------------------------------------------------------

def test_probability_of_superiority_is_one_when_a_sample_is_entirely_dearer():
    a, b = np.array([100.0, 200.0, 300.0]), np.array([10.0, 20.0])
    assert probability_of_superiority(a, b) == 1.0


def test_probability_of_superiority_is_a_half_for_identical_samples():
    values = np.array([1.0, 2.0, 3.0])
    assert probability_of_superiority(values, values) == 0.5


# ---------------------------------------------------------------------------
# Permutation test
# ---------------------------------------------------------------------------

def test_the_permutation_test_is_calibrated_under_the_null():
    """The property that matters, rather than one lucky seed: when both samples come from the same
    distribution, a 5% test must reject about 5% of the time. One seed proves nothing - the first
    version of this test used seed 7 and got p = 0.047 from two identical distributions, which is
    exactly what a correct test does one time in twenty."""
    rejections = 0
    trials = 100
    for seed in range(trials):
        rng = np.random.default_rng(seed)
        a, b = rng.normal(500_000, 50_000, 30), rng.normal(500_000, 50_000, 30)
        _, p_value = permutation_median_difference(a, b, permutations=300, seed=seed)
        rejections += p_value < 0.05
    assert rejections <= 13, (
        f"{rejections} of {trials} false positives at the 5% level: the test is not calibrated")


def test_permutation_finds_a_difference_that_is_really_there():
    rng = np.random.default_rng(7)
    a = rng.normal(900_000, 50_000, 40)
    b = rng.normal(400_000, 50_000, 40)
    difference, p_value = permutation_median_difference(a, b, permutations=2_000)
    assert difference > 400_000
    assert p_value < 0.01


def test_a_permutation_p_value_is_never_exactly_zero():
    """With a finite number of permutations, 0 would be a claim the method cannot make."""
    a, b = np.array([1e6] * 20), np.array([1.0] * 20)
    _, p_value = permutation_median_difference(a, b, permutations=200)
    assert 0 < p_value <= 1


def test_the_permutation_test_is_reproducible():
    a, b = np.array([1.0, 5.0, 9.0, 2.0] * 6), np.array([3.0, 4.0, 8.0, 2.0] * 6)
    first = permutation_median_difference(a, b, permutations=500, seed=11)
    second = permutation_median_difference(a, b, permutations=500, seed=11)
    assert first == second


# ---------------------------------------------------------------------------
# Q1: do the groups price a category alike?
# ---------------------------------------------------------------------------

def prices_for(groups: dict[str, list[float]], category="bouquets_unspecified"):
    return {(category, g): v for g, v in groups.items()}


def test_identical_groups_do_not_reject_the_null():
    rng = np.random.default_rng(3)
    base = list(rng.normal(500_000, 80_000, 30))
    results = groups_differ_within_category(prices_for({
        "UZFLORA": base, "PROBUKET": list(rng.normal(500_000, 80_000, 30))}))
    test = next(r for r in results if r.p_value is not None)
    assert test.p_adjusted > 0.05
    assert "Do not reject" in test.conclusion


def test_clearly_different_groups_reject_the_null_and_name_the_dearest():
    rng = np.random.default_rng(3)
    results = groups_differ_within_category(prices_for({
        "UZFLORA": list(rng.normal(400_000, 40_000, 30)),
        "PROBUKET": list(rng.normal(1_500_000, 100_000, 30))}))
    test = next(r for r in results if r.p_value is not None)
    assert test.p_adjusted < 0.01
    assert "Reject" in test.conclusion and "PROBUKET is the dearest" in test.conclusion
    assert test.effect_name == "epsilon_squared" and 0 <= test.effect_size <= 1


def test_a_category_with_one_usable_group_reports_insufficient_evidence():
    results = groups_differ_within_category(prices_for({
        "UZFLORA": [100_000.0] * 20, "KAMILAS": [120_000.0] * 3}))
    test = results[0]
    assert test.p_value is None and "insufficient evidence" in test.conclusion


def test_the_assumption_check_is_recorded_with_every_test():
    rng = np.random.default_rng(5)
    results = groups_differ_within_category(prices_for({
        "UZFLORA": list(rng.normal(400_000, 40_000, 30)),
        "PROBUKET": list(rng.lognormal(13.5, 0.8, 30))}))
    test = next(r for r in results if r.p_value is not None)
    assert "skewness" in test.assumptions and "IQR/median" in test.assumptions
    assert "independent products" in test.assumptions
    # Different shapes must change how the result is worded.
    assert ("stochastic dominance" in test.assumptions
            or "can be read as about medians" in test.assumptions)


def test_pairwise_tests_name_the_pair_and_carry_an_effect_size():
    rng = np.random.default_rng(9)
    prices = prices_for({"UZFLORA": list(rng.normal(400_000, 30_000, 25)),
                         "PROBUKET": list(rng.normal(1_200_000, 60_000, 25))})
    results = pairwise_within_category(prices, "bouquets_unspecified", permutations=500)
    assert len(results) == 1
    result = results[0]
    assert "PROBUKET" in result.scope and "UZFLORA" in result.scope
    assert result.effect_name == "probability_of_superiority"
    assert result.p_adjusted < 0.05


# ---------------------------------------------------------------------------
# Q2: Secret against a group (pending the owner's export)
# ---------------------------------------------------------------------------

def test_secret_comparison_reports_insufficient_evidence_until_the_export_arrives():
    result = secret_versus_group([], [100_000.0] * 30, "bouquets_unspecified", "UZFLORA")
    assert result.p_value is None
    assert "insufficient evidence" in result.conclusion
    assert "owner's export" in result.conclusion


def test_secret_comparison_reports_a_percentage_once_both_sides_have_enough():
    secret = [600_000.0] * 12
    competitor = [500_000.0] * 20
    result = secret_versus_group(secret, competitor, "bouquets_unspecified", "UZFLORA",
                                 permutations=300)
    assert result.effect_name == "percentage_difference"
    assert result.effect_size == pytest.approx(20.0)      # 600k vs 500k
    assert "observed assortments" in result.conclusion


def test_results_are_stored_with_their_assumptions_and_conclusion(market_db):
    """A stored test must carry enough to be read a month later: the question, what was assumed,
    the effect size and the conclusion in words."""
    from priceintel import config
    from priceintel.analysis.categories import load_rules, register_rules
    rules = load_rules(config.CATEGORY_RULES_FILE)
    register_rules(market_db, rules)
    pipeline_run_id = market_db.execute(
        "INSERT INTO pipeline_runs (pipeline_version, purpose, window_start, window_end,"
        " rules_version, git_commit, git_dirty) VALUES ('1.0.0', 'test', '2026-11-09',"
        " '2026-12-06', ?, 'unknown', 0) RETURNING pipeline_run_id",
        (rules.version,)).fetchone()[0]

    rng = np.random.default_rng(1)
    results = groups_differ_within_category(prices_for({
        "UZFLORA": list(rng.normal(400_000, 40_000, 30)),
        "PROBUKET": list(rng.normal(900_000, 40_000, 30))}))
    assert store(market_db, pipeline_run_id, results) == len(results)

    row = market_db.execute("SELECT * FROM hypothesis_tests").fetchone()
    assert row["method"] == "kruskal_wallis"
    assert row["question"].startswith("Within a category")
    assert "independent products" in row["assumptions"]
    assert row["effect_name"] == "epsilon_squared" and row["effect_size"] is not None
    assert 0 <= row["p_adjusted"] <= 1
    assert "Reject" in row["conclusion"]
