# Checkpoint 1 — Data-Mining Lifecycle and Data Collection MVP (LO1, LO2)

## Submission fields

| Field | Value |
|---|---|
| Repository | https://github.com/dilmurod-tolipov/rep_for_UDE5014CM |
| Assessed branch | `main` |
| Tag | `cp1` |
| Full commit hash | `1cd776dccf36874c03a1b1302659cbaa27cdefe6` |
| State reached | 2026-11-03; first assessed collection from this commit 2026-11-09 00:15 Asia/Tashkent |
| Approval record | Approved by the Module Leader on 2026-11-03 by University email — transcript in `docs/emails/2026-11-03-approval-decision.md`, scope and window in `docs/approval/APPROVED-SCOPE.md` |
| Submission route | No checkpoint form is published on the LMS. The Module Leader confirmed in writing (email, 26 October 2026) that the assessment has one final submission in Teaching Week 12 and that **checkpoint records are submitted with the final report**. This record is that submission. |

### Why this commit and not an earlier one

The brief places Checkpoint 1 in Teaching Week 7 and requires evidence of a **new record collected,
saved and retrieved after approval**. Approval was recorded on 3 November 2026 and the Module Leader
set the assessed collection window to **9 November – 6 December 2026**, so no assessed record could
exist before 9 November. Collecting earlier, or relabelling development records as assessed data,
was explicitly forbidden by the same decision. `cp1` therefore marks the exact commit that was
running when the first assessed record was collected. Everything before it is development work,
flagged `purpose = dev` and excluded from the assessed dataset.

## Independently executable component

A competitor price collector that accepts new input, validates it, stores it with full provenance and
lets the new record be retrieved:

- four operator groups, one canonical domain each (ADR-001), mirrors registered and never crawled;
- `robots.txt` read and enforced before every crawl, with a per-host delay and an identifying user
  agent; every HTTP attempt logged with status, size, timing and content hash;
- parsed records validated and either stored or quarantined with the rule that failed;
- idempotent re-runs (`UNIQUE (listing_id, run_id)`), append-only evidence tables;
- assessed runs refused from modified code (`CHECK` on `scrape_runs`).

## Value statement

This component enables **the owner of Secret** to **see what four competing Tashkent flower shops are
charging today, without checking any website by hand** by **collecting, validating and storing public
catalogue prices twice a day with their source, time and collection run**, resulting in **a dated,
checkable price record that already holds 579 competitor products and 2,501 observations after four
days, where previously there was none**.

## Independent test specification

| | |
|---|---|
| **Purpose** | Prove that the system collects a new genuine record after approval, saves it with provenance and retrieves it |
| **Inputs** | The four approved competitor catalogues, live, over HTTPS |
| **Start command** | `python -m priceintel init-db` |
| **Collect** | `python -m priceintel collect --all --purpose dev` (an assessed run only inside the approved window, from committed code) |
| **Retrieve** | `python -m priceintel listings --limit 20` and `python -m priceintel runs` |
| **Test command** | `python -m pytest -q` |
| **Acceptance criteria** | a run row with a 40-character commit hash and `git_dirty = 0`; at least one new observation linked to a fetch, a run and a source URL; the record retrievable through the view; all tests pass |
| **Actual result** | Run 12, scheduled, `purpose = assessed`, started 2026-11-08T19:15:42Z (2026-11-09 00:15 Tashkent), commit `1cd776d…`, `git_dirty = 0`, 11/11 pages fetched and parsed, **218 observations saved, 0 rejected**. Example retrieved record: observation 4176, listing 362, "15 розовых роз в коробке", 1,300,578 UZS, currency label UZS, observed 2026-11-08T19:18:43Z. 187 tests passed at this commit. |

The run, its fetch log and its observations are in `data/snapshots/assessed-window/` with a manifest
giving the row counts and each file's SHA-256, so the result can be checked without re-running the
collector.

## Substantive change in this period

| Work item | Issue | Commit | Verification |
|---|---|---|---|
| Category rules, versioned and price-independent | — | `7db976a` (tag `category-rules-v1.0.0`) | 38 tests; rules file SHA-256 registered in the database |
| Telegram collection withdrawn; reference import built | [#9](https://github.com/dilmurod-tolipov/rep_for_UDE5014CM/issues/9) | `c75aee9`, `426a206` | 9 import tests + 4 leakage tests; migrations 005/006 delete the withdrawn data |
| Parsers for the three remaining operator groups | [#10](https://github.com/dilmurod-tolipov/rep_for_UDE5014CM/issues/10) | `426a206` | 9 parser tests against real page fragments; dev crawl of 586 products |
| Operator groups and mirror rule | [#11](https://github.com/dilmurod-tolipov/rep_for_UDE5014CM/issues/11) | `426a206` | 5 tests; the database refuses a second active domain per group |
| Approval clarifications (currency, variant, identity, calendar) | — | `ecac792` | migrations 008–010; 19 tests |
| Collector workflow repaired; assessed snapshots committed | — | `1cd776d` | the run above |

## Known limitations at this checkpoint

- Run 12 reached only two of the four groups: `loveflowers.uz` and `kamilas.uz` did not answer their
  `robots.txt` inside the timeout, so the collector correctly refused to crawl them — but the run
  still reported `success`. Found on 2026-11-13 and corrected in `88b75d2` (migration 011: a run that
  loses an operator group is `partial`; `robots.txt` retried five times at a 60 s timeout). The
  consequence for the approved 95% success rate is reported in `docs/analysis_plan.md`.
- `kamilas.uz` publishes a price for only about 7 of its 29 products; the rest are quarantined as
  `missing_price` and the group is expected to stay below the 10-product minimum.
- Scheduled runs start several hours after their nominal 08:00/20:00 Tashkent times because GitHub
  queues scheduled workflows; every run records its own `started_at`, which is what the analysis uses.
- No analysis yet: that is Checkpoint 3.

## AI assistance in this period

Claude Code (Opus) was used for the category rules, the three parsers, the reference importer, the
approval clarifications and this record. What was produced, what it got wrong and how it was checked
is in `docs/ai-use-log.md`; the student is responsible for every line and can modify it.
