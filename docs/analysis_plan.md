# Analysis plan (final, for approval)

Version 2.0, 2026-11-03, after the **approval decision of 3 November 2026** and its four
clarifications (ADR-008). Categories and price-unit rules are fixed by
`config/category_rules.v1.json` (rules 1.2.2) **before** any analysis.

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

## 2. Sampling plan (approved)

| | |
|---|---|
| Collection window | **9 November – 6 December 2026** (28 days), set by the Module Leader |
| Cadence | 08:00 and 20:00 Asia/Tashkent = **56 scheduled runs** |
| Success criterion | a successful run fetches and parses at least 80% of requested pages; the target is **at least 54 of the 56 scheduled runs (95%)**, with missed runs counted as failures |
| Product target | at least 300 distinct competitor products |
| Secret's offers | one export by the owner after the window closes (ADR-007) |
| Extension | none. A 42-day window would end on 20 December, after the 14 December deadline |

The workflow derives the purpose from the date, so nothing collected outside the window can become
assessed data.

### Units, and what counts once

- **A competitor product** is one distinct listing. Its summary is the **median of its observations
  in the window**, so a product seen 56 times contributes exactly as much as one seen once.
- **A Secret offer** is one distinct caption, dated by first publication, summarised by the median of
  the prices it was posted at. A repost is the same offer however long the gap and whatever the
  price; a price change makes the match `uncertain`, not a new offer (ADR-008).
- **Per-stem listings are not assortment prices.** A listing priced by the stem is excluded from
  category medians and reported separately.

### Table 1 — competitor products, three counts

Measured in the development crawl of **2026-10-29** (runs 3–6, `purpose = dev`, rules 1.2.2;
`python -m priceintel category-report --purpose dev`). "Usable" means eligible **and** priced for a
whole item or a stated bundle.

| Operator group | Collected | Eligible | **Usable** |
|---|---|---|---|
| KAMILAS | 14 | 8 | **8** |
| LOVEFLOWERS_NET | 354 | 333 | **223** |
| PROBUKET | 64 | 60 | **60** |
| UZFLORA | 154 | 117 | **114** |
| **Total** | **586** | **518** | **405** |

Usable products per category and group:

| Category | KAMILAS | LOVEFLOWERS_NET | PROBUKET | UZFLORA |
|---|---|---|---|---|
| roses_mono | 0 | 11 | 19 | 0 |
| mixed_bouquets | 0 | 1 | 0 | 0 |
| bouquets_unspecified | 8 | 63 | 35 | 94 |
| **bouquets, merged** | **8** | **75** | **54** | **94** |
| boxes_baskets | 0 | 136 | 5 | 0 |
| potted_plants | 0 | 8 | 1 | 8 |
| edible_sets | 0 | 4 | 0 | 12 |

The per-stem rule changes the headline: `roses_mono` for LOVEFLOWERS_NET falls from 121 listings to
**11** once single stems are removed, because most of that section is sold by the stem. The merged
bouquet category remains the only one with enough on the competitor side everywhere except KAMILAS.

### Table 2 — Secret's offers: observed and projected

| | Observed, 14 days (4–17 Oct 2026, `dev`) | Projected, 28 days |
|---|---|---|
| roses_mono | 25 | ~50 |
| mixed_bouquets | 3 | ~6 |
| bouquets_unspecified | 27 | ~54 |
| **bouquets, merged** | **55** | **~110** |
| boxes_baskets | 0 | 0 |
| potted_plants | 0 | 0 |
| edible_sets | 0 | 0 |
| unclassified (excluded from every comparison) | 64 | ~128 |
| **All distinct offers** | **119** | **~238** |

The observed column is a measurement; the projected column is a projection from it and is labelled as
one everywhere it appears. Unclassified offers are counted and excluded, never assigned to a
category.

### Minimum evidence, and what happens when it is not met

A comparison is displayed only with **at least 10 distinct Secret offers and at least 10 usable
products from that operator group** in the same category. Otherwise the cell reads "insufficient
evidence" with both counts. If a category falls short, the three bouquet categories merge by a
count-only rule, before any price is examined, with the counts that triggered the merge recorded.
There is no window extension; a category that is still short is reported as insufficient evidence.

On these figures, the expected displayed comparisons are the merged bouquet category against
LOVEFLOWERS_NET, PROBUKET and UZFLORA, with KAMILAS short of 10 usable products.

## 3. Comparison, percentage and bootstrap

- **Estimand.** For each category *c* and operator group *g*:
  `D = 100 × (median(Secret price in c) / median(group g price in c) − 1)`, reported with the median
  difference in UZS. A difference in log prices is **never** reported as a percentage.
- **Price selection.** Only a price the shop publishes in UZS; the project never converts a currency
  (ADR-008), the currency label is stored on every observation, and a database trigger refuses
  anything else. Regular advertised prices (the old price where a sale is shown); current sale prices
  are a sensitivity check. Conditional promotions (codes, bundles, free-delivery conditions) are flags and
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
- **Pooling and weighting.** Per-group comparisons are the primary output. Only displayed
  comparisons enter the pooled summary, as the **unweighted mean of the per-group percentages**, so
  LOVEFLOWERS_NET (223 usable products) does not outweigh KAMILAS (8). The weighting is stated beside
  every pooled figure.
- **Interpretation.** Results are comparisons of the **observed assortments** of the sampled shops in
  the selected window. Bootstrap intervals describe uncertainty within the four sampled operator
  groups and the 28-day window; they are not intervals for the Tashkent market. They do not show that equivalent bouquets are over- or under-priced, and they do not justify
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
6. Exclude reference offers whose repost match is `uncertain` (ADR-008).
7. Exclude listings whose price unit was `inferred` rather than stated by the shop.

## 6. LO evidence map

| Learning outcome | Evidence |
|---|---|
| LO1 - data-mining lifecycle | CRISP-DM record in the report Sections 1 and 6; ADR-001 to ADR-007 show decisions **and revisions** (the Telegram route withdrawn, the category rules corrected, the operator grouping); four checkpoint tags |
| LO2 - database solution | Two SQLite databases; migrations 001-006 with constraints, triggers and views; provenance from observation to HTTP request; quarantine (`rejected_records`); operator groups and mirror rule; `reference_offers` kept separate; five stakeholder queries; backup/restore evidence; ER diagram and critical evaluation in report Section 2 |
| LO5 - statistical analysis | This plan: sampling rules and minimum counts (§2), the percentage definition and bootstrap (§3), models with leakage controls (§4), robustness checks (§5); assumption checks and uncertainty in report Section 3; limits on interpretation stated with every result |
| Primary vs reference distinction | §1 of this plan, ADR-007, migration 005, `tests/test_no_reference_in_models.py` |
