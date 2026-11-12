# Checkpoint 2 — Database Design, Reliable Collection and Data Quality (LO2)

## Submission fields

| Field | Value |
|---|---|
| Repository | https://github.com/dilmurod-tolipov/rep_for_UDE5014CM |
| Assessed branch | `main` |
| Tag | `cp2` |
| Full commit hash | `96bf0c84442092086f3a19c2e3868f02e6ec525f` |
| State reached | 2026-11-13 (Teaching Week 8), five days into the approved collection window |
| Submission route | No checkpoint form is published on the LMS; the Module Leader confirmed in writing (26 October 2026) that checkpoint records are submitted with the final report. |

## Independently executable component

Continued genuine acquisition, with the data-management side the brief asks for at this stage:

- **Continued collection.** Twice a day, unattended, in GitHub Actions. The purpose is derived from
  the date, so only runs inside the approved window are assessed.
- **Schema and data validation.** STRICT tables, CHECK constraints, provenance triggers, append-only
  evidence tables, and a validator that quarantines every record it refuses with the rule that failed.
- **Duplicate and error handling.** `UNIQUE (listing_id, run_id)` makes a re-run idempotent;
  `UNIQUE (shop_id, url)` makes a product one product; mirrored domains cannot be collected at all
  (`ux_shops_one_active_domain_per_group`); `/en/` duplicate product pages are filtered at the parser.
- **Audit and provenance.** Every observation points at the HTTP request that produced it, which
  points at the run, which names the git commit, the host and whether the code was modified.
- **Data quality.** Nine recorded checks (`python -m priceintel quality`) stored in
  `data_quality_checks` with thresholds and status.
- **Stakeholder queries.** Five documented SQL files (`python -m priceintel query --list`).
- **Monitoring output.** The dashboard's overview and data-quality pages, and `v_run_coverage`.

## Value statement

This component enables **the owner of Secret** to **trust a price comparison enough to act on it**, by
**collecting from four competitors twice a day, refusing and recording anything that fails validation,
proving every price back to the request that fetched it, and reporting nine quality measures against
their thresholds**, resulting in **a dataset whose gaps are visible and counted — 154 quarantined
records and the five runs that lost an operator group are all on the record — instead of a spreadsheet
whose holes nobody can see**.

## Evidence of progress toward the approved data target

As of the snapshot of 2026-11-12 (`data/snapshots/assessed-window/`):

| | |
|---|---|
| Assessed runs | 8 |
| Distinct competitor products | **579** (target: 300) |
| Price observations | **2,501** across 5 collection days |
| HTTP requests logged | 408 |
| Records quarantined | 154, all `missing_price` from kamilas.uz |
| Duplicate `(listing, run)` pairs | **0** |

## Independent test specification

| | |
|---|---|
| **Purpose** | Prove that collection continues reliably, that invalid, duplicate and edge-case input is handled, and that quality and queries produce reproducible output |
| **Start command** | `python -m priceintel init-db` |
| **Run** | `python -m priceintel collect --all --purpose dev` (twice, to show idempotence) |
| **Quality** | `python -m priceintel quality --purpose assessed` |
| **Queries** | `python -m priceintel query 02_category_coverage --purpose assessed` |
| **Test command** | `python -m pytest -q` |
| **Acceptance criteria** | second run adds no duplicate observations; every refused record appears in `rejected_records` with a rule; all nine quality checks produce a measured value, a threshold and a status; each of the five queries runs and returns its documented columns; at least five cumulative tests pass (the brief's minimum for this stage) |
| **Actual result** | **195 tests pass**. Second run adds 0 duplicate observations. 154 records quarantined, all with rule `missing_price`. Quality on assessed data reports `products_collected` 579 against a 300 target, `duplicate_observations` 0 and `orphan_observations` 0. All five queries run; coverage shows LOVEFLOWERS_NET 354, UZFLORA 154, PROBUKET 64, KAMILAS 7 products. |

## Substantive change since Checkpoint 1

| Work item | Issue / record | Commit | Verification |
|---|---|---|---|
| Five stakeholder queries with a parameterised runner | — | `0200a0a` | 12 tests on a fixture with hand-computed medians |
| Nine recorded data-quality checks (migration 007) | — | `0200a0a` | 8 tests, including that a breached threshold is reported as a breach |
| Committed CSV data snapshots with manifest and SHA-256 | — | `0200a0a`, `a6d5249` | the assessed snapshot, rewritten twice a day by the workflow |
| Dashboard over both databases, six pages and a JSON API | — | `95c20e7` | 23 tests, one of which starts the server and fetches a page |
| Approval recorded; the four clarifications implemented | ADR-008 | `ecac792` | migrations 008–010, 19 tests |
| **Defect: a run that lost an operator group reported success** | ADR-008 §1, this record | `88b75d2` | migration 011 and 8 tests; the failing case is reproduced in `tests/test_run_coverage.py` |

## Correction evidence (the brief asks for failures to be recorded when they happen)

On 2026-11-13 an audit of the first days of assessed collection found that **five of the first seven
assessed runs collected nothing from `LOVEFLOWERS_NET`**, and one lost `KAMILAS` as well, because
those sites did not answer `robots.txt` within the 30-second timeout. Refusing to crawl a site whose
`robots.txt` cannot be read is correct and was kept. What was wrong was the measurement: the skipped
shop's pages were never *requested*, so the page success rate stayed at 100% and the run reported
`success`.

Corrected in `88b75d2`: runs record groups expected and reached, a run that loses a group is
`partial`, `robots.txt` is retried five times at a 60-second timeout, and the historical runs were
re-marked by migration 011 rather than left flattering. The consequence — that the approved 95%
success rate can no longer be reached, with a best case of about 89% — is reported rather than
hidden, in `docs/analysis_plan.md` and in the final report.

## Known limitations at this checkpoint

- `KAMILAS` will not reach the 10-product minimum: it publishes prices for about 7 products.
- Scheduled runs start several hours after their nominal times (GitHub queues scheduled workflows);
  each run's own `started_at` is what the analysis uses.
- Secret's reference offers are not imported yet: the owner's export is taken once, after the window
  closes on 6 December (ADR-007).
- No analysis yet — that is Checkpoint 3.

## AI assistance in this period

Claude Code (Opus) was used for the queries, the quality checks, the snapshot mechanism, the
dashboard, the approval clarifications and the run-coverage fix. `docs/ai-use-log.md` records what it
produced, the mistakes its own tests caught and how each was verified.
