# Checkpoint 4 — Integrated Data-Producing System (LO1, LO2, LO5)

## Submission fields

| Field | Value |
|---|---|
| Repository | https://github.com/dilmurod-tolipov/rep_for_UDE5014CM |
| Assessed branch | `main` |
| Tag | `cp4` |
| Full commit hash | `7341057c4e00410c5504c1ff9962b1c582057186` |
| State reached | 2026-11-20 (Teaching Week 10), day 12 of the approved collection window |
| Note on the commit | The implementation landed in the commit above under the message "Record the cp4 commit hash in the checkpoint evidence", which does not describe it. A failed shell step broke the chain that should have committed the work under its own message, so everything was swept into the next commit, and the tag was briefly on an automated snapshot commit instead. The tag was corrected to this commit the same day. The history is not rewritten: what happened is recorded here rather than tidied away. |
| Submission route | No checkpoint form is published on the LMS; the Module Leader confirmed in writing (26 October 2026) that checkpoint records are submitted with the final report. |

## The end-to-end release

```bash
python -m priceintel refresh            # collect → classify → clean → analyse → decision
python -m priceintel dashboard          # read it at http://127.0.0.1:8000/
```

`refresh` runs the five stages in order and stops at the first that fails, so a half-updated
dashboard is never shown as current:

1. **collect** — the four operator groups, robots.txt obeyed, every request logged;
2. **classify** — categories and price units from the versioned rules file;
3. **pipeline** — cleaning and transformation, every decision counted;
4. **analyse** — hypothesis tests, the comparison with bootstrap intervals, three models;
5. **figures** — the six exploratory charts.

It ends by printing the decision the owner acts on, and the dashboard serves the same build: a new
page, **"What to look at"**, ranks the categories by how far apart the sampled shops are, with
**Analysis** and **Models** behind it for the evidence.

## Value statement

This component enables **the owner of Secret** to **decide which category to examine first, and see
the evidence behind that advice, without running anything himself** by **collecting competitor prices
twice a day and carrying them through cleaning, testing and modelling to a ranked decision page that
updates with every collection**, resulting in **a standing answer to "where should I look?" that was
previously unavailable: on 20 November it names roses and mono-bouquets, where the dearest group's
median is 243% above the cheapest across 484 products from two groups**.

## Independent test specification

| | |
|---|---|
| **Purpose** | Prove the system runs end to end, and that a new record reaches the decision output |
| **Start command** | `python -m priceintel init-db` |
| **Run** | `python -m priceintel refresh --purpose dev` then `python -m priceintel dashboard` |
| **Reproduce from saved data** | `python tools/load_snapshot.py data/snapshots/assessed-window --db data/replay.db` then `python -m priceintel refresh --db data/replay.db --no-collect` |
| **Test command** | `python -m pytest -q` |
| **Acceptance criteria** | collection stores records with provenance; the pipeline builds a dataset from them; the analysis runs on that dataset; every dashboard page serves the new build; **a new record changes the decision the dashboard shows**; a failed collection leaves the previous build in place; at least eight cumulative tests |
| **Actual result** | **276 tests pass**, 14 of them end-to-end. The new-record test collects, reads the decision, lets a shop double its prices, collects again, and asserts the decision moves — it does, and the dashboard page changes with it. Live data on 20 November: 22 assessed runs, 2,571 products, 23,362 observations. |

## Integration evidence

| Stage | Proof it is joined to the next |
|---|---|
| collection → database | every observation points at the HTTP request, the run and the commit that produced it |
| database → pipeline | `analysis_products` is built only from stored observations, with stage counts that reconcile |
| pipeline → analysis | every test, comparison and model run records the `pipeline_run_id` it used |
| analysis → application | the dashboard reads those tables; with no build it says how to make one rather than showing a blank page |
| application → decision | "What to look at" ranks categories by spread, under the same minimum-evidence rule as every other figure |

## A defect this checkpoint found

The first version of the decision page ranked categories by raw spread and told the owner to look at
**potted plants, 3,948%** — which was one PROBUKET plant at 1.8M UZS against loveflowers' 45,000. A
ranking a single product can set is not decision support. The page and the `refresh` headline now
compare only groups with at least ten usable products, and categories that cannot clear it are shown
as `insufficient_evidence` with the reason, rather than dropped. `test_the_decision_output_obeys_the_minimum_evidence_rule`
reproduces the original fault.

## Realised value, and what is still missing

**Realised.** The owner has a standing, dated answer to "where should I look?", refreshed twice a day
without anyone running anything, with the evidence one click away and every figure traceable to the
run and commit that produced it.

**Missing.**

- **Secret's own prices.** All 13 Secret comparisons read `insufficient_evidence`; the channel export
  is imported once after 6 December (ADR-007). Until then the dashboard compares competitors with
  each other and says so on the page.
- **KAMILAS** publishes prices for about 7 products and will not reach the minimum.
- **LOVEFLOWERS_NET** advertises "от" on most bouquets, so its bouquet prices cannot be compared;
  they are kept and counted as lower bounds.
- 11 of 22 assessed runs reached all four groups. The two causes — robots.txt timeouts and a site
  redesign — are fixed, and the last 11 runs are clean, but the approved 95% is out of reach and the
  report says so.

## AI assistance in this period

Claude Code (Opus) wrote the dashboard pages, the `refresh` command and the end-to-end tests. It
introduced the decision-ranking defect above and the empty-state page bug that its own tests caught
(`_no_analysis` was passed `None` instead of the database). See `docs/ai-use-log.md`.

> *Added 2026-11-25 (ADR-010): the export is produced by the student from Secret's public
> channel, not handed over by the owner. The timing and the reference-only treatment are
> unchanged.*

> *Added 2026-11-26: the heading "Realised value" above overstates it. The shop declined an earlier
> offer of a storefront and admin panel and does not use this system either, so the value described
> is **available, not realised**. The capability claims — that the chain runs end to end and
> produces a dated decision — are unaffected and are what the tests demonstrate. Report Section 5
> states this.*

> *Added 2026-11-26 (ADR-010): Secret's written confirmation could not be obtained, so its prices
> are omitted from the submission entirely and every Secret comparison stays
> `insufficient_evidence`. The competitor analysis is unaffected.*
