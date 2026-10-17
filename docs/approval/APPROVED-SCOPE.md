# Project scope (v2 proposal)

| Field | Value |
|---|---|
| Title | **Competitive Price Intelligence for a Tashkent Flower Shop** |
| Module | UDE5014CM Data Science for Developers, Assessment 2 |
| Student | Dilmurod Tolipov (50000161) |
| Module Leader | Sanjar Bekov |
| Approval route | University email |
| Approval status | **Awaiting the Module Leader's decision on v2** |
| Approval date / reference | <!-- FILL IN when Mr Bekov records "Approved": date and subject line --> |

## Approval history (from the email thread)

| Date (Asia/Tashkent) | From | Message |
|---|---|---|
| Wed 2026-09-30 11:32 | Student | v1: "Coursework approval request: Competitive Price Intelligence for a Tashkent Flower Shop" |
| Mon 2026-10-05 | Sanjar Bekov | Suitable in principle; **revisions required** (8 points) before formal approval |
| Sat 2026-10-17 21:40 | Student | v2: "Revised proposal for formal approval", answering all 8 points |
| — | Sanjar Bekov | *(decision pending)* |

Until approval is recorded, **no assessed primary data is collected** (as promised in v2):
the collector only runs with `purpose = dev`, and those rows are excluded from the analysis.

This page summarises the v2 proposal. The emails themselves are the authoritative record.
Later changes are recorded as ADRs in `docs/decisions/`.

## Problem, stakeholder, decision

- **Stakeholder:** the owner/manager of Secret (flowers, Secret Berries, Green Mood plants), Tashkent.
- **Problem:** the owner has no systematic evidence of how Secret's prices compare with competitors.
- **Decision supported:** price-position comparison against a sample of Tashkent competitors, and
  identifying products and categories that **warrant further investigation**. The system does not
  claim to establish profitability, demand, or the revenue effect of price changes.

## Unit and population

- **Unit:** one product listing observed on one shop website in one scrape run.
- **Population:** publicly listed bouquet, plant and gift products of the sampled Tashkent shops.
  Findings apply to the sampled shops and matched products only.

## Analytical questions

1. How do prices differ across shops (operators) and product categories?
2. **Hypothesis.** For each matched product group *g*: r_g = log(Secret price / median competitor price),
   using each listing's median regular price over the comparison window (Weeks 6–9).
   H0: median r_g = 0; H1: ≠ 0. Wilcoxon signed-rank test after a symmetry check; sign test as fallback.
   Effect sizes are the median % difference and the rank-biserial correlation, with bootstrap CIs.
   Sale prices are analysed separately.
3. What predicts a listing's price? Category-median baseline vs ridge regression vs a tree-based model.

## Objectives and success criteria

| # | Objective | Success criterion |
|---|---|---|
| O1 | Reliable automated collection | Runs every 12 h; ≥95% of scheduled runs successful (missed runs count as failures); a run succeeds if ≥80% of requested pages return HTTP 200 and parse |
| O2 | Enough evidence | By Week 9: ≥30 completed runs, ≥300 distinct competitor listings from ≥4 competitor sources (excluding Secret); distinct listings counted separately from repeated observations |
| O3 | Valid comparison | A category is analysable only with ≥20 distinct competitor listings from ≥3 sources and ≥5 comparable Secret products |
| O4 | Honest model evaluation | Evaluate whether either model improves on the baseline (MAE in UZS, median APE, per category) and explain the result |
| O5 | Decision support | The dashboard shows Secret's price position by category and lists products for review |

## Comparable products

Attributes: flower/plant type, stem count, size/height, packaging (paper, box, basket), add-ons,
promotion status, delivery terms per shop (dated). Matching requires the same type and packaging and
the same stem-count band (9–15, 21–35, 45+). Confidence labels: exact / probable / uncertain. Uncertain
matches are used only in a sensitivity analysis. Missing attributes are not imputed in the main analysis.

## Secret's prices

Fresh, dated observations written by our own system after approval (`source_type = own_system`,
`is_own_shop = 1`), kept apart from competitor observations and from any pre-existing reference catalogue
(marked `reference` and excluded from the primary comparison).

## Model evaluation

Unseen listings: grouped CV, with all observations of a listing in one fold. Future prices: chronological
or rolling-origin split if enough price changes happen (otherwise this is stated). Preprocessing and the
baseline are fitted on training folds only.

## Databases (SQLite)

- **market_intel** (priority): shops, shop_delivery_terms, scrape_runs, fetch_log, listings,
  price_observations, rejected_records, data_quality_checks; analysis tables listing_features,
  product_matches, dataset_splits, model_runs, model_metrics. Re-runs are idempotent through UNIQUE (listing_id, run_id).
- **secret_shop** (core): categories, products, product_attributes, product_price_history, clients,
  addresses, orders, order_items, payments, admin_users. Deferred: couriers, deliveries, status history, districts, audit log.
- The only link is `product_matches`; cross-database orphan checks run in the pipeline and the tests.

## Synthetic data and existing work

Synthetic clients/orders/payments are flagged `is_synthetic`, live in separate fixtures, and are never used in
the analysis. The pre-approval React demo is reused and recorded in `docs/baseline/EXISTING-WORK.md`.

## Evidence plan

≥8 meaningful automated tests; reproducible setup with pinned dependencies; dated data snapshots at each
checkpoint; four git-tagged checkpoints (`cp1`–`cp4`), each runnable from a clean checkout.

## LO evidence map

| LO | Evidence | Where assessed |
|---|---|---|
| LO1 Data-mining lifecycle | CRISP-DM decision log (`docs/decisions/`), objectives → collection → analysis → deployment, iteration records | Approval; CP1, CP4; Report §1, §4, §5; viva |
| LO2 Database solution | Two schemas, constraints, provenance, quality checks, 5 stakeholder queries, backup/restore, integrity tests | CP1, CP2, CP4; Report §2, §4, §5; viva |
| LO5 Statistical analysis | Hypothesis test, assumption checks, baseline + 2 models, grouped CV, uncertainty, robustness | CP3, CP4; Report §3, §4, §5; viva |
