# Checkpoint evidence register

Required by the brief ("The report or repository must include the following checkpoint evidence
register"). The LMS publishes no checkpoint form; the Module Leader confirmed in writing on
26 October 2026 that the assessment has one final submission in Teaching Week 12 and that checkpoint
records are submitted with the final report. Each checkpoint below is a git tag, so the marker can
check out the exact commit and run that stage.

A commit cannot contain its own hash, so each checkpoint hash is written into this register by the
commit that immediately follows its tag. The tag is the authority: 1cd776dccf36874c03a1b1302659cbaa27cdefe6
and 96bf0c84442092086f3a19c2e3868f02e6ec525f return the hashes recorded below.

| Checkpoint | State reached and full commit hash | Operational component and substantive change | Tests and verifiable results |
|---|---|---|---|
| **1** — Data-Mining Lifecycle and Data Collection MVP | 2026-11-09 (first assessed run), tag `cp1`<br>`1cd776dccf36874c03a1b1302659cbaa27cdefe6` | Competitor price collector over four operator groups: robots.txt enforced, polite delays, every HTTP attempt logged, records validated or quarantined, idempotent re-runs, assessed runs refused from modified code. Since CP0: category rules, three new parsers, reference-offer import replacing the withdrawn Telegram collector, operator-group rule, the four approval clarifications. | 187 tests pass at this commit. Run 12, scheduled, `purpose = assessed`, 2026-11-08T19:15:42Z, `git_dirty = 0`: 11/11 pages, **218 observations saved, 0 rejected**. Retrieved example: observation 4176, "15 розовых роз в коробке", 1,300,578 UZS. Evidence: `data/snapshots/assessed-window/` with manifest and SHA-256 per file. |
| **2** — Database Design, Reliable Collection and Data Quality | 2026-11-13 (Teaching Week 8), tag `cp2`<br>`96bf0c84442092086f3a19c2e3868f02e6ec525f` | Continued twice-daily collection; schema and data validation; duplicate and edge-case handling; audit and provenance on every row; nine recorded quality checks; five stakeholder queries; dashboard monitoring; committed CSV snapshots. | **195 tests pass**. 8 assessed runs, **579 distinct products** (target 300), **2,501 observations**, 408 logged requests, 154 quarantined (all `missing_price`), **0 duplicate (listing, run) pairs**. Defect found and corrected: runs that lost an operator group reported success (`88b75d2`, migration 011, 8 tests). |
| **3** — Statistical Analysis and Decision Support | Teaching Week 9 (planned), tag `cp3` | EDA, the testable hypothesis, bootstrap, baseline plus ridge and tree models, leakage-safe grouped validation, robustness checks — on data this system collected. | Planned: analysis tests, reproducible estimates with uncertainty, comparative result, stakeholder decision output. |
| **4** — Integrated Data-Producing System | Teaching Week 10 (planned), tag `cp4` | End-to-end release: collection, database, pipeline, analysis and dashboard integrated; a new record flows through to an updated decision-support output. | Planned: at least eight cumulative tests (already 195), end-to-end new-record test, clean-checkout evidence. |

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
- **CP3:** *(to be written at Checkpoint 3)*
- **CP4:** *(to be written at Checkpoint 4)*

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
| **Defect:** scheduled collection silently failed for 11 days | — | `1cd776d` | The verification run of 2026-11-03: 49/49 pages, 579 observations | Found by auditing the Actions history; cause was deleted artifacts plus a restore step that could not tell "no artifact" from "download failed" |
