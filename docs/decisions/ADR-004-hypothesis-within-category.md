# ADR-004: Hypothesis design — compare Secret with competitors within each category

- **Date:** 2026-10-17 (Week 6)
- **Status:** Proposed to the Module Leader by email (2026-10-17 23:20); awaiting his decision.
  Chosen by the student over Option B (manual annotation of photos).
- **Related:** v2 proposal "Statistical design"; ADR-003 (thin captions); approval feedback point 3

## Context

v2 defined the hypothesis on **matched product groups**: r_g = log(Secret price / median competitor
price), with matches requiring the same flower type, packaging and stem-count band. ADR-003 found that
Secret's posts name a flower type in about 30 of 123 captions and a stem count in none, so most Secret
products cannot be matched under that rule.

## Decision

### Primary analysis: within-category comparison of price levels

- **Unit:** one listing (a competitor product page, or one Secret post), summarised as its **median
  regular price over the comparison window**. Repeated observations of the same listing are collapsed
  first, so they are not counted as independent products (feedback point 3).
- **Groups:** our own categories (bouquets; roses and mono-bouquets; boxes and baskets; plants; edible
  sets). Competitor site categories and Secret captions are mapped to them by documented rules in the
  pipeline. A category is analysed only if it has >= 20 competitor listings from >= 3 operators and
  >= 5 Secret listings (v2 coverage rule).
- **Estimand:** the difference in **median log price**, Δ_c = median(log p_Secret) − median(log p_comp),
  reported as a percentage, exp(Δ_c) − 1. This compares medians directly, not "distributions", which
  answers the feedback that Mann–Whitney is not automatically a test of medians.
- **Hypotheses:** H0: Δ_c = 0 (Secret's median price equals the sampled competitors' median in category c);
  H1: Δ_c ≠ 0. Also a pooled estimate across categories.
- **Uncertainty and test:**
  - 95% CI for Δ_c by a **stratified bootstrap**: listings are resampled within each operator (and
    within Secret), keeping each operator's share fixed. Resampling only 4 competitor operators as
    clusters would give too few distinct resamples to be reliable, so operator-level dependence is
    handled in the robustness checks instead.
  - p-value by a **permutation test** of Δ_c (labels Secret/competitor permuted within category).
  - Holm correction across categories.
- **Effect sizes:** the median % difference with its CI, and the probability of superiority
  P(p_Secret > p_comp) (equivalent to the rank-biserial correlation), so the size of the gap is reported
  alongside the p-value.

### Secondary analysis: flower-type matches

For Secret posts whose caption names a flower type, r_g = log(Secret price / median price of competitor
listings with the same flower type and category). Matches are labelled **probable** (type known, size and
stem count unknown). Wilcoxon signed-rank on r_g if there are at least 6 matched groups (with n <= 5 no
two-sided p-value can be below 0.05), otherwise descriptive results only.

### Robustness checks (at least three required by the brief)

1. **Leave one operator out:** recompute Δ_c without each competitor operator (operator dependence).
2. **Outliers:** exclude the top and bottom 2.5% of log prices per category.
3. **Time window:** first half vs second half of the comparison window.
4. **uzflora currency effect** (issue #8): with and without uzflora.
5. **"From" prices:** with and without listings that only show a starting price.

## Consequences

- Answers analytical question 2 as "how does Secret's price level compare with the sampled competitors
  in each category", not "is Secret more expensive for the same bouquet". The report must say so, and
  must not claim like-for-like price differences from the primary analysis.
- Findings apply only to the sampled shops, categories and window (not the whole Tashkent market).
- The model comparison (baseline vs ridge vs tree, analytical question 3) is unaffected.
- If the Module Leader prefers Option B, the matched design can be restored by filling
  `secret_shop.product_attributes` with `method = 'manual'` annotations; the schema already supports it.
