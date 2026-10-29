# Analysis plan (final, for approval)

Version 1.0, 2026-10-29. Answers the Module Leader's points of 26/10/2026. Categories are fixed by
`config/category_rules.v1.json` (rules 1.1.0, tag `category-rules-v1.1.0`) **before** any analysis.

## 1. Primary data and reference data

| | Primary data (assessed) | Reference data |
|---|---|---|
| What | Competitor product listings and their dated price observations | Secret's own offers |
| How | My own scrapers, `python -m priceintel collect`, every 12 hours | One Telegram Desktop export by the owner, `python -m priceintel import-reference` (ADR-007) |
| Where | `market_intel.listings`, `market_intel.price_observations` | `market_intel.reference_offers` |
| Counts towards the primary-data target | Yes | **No** |
| Enters the models | Yes | **Never** (`tests/test_no_reference_in_models.py`) |

Four operator groups are collected, one domain each: `PROBUKET`, `UZFLORA`, `LOVEFLOWERS_NET`,
`KAMILAS`. Mirrors are registered and never crawled, so they cannot inflate any count
(`docs/compliance/source_groups.md`, migration 004, `tests/test_source_groups.py`).

## 2. Sampling plan

- **Window:** 28 days, starting the first Monday after the approval date. Secret's export is taken
  once, after the window closes, and covers it.
- **Cadence:** 08:00 and 20:00 Asia/Tashkent = **56 scheduled runs**. Target at least 50 completed
  runs. A *completed* run attempts every active group's catalogue pages and ends with a recorded
  status; a *successful* run has at least 80% of requested pages returning HTTP 200 and parsing;
  success rate = successful / scheduled, missed runs counting as failures (target 95%).
- **Units.** One competitor product = one distinct listing (`UNIQUE (shop_id, url)`), its window
  observations collapsed to one regular price (the median). One Secret offer = one distinct
  `offer_group_id`, dated by first publication; reposts (same normalised title and price within 14
  days) count once. Repeated observations are never counted as new products.
- **Minimum evidence for a displayed comparison:** at least **10 distinct Secret offers** in the
  category **and** at least **10 distinct products from that operator group** in the same category.
  Otherwise the cell reads "insufficient evidence" with both counts. This replaces the earlier
  "20 products across 3 groups", which could still leave an individual comparison with very few items.
- **Too few Secret offers.** Checked at Day 21 from the counts only. Categories whose Secret count is
  below 10 are merged by the count-only rule (the three bouquet categories first), before any price is
  looked at, and the merge is logged with the counts that triggered it. If a category is still below
  10 it is reported as insufficient evidence; the window is extended to Day 42 only if the timetable
  allows.

### Table 1 - distinct competitor products per category and operator group

Measured in the development crawl of **2026-10-29** (runs 3-6, `purpose = dev`, rules 1.1.0;
`python -m priceintel category-report --purpose dev`). These are the figures the plan is based on, not
a forecast.

| Category | KAMILAS | LOVEFLOWERS_NET | PROBUKET | UZFLORA | Total |
|---|---|---|---|---|---|
| roses_mono | 0 | 121 | 19 | 3 | 143 |
| mixed_bouquets | 0 | 1 | 0 | 0 | 1 |
| bouquets_unspecified | 8 | 63 | 35 | 94 | 200 |
| **bouquets, merged** | **8** | **185** | **54** | **97** | **344** |
| boxes_baskets | 0 | 136 | 5 | 0 | 141 |
| potted_plants | 0 | 8 | 1 | 8 | 17 |
| edible_sets | 0 | 4 | 0 | 12 | 16 |
| out_of_scope (excluded, counted) | 1 | 16 | 0 | 22 | 39 |
| unclassified (excluded, counted) | 5 | 5 | 4 | 15 | 29 |
| **All distinct products** | **14** | **354** | **64** | **154** | **586** |

A single pass already exceeds the 300-product target. Notes that follow from the table:

- `KAMILAS` publishes about 29 products and a price for only 7 of them (the others say the bouquet is
  "a reference for a future arrangement"); the rest are quarantined as `missing_price`. It will
  usually fall below the 10-product minimum, so most comparisons against it will read "insufficient
  evidence". It is kept because the operator is independent and the robustness checks use it.
- `boxes_baskets` has enough products in `LOVEFLOWERS_NET` only; `potted_plants` and `edible_sets`
  have fewer than 10 everywhere.

### Table 2 - distinct Secret offers per category

Estimated from the 123 channel posts observed during pre-approval development (4-17 October 2026,
`purpose = dev`, route since withdrawn - ADR-007), classified by rules 1.1.0, identical title and
price collapsed: **119 distinct offers in 14 days**, so about **240 per 28 days**.

