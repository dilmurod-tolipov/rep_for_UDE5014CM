# Checkpoint 3 — Statistical Analysis and Decision Support (LO5)

## Submission fields

| Field | Value |
|---|---|
| Repository | https://github.com/dilmurod-tolipov/rep_for_UDE5014CM |
| Assessed branch | `main` |
| Tag | `cp3` |
| Full commit hash | `82b5f29b6e986fb3b32900f9dc4c0d8d1fed326d` |
| State reached | 2026-11-16 (Teaching Week 9), day 8 of the approved collection window |
| Submission route | No checkpoint form is published on the LMS; the Module Leader confirmed in writing (26 October 2026) that checkpoint records are submitted with the final report. |

## Independently executable component

```bash
python -m priceintel pipeline --purpose assessed     # cleaning, transformation, features, splits
python -m priceintel analyse  --purpose assessed     # figures, tests, comparison, models, robustness
```

Everything runs on **data this system collected**: `analyse` reads `analysis_products`, which the
pipeline builds from scraped competitor observations only. Secret's offers are reference data and
arrive with the owner's export after the window closes; no model ever sees them
(`tests/test_no_reference_in_models.py`).

## Value statement

This component enables **the owner of Secret** to **see which categories competitors disagree about,
and by how much, before deciding where to look at his own prices** by **testing whether the four
operator groups price a category alike, estimating the gaps with resampled intervals, and comparing
a baseline with two models on data the system collected itself**, resulting in **two categories
identified where the groups demonstrably do not price alike (bouquets, ε² = 0.26; roses and
mono-bouquets, ε² = 0.10, both Holm-adjusted p < 0.0001), and three where the evidence is too thin to
say anything — which is itself a finding, since it says where collecting more would pay**.

## What the analysis found, on 2026-11-16

Dataset: pipeline run on the assessed window, **2,066 products collected → 501 usable** (1,406
observations were starting prices, 298 products are priced per stem, 118 have no analysis category).

| Category | Groups with ≥10 products | Kruskal–Wallis | Holm-adjusted p | Effect (ε²) |
|---|---|---|---|---|
| bouquets_unspecified | PROBUKET (35), UZFLORA (94) | reject H0 | < 0.0001 | 0.263 |
| roses_mono | LOVEFLOWERS_NET (258), PROBUKET (19) | reject H0 | < 0.0001 | 0.104 |
| boxes_baskets, edible_sets, potted_plants | fewer than two | not tested | — | — |

Models, grouped cross-validation by listing (so no model is scored on a product it trained on):

| Model | MAE (UZS) | MdAPE (%) |
|---|---|---|
| category-median baseline | 602,248 | 58.0 |
| ridge | **404,458** | 35.4 |
| decision tree | 441,356 | **31.1** |

Both models improve on the baseline — ridge by about a third on MAE. That is the expected shape when
the operator group carries real information: the same category is priced very differently by
different shops, which is precisely what the hypothesis test found.

**The Secret comparison is not yet available.** All 13 category × group comparisons are stored as
`insufficient_evidence` with `n_secret_offers = 0`, because the owner's export is taken once after
the window closes (ADR-007). The machinery is built and tested; it reports the state of the evidence
rather than a blank page.

## Independent test specification

| | |
|---|---|
| **Purpose** | Prove that the analysis answers the approved questions reproducibly, on collected data, without leakage |
| **Start command** | `python -m priceintel init-db` then `python tools/load_snapshot.py data/snapshots/assessed-window --db data/analysis.db` |
| **Run** | `python -m priceintel pipeline --db data/analysis.db --purpose assessed` then `python -m priceintel analyse --db data/analysis.db --purpose assessed` |
| **Test command** | `python -m pytest -q` |
| **Acceptance criteria** | at least five labelled figures written; a hypothesis test per category with its assumptions and effect size recorded; bootstrap intervals reproducible from a fixed seed; three models scored on folds that keep every observation of a listing together; at least three robustness checks stored; all tests pass |
| **Actual result** | 6 figures; 20 hypothesis tests stored; 91 comparison rows across 8 variants; 3 model runs with 66 metrics; 8 robustness checks; **259 tests pass**. Reproduced from the committed snapshot rather than from a working database. |

## Methods, and why these ones

- **Kruskal–Wallis** for "do the groups price this category alike": prices are strongly right-skewed
  and group sizes differ by an order of magnitude, so ANOVA's assumptions do not hold.
- **Permutation tests** for the pairwise comparisons and for the Secret hypothesis: no distributional
  assumption at all, and the statistic is the median difference the report actually quotes.
- **Holm** across categories, because five tests at 5% would find a "difference" about a quarter of
  the time by chance.
- **Percentile bootstrap**, B = 5,000, resampling whole products, with the Secret sample drawn once
  per replicate and reused across that category's groups (ADR-008). Intervals describe the four
  sampled groups and this window — not the Tashkent market.
- **Effect sizes** beside every p-value: ε² for the group test, probability of superiority for the
  pairwise ones, the percentage difference for the Secret comparison.

## Robustness checks (8 stored)

Leave out each operator group in turn (4), exclude flagged outliers, first and second half of the
window, and only products whose price unit the shop stated.

The informative one: **dropping PROBUKET removes every significant result**, because without it no
category has two groups with ten or more usable products. The finding therefore depends on PROBUKET
being in the sample, and the report must say so. Dropping UZFLORA or LOVEFLOWERS_NET leaves it
standing. The medians themselves barely move under any check, which is what a median is for.

## Known limitations at this checkpoint

- Secret's side is pending; every Secret comparison is insufficient evidence until the export.
- `LOVEFLOWERS_NET` advertises a starting price ("от 550 000") on most bouquets, so only 2 of its
  bouquets are usable even though 1,841 of its products were collected. Its bouquet prices cannot be
  compared on this evidence; the starting prices are kept and counted as lower bounds.
- `KAMILAS` publishes prices for about 7 products and will not reach the minimum.
- The second half of the window is empty today, so that robustness check is pending by construction.
- Three assessed runs in 14 reached all four groups; the causes (robots timeouts, a site redesign)
  are fixed, and the shortfall against the approved 95% is reported rather than hidden.

## AI assistance in this period

Claude Code (Opus) wrote the analysis modules, the figures and the tests. Two of its own defects were
caught by running on real data: a zero median absolute deviation flagged eight identically priced
plants as outliers, and a pooled metric could not be stored because a STRICT table's key cannot be
NULL. A third was caught by a test it wrote: a permutation p-value of 0.047 from two identical
distributions, which was a lucky seed rather than a bug — the test was replaced with a calibration
check over 100 seeds. See `docs/ai-use-log.md`.
