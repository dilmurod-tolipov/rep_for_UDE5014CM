# Checkpoint evidence register

Required by the brief ("The report or repository must include the following checkpoint evidence
register"). The LMS publishes no checkpoint form; the Module Leader confirmed in writing on
26 October 2026 that the assessment has one final submission in Teaching Week 12 and that checkpoint
records are submitted with the final report. Each checkpoint below is a git tag, so the marker can
check out the exact commit and run that stage.

A commit cannot contain its own hash, so each checkpoint hash is written into this register by the
commit that immediately follows its tag. The tag is the authority: 1cd776dccf36874c03a1b1302659cbaa27cdefe6
and 35ba26068f1a61331d9fcd8f387037b02c4db638 return the hashes recorded below.

| Checkpoint | State reached and full commit hash | Operational component and substantive change | Tests and verifiable results |
|---|---|---|---|
| **1** — Data-Mining Lifecycle and Data Collection MVP | 2026-11-09 (first assessed run), tag `cp1`<br>`1cd776dccf36874c03a1b1302659cbaa27cdefe6` | Competitor price collector over four operator groups: robots.txt enforced, polite delays, every HTTP attempt logged, records validated or quarantined, idempotent re-runs, assessed runs refused from modified code. Since CP0: category rules, three new parsers, reference-offer import replacing the withdrawn Telegram collector, operator-group rule, the four approval clarifications. | 187 tests pass at this commit. Run 12, scheduled, `purpose = assessed`, 2026-11-08T19:15:42Z, `git_dirty = 0`: 11/11 pages, **218 observations saved, 0 rejected**. Retrieved example: observation 4176, "15 розовых роз в коробке", 1,300,578 UZS. Evidence: `data/snapshots/assessed-window/` with manifest and SHA-256 per file. |
| **2** — Database Design, Reliable Collection and Data Quality | 2026-11-13 (Teaching Week 8), tag `cp2`<br>`35ba26068f1a61331d9fcd8f387037b02c4db638` | Continued twice-daily collection; schema and data validation; duplicate and edge-case handling; audit and provenance on every row; nine recorded quality checks; five stakeholder queries; dashboard monitoring; committed CSV snapshots. | **195 tests pass**. 8 assessed runs, **579 distinct products** (target 300), **2,501 observations**, 408 logged requests, 154 quarantined (all `missing_price`), **0 duplicate (listing, run) pairs**. Defect found and corrected: runs that lost an operator group reported success (`88b75d2`, migration 011, 8 tests). |
| **3** — Statistical Analysis and Decision Support | 2026-11-16 (Teaching Week 9), tag `cp3`<br>`82b5f29b6e986fb3b32900f9dc4c0d8d1fed326d` | `python -m priceintel analyse`: six labelled figures, Kruskal–Wallis per category with Holm correction and effect sizes, pairwise permutation tests, percentile bootstrap (B = 5,000) on the approved percentage, category-median baseline against ridge and a decision tree under grouped cross-validation, eight robustness checks. Secret's side reports insufficient evidence until the channel export. | **259 tests pass**. On 501 usable products: bouquets ε² = 0.263 and roses ε² = 0.104, both Holm-adjusted p < 0.0001; ridge MAE 404,458 UZS against the baseline's 602,248; the tree's MdAPE 31.1% against 58.0%. Dropping PROBUKET removes every significant result, which the report states. Reproduced from the committed snapshot. |
| **4** — Integrated Data-Producing System | 2026-11-20 (Teaching Week 10), tag `cp4`<br>`7341057c4e00410c5504c1ff9962b1c582057186` | `python -m priceintel refresh` runs collection, classification, cleaning, analysis and figures in one command and prints the decision; the dashboard gains "What to look at", "Analysis" and "Models", so a new record reaches an updated decision-support output with no manual step. | **276 tests pass**, 14 end-to-end. The new-record test collects, reads the decision, lets a shop double its prices, collects again and asserts the decision moves. Live: 22 assessed runs, 2,571 products, 23,362 observations; the decision page names roses and mono-bouquets at 243% spread across 484 products. |

## Value statements

- **CP1:** This component enables the owner of Secret to see what four competing Tashkent flower shops
  are charging today, without checking any website by hand, by collecting, validating and storing
  public catalogue prices twice a day with their source, time and collection run, resulting in a
  dated, checkable price record that held 579 competitor products and 2,501 observations after four
  days, where previously there was none.
- **CP2:** This component enables the owner of Secret to trust a price comparison enough to act on it,
  by collecting from four competitors twice a day, refusing and recording anything that fails
  validation, proving every price back to the request that fetched it, and reporting nine quality
  measures against their thresholds, resulting in a dataset whose gaps are visible and counted —
  154 quarantined records and five runs that lost an operator group are all on the record.
- **CP3:** This component enables the owner of Secret to see which categories competitors disagree
  about, and by how much, before deciding where to look at his own prices, by testing whether the
  four operator groups price a category alike, estimating the gaps with resampled intervals, and
  comparing a baseline with two models on data the system collected itself, resulting in two
  categories where the groups demonstrably do not price alike and three where the evidence is too
  thin to say anything — which says where collecting more would pay.
- **CP4:** This component enables the owner of Secret to decide which category to examine first, and
  see the evidence behind that advice, without running anything himself, by collecting competitor
  prices twice a day and carrying them through cleaning, testing and modelling to a ranked decision
  page that updates with every collection, resulting in a standing answer to "where should I look?"
  — on 20 November, roses and mono-bouquets, where the dearest group's median is 243% above the
  cheapest across 484 products.

## Evidence chains

The brief asks for at least four complete chains: requirement, defect or decision → issue with
acceptance criteria → implementation commit → verification → closure.

| Requirement / defect / decision | Issue | Implementation | Verification | Closure |
|---|---|---|---|---|
| ADR-001: sites sharing a catalogue count as one competitor | [#1](https://github.com/dilmurod-tolipov/rep_for_UDE5014CM/issues/1), [#11](https://github.com/dilmurod-tolipov/rep_for_UDE5014CM/issues/11) | `fc9c5a0`, `426a206` (migration 004, `docs/compliance/source_groups.md`) | 5 tests in `tests/test_source_groups.py`; the database refuses a second active domain per group | Both issues closed with the commit and test result |
| Telegram collection withdrawn; Secret's offers become reference data (ADR-007) | [#7](https://github.com/dilmurod-tolipov/rep_for_UDE5014CM/issues/7) → [#9](https://github.com/dilmurod-tolipov/rep_for_UDE5014CM/issues/9) | `c75aee9` (stop the scheduled collector), `426a206` (migrations 005/006, importer) | 9 import tests + 4 leakage tests proving no reference row reaches a model matrix | #7 closed as superseded with a written reason; #9 closed with evidence |
| Only one parser existed, so Table 1 had one column | [#10](https://github.com/dilmurod-tolipov/rep_for_UDE5014CM/issues/10) | `426a206` (parsers for pro-buket, loveflowers, kamilas) | 9 parser tests against real page fragments; dev crawl of 586 products across four groups | Closed with the crawl figures; two parser defects recorded (loveflowers ajax grid, kamilas `/en/` duplicates) |
| Module Leader's four clarifications on approval | ADR-008 | `ecac792` (migrations 008–010, rules 1.2.2) | 19 tests; two defects caught by them (potted orchid read as a stem; "(за шт)" missed) | Implemented before assessed collection began |
| **Defect:** a run that lost an operator group reported success | ADR-008 §1, `docs/checkpoints/CP2.md` | `88b75d2` (migration 011, harder robots retry, honest run status) | 8 tests in `tests/test_run_coverage.py`, one reproducing the original defect; historical runs re-marked `partial` | Corrected five days into the window; the effect on the 95% target is reported, not hidden |
| **Defect:** the decision page could be set by a single product | — | `cp4` commit | `test_the_decision_output_obeys_the_minimum_evidence_rule` | Ranking by raw spread named potted plants at 3,948% from one product; the minimum-evidence rule now applies to the decision output too |
| **Defect:** a redesigned site returned 200 but parsed to nothing | — | `60949a5` | `tests/test_group_freshness.py`; the parser reads both layouts and 56 of 56 cards now validate | loveflowers.uz changed its theme on 13 November; the largest group contributed nothing to five assessed runs while every overall measure stayed green. A per-group freshness check now fails on the first run a source goes quiet |
| Approved proposal promised an operational core and dated delivery terms that were never built | ADR-009 | `sql/secret_shop/003_operational_core.sql`, `sql/market_intel/014_shop_delivery_terms.sql` | 40 tests in `tests/test_operational_core.py` and `tests/test_delivery_terms.py`; 316 pass | Built after cp4 with every fabricated row declared `is_synthetic` and enforced by triggers; `shop_delivery_terms` ships empty because inventing another business's fees would be fabrication. `product_matches` stays unbuilt, with the reason recorded |
| Module Leader's reply of 2026-11-26: measure O1 against all scheduled runs; check whether the comparisons survive restriction to full-coverage days | ADR-010 postscript | `priceintel/quality.py` (`scheduled_slot_completion`), `priceintel/analysis/comparison.py` (`full_coverage_only`), `robustness.py` ninth check | 7 tests in `tests/test_schedule_and_coverage.py`; 331 pass | O1 is reported as 23 of 34 scheduled slots (67.6%), counting one slot that never started; the comparisons are unchanged on the 14 full-coverage days, which the report states |
| **Defect:** scheduled collection silently failed for 11 days | — | `1cd776d` | The verification run of 2026-11-03: 49/49 pages, 579 observations | Found by auditing the Actions history; cause was deleted artifacts plus a restore step that could not tell "no artifact" from "download failed" |