| Category | 14 days observed | 28-day estimate |
|---|---|---|
| roses_mono | 25 | ~50 |
| mixed_bouquets | 3 | ~6 |
| bouquets_unspecified | 27 | ~54 |
| **bouquets, merged** | **55** | **~110** |
| boxes_baskets | 0 | 0 |
| potted_plants | 0 | 0 |
| edible_sets | 0 | 0 |
| unclassified (caption says nothing classifiable) | 64 | ~128 |

**Consequence, stated plainly:** only the merged bouquet category is expected to have 10 or more
Secret offers. So the plan expects to display bouquet comparisons against `LOVEFLOWERS_NET`,
`PROBUKET` and `UZFLORA`, and to report everything else as insufficient evidence. About half of
Secret's captions say nothing that identifies a product type; those offers are counted and excluded,
not guessed at.

## 3. Comparison, percentage and bootstrap

- **Estimand.** For each category *c* and operator group *g*:
  `D = 100 × (median(Secret price in c) / median(group g price in c) − 1)`, reported with the median
  difference in UZS. A difference in log prices is **never** reported as a percentage.
- **Prices.** Regular advertised prices (the old price where a sale is shown); current sale prices are
  a sensitivity check. Conditional promotions (codes, bundles, free-delivery conditions) are flags and
  excluded from the price. Delivery fees and free-delivery thresholds are recorded per shop with a
  date and reported descriptively, never added to a price. Listings that show only a starting price
  (`is_from_price`) are excluded from the main comparison and included in a sensitivity check.
- **Bootstrap.** B = 5,000 replicates per category. Whole products are resampled, so all repeated
  observations of one product stay together. In each replicate the Secret sample is drawn **once** and
  reused across every competitor comparison, so the pooled figure keeps their shared dependence; each
  group's products are resampled independently. 95% percentile intervals. No bootstrap over the four
  businesses: with four groups it would say nothing about the wider market.
- **Temporal uncertainty.** A 28-day window gives four weekly blocks, too few for a week-block
  bootstrap, so weekly medians are reported descriptively with that limitation stated.
- **Pooling.** Only displayed comparisons enter the pooled summary, as the unweighted mean of the
  per-group percentages, so the largest catalogue does not dominate.
- **Interpretation.** Results describe the price ranges of the selected assortments in the selected
  window. They do not show that equivalent bouquets are over- or under-priced, and they do not justify
  a particular price change. Differences may reflect bouquet size, composition or presentation.

## 4. Models

Competitor scraper data only, from `priceintel/analysis/model_data.py`.

| | |
|---|---|
| Baseline | category median, fitted on the training split only |
| Models | ridge regression; tree-based model |
| Unseen listings | grouped cross-validation, `group_key = listing_id`: every observation of a listing stays in one fold |
| Sensitivity | leave-one-operator-group-out |
| Future prices | chronological evaluation if enough price changes are observed; otherwise reported as too rare, explicitly |
| Preprocessing | fitted on training data only |
| Metrics | MAE in UZS, median absolute percentage error, and both by category |
| Claim | whether either model improves on the baseline, and why - the baseline winning is a valid result |

## 5. Robustness checks (at least three required)

1. Leave one operator group out, in turn.
2. Exclude the top and bottom 2.5% of prices per category.
3. First half vs second half of the window.
4. With and without listings that show only a starting price.
5. Category rules: re-run with the generic sweetness words removed from `edible_sets` (ADR-006).

## 6. LO evidence map

| Learning outcome | Evidence |
|---|---|
| LO1 - data-mining lifecycle | CRISP-DM record in the report Sections 1 and 6; ADR-001 to ADR-007 show decisions **and revisions** (the Telegram route withdrawn, the category rules corrected, the operator grouping); four checkpoint tags |
| LO2 - database solution | Two SQLite databases; migrations 001-006 with constraints, triggers and views; provenance from observation to HTTP request; quarantine (`rejected_records`); operator groups and mirror rule; `reference_offers` kept separate; five stakeholder queries; backup/restore evidence; ER diagram and critical evaluation in report Section 2 |
| LO5 - statistical analysis | This plan: sampling rules and minimum counts (§2), the percentage definition and bootstrap (§3), models with leakage controls (§4), robustness checks (§5); assumption checks and uncertainty in report Section 3; limits on interpretation stated with every result |
| Primary vs reference distinction | §1 of this plan, ADR-007, migration 005, `tests/test_no_reference_in_models.py` |
