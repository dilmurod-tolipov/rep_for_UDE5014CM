# Addendum sent to the Module Leader for the final approval decision — 29 October 2026

Draft prepared by the student with AI assistance (`docs/ai-use-log.md`). Every figure comes from the
development crawl of 2026-10-29 and can be reproduced with
`python -m priceintel category-report --purpose dev`.

---

**Subject:** UDE5014CM Assessment 2 — completed addendum (points 1–4) for the final decision

Dear Mr Bekov,

Thank you for the decision of 26 October. The addendum is below, numbered to match your points.
Everything in it is implemented and tested in the repository
(https://github.com/dilmurod-tolipov/rep_for_UDE5014CM, commit `426a206`); the figures come from a
development crawl on 29 October, not from estimates.

**1. Primary collection and the reference dataset.** Accepted. The assessed primary data is what my
own scrapers collect from the four operator groups. Secret's offers are a separate reference dataset
in their own tables (`reference_offers`, `reference_imports`), they do not count towards the
primary-data target, and they never enter model training, tuning or evaluation — enforced by one
function that builds every model matrix from scraped competitor rows only, with a test that imports
reference offers and proves they cannot appear there.

Since the import earns no primary-data credit, its frequency carries no assessment weight, so I have
replaced the weekly export with **one export after the collection window closes** (a second only if
the window is extended). This also removes the last part of the design that needed a human action on a
schedule. Each import records the file name, its SHA-256, the export date and the consent note, which
will cover the academic use and sharing of the prices with the assessors; only the post date, link,
price and a short title are stored, with contact lines stripped. The automatic reading of the channel
is gone from the code (it was still running on my 12-hourly schedule until 29 October, as `dev` runs
only), and the records it had produced are deleted by a numbered migration rather than by hand.

**2. Sampling plan.** Window: 28 days from the first Monday after approval; competitor runs at 08:00
and 20:00 Asia/Tashkent (56 scheduled runs; target ≥50 completed, ≥95% successful, where a successful
run has ≥80% of pages returning 200 and parsing).

Table 1 — distinct competitor products per category, development crawl of 29 October (586 products
in a single pass, already above the 300 target):

| Category | KAMILAS | LOVEFLOWERS_NET | PROBUKET | UZFLORA |
|---|---|---|---|---|
| roses and mono-bouquets | 0 | 121 | 19 | 3 |
| mixed bouquets | 0 | 1 | 0 | 0 |
| bouquets, composition not stated | 8 | 63 | 35 | 94 |
| **bouquets, merged** | **8** | **185** | **54** | **97** |
| boxes and baskets | 0 | 136 | 5 | 0 |
| potted plants | 0 | 8 | 1 | 8 |
| edible/berry sets | 0 | 4 | 0 | 12 |
| excluded (balloons, vases, cakes; unclassified) | 6 | 21 | 4 | 37 |

Table 2 — distinct Secret offers per category, estimated from the 123 channel posts observed during
pre-approval development (4–17 October, `dev`): 119 distinct offers in 14 days, so roughly 240 per 28
days; roses and mono-bouquets ~50, mixed ~6, bouquets with no stated composition ~54, and ~128 whose
caption identifies no product type at all. Boxes, plants and edible sets: none.

A comparison is displayed only with **≥10 distinct Secret offers and ≥10 distinct products from that
operator group** in the same category; otherwise the cell reads "insufficient evidence" with both
counts. On these figures I expect to display the merged bouquet category against LOVEFLOWERS_NET,
PROBUKET and UZFLORA, and to report the rest as insufficient evidence — KAMILAS publishes about 29
products and a price for only 7 of them. If a category falls below 10, the three bouquet categories
are merged by a count-only rule, before any price is examined, with the counts logged; the window
extends to Day 42 only if the timetable allows. Reposts of one offer (same normalised title and price
within 14 days) share an `offer_group_id` and count once, dated by first publication; older posts stay
dated reference material and are never presented as new offers or as current availability.

**3. Percentage and bootstrap.** The percentage is `100 × (Secret median price / competitor median
price − 1)`, reported with the median difference in UZS; log-price differences are never reported as
percentages. The bootstrap uses B = 5,000 replicates within each category over whole products, so
repeated observations of a product stay together, and in each replicate the Secret sample is drawn once
and reused across every competitor comparison, so the pooled figure keeps their shared dependence; each
group is resampled independently; 95% percentile intervals; no bootstrap over the four businesses. The
28-day window gives four weekly blocks, which is too few for a week-block bootstrap, so the temporal
check is reported descriptively with that limitation stated.

**4. Modelling.** Category-median baseline, ridge and tree models, competitor data only. Grouped
cross-validation keeps every observation of a listing in one fold, with leave-one-operator-group-out as
a sensitivity check; preprocessing and the baseline are fitted on training data only; metrics are MAE
in UZS and median absolute percentage error, both overall and by category. I evaluate whether either
model improves on the baseline and explain the result, including if the baseline wins. The sampling
rules and the primary/reference distinction are in the LO evidence map (`docs/analysis_plan.md`).

Also done since your decision: each source now carries an operator-group identifier and a mirror flag,
with the grouping evidence and dates in `docs/compliance/source_groups.md` and a test that no group can
be collected twice; the category rules are tagged (`category-rules-v1.1.0`) before any analysis.

No assessed data has been collected. May I please have the approval decision? I will record the date of
your email, keep it with the approved version, and cite both in the Checkpoint 1 evidence with the
commit hash.

Kind regards,
Dilmurod Tolipov
Student ID: 50000161
