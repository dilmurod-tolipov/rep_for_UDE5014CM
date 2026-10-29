# Addendum sent to the Module Leader for the final approval decision — 29 October 2026

Draft prepared by the student with AI assistance (`docs/ai-use-log.md`). Every figure comes from the
development crawl of 2026-10-29 and can be reproduced with
`python -m priceintel category-report --purpose dev`. The email itself names no repository links,
commits, tags or file paths: those belong in the checkpoint evidence, not in the method description.

---

**Subject:** UDE5014CM Assessment 2 — completed addendum (points 1–4) for the final decision

Dear Mr Bekov,

Thank you for the decision of 26 October. The addendum is below, numbered to match your points. The
figures come from a development crawl I ran on 29 October, not from estimates.

**1. Primary collection and the reference dataset.** Accepted. The assessed primary data is what my
own scrapers collect from the four operator groups. Secret's offers are a separate reference dataset
in a table of their own, they do not count towards the primary-data target, and they never enter model
training, tuning or evaluation: every model matrix is built by a single function that reads scraped
competitor records only, and an automated test imports reference offers and then proves they cannot
appear in it.

Since the import earns no primary-data credit, its frequency carries no assessment weight, so I have
replaced the weekly export with **one export after the collection window closes** (a second only if
the window is extended). This also removes the last part of the design that needed a human action on a
schedule, so reproducing the work needs no Telegram account or credential of mine. Each import records
the file name, its SHA-256, the export date and the consent note, which will cover the academic use
and the sharing of the prices with the assessors; only the post date, link, price and a short title
are stored, with contact lines stripped. The automatic reading of the channel has been removed from my
code — it was still running on my 12-hourly schedule until 29 October, as development runs only — and
the records it had produced are deleted.

**2. Sampling plan.** Window: 28 days from the first Monday after approval; competitor runs at 08:00
and 20:00 Asia/Tashkent (56 scheduled runs; target at least 50 completed and 95% successful, where a
successful run has at least 80% of requested pages returning HTTP 200 and parsing).

Table 1 — distinct competitor products per category, development crawl of 29 October (586 products in
a single pass, already above the 300 target):

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
pre-approval development (4–17 October, development purpose): 119 distinct offers in 14 days, so
roughly 240 per 28 days; roses and mono-bouquets about 50, mixed about 6, bouquets with no stated
composition about 54, and about 128 whose caption identifies no product type at all. Boxes, plants and
edible sets: none.

A comparison is displayed only where there are **at least 10 distinct Secret offers and at least 10
distinct products from that operator group** in the same category; otherwise the cell reads
"insufficient evidence" with both counts. On these figures I expect to display the merged bouquet
category against LOVEFLOWERS_NET, PROBUKET and UZFLORA, and to report the rest as insufficient
evidence — KAMILAS publishes about 29 products and a price for only 7 of them. If a category falls
below 10, the three bouquet categories are merged by a count-only rule, before any price is examined,
and the counts that triggered the merge are recorded; the window extends to Day 42 only if the
timetable allows. Reposts of one offer (the same normalised title and price within 14 days) share one
offer identifier and count once, dated by first publication; older posts stay dated reference material
and are never presented as new offers or as evidence of current availability.

**3. Percentage and bootstrap.** The percentage is 100 × (Secret median price / competitor median
price − 1), reported with the median difference in UZS; a difference in log prices is never reported as
a percentage. The bootstrap uses B = 5,000 replicates within each category over whole products, so
repeated observations of a product stay together, and in each replicate the Secret sample is drawn once
and reused across every competitor comparison, so the pooled figure keeps their shared dependence; each
group is resampled independently; 95% percentile intervals; no bootstrap over the four businesses. The
28-day window gives four weekly blocks, too few for a week-block bootstrap, so the temporal check is
reported descriptively with that limitation stated.

**4. Modelling.** Category-median baseline, ridge and tree models, competitor data only. Grouped
cross-validation keeps every observation of one listing in the same fold, with
leave-one-operator-group-out as a sensitivity check; preprocessing and the baseline are fitted on
training data only; metrics are MAE in UZS and median absolute percentage error, both overall and by
category. I evaluate whether either model improves on the baseline and explain the result, including if
the baseline performs best. The final sampling rules and the primary/reference distinction are included
in the LO evidence map.

Also done since your decision: each source now carries an operator-group identifier and a mirror flag,
with the evidence for each grouping and the dates it was checked recorded in my compliance notes, and
an automated test that no group can be collected twice; the category rules are version-controlled and
tagged before any analysis.

No assessed data has been collected. May I please have the approval decision? I will record the date of
your email, keep it together with the approved version of the proposal, and cite both in my Checkpoint
1 evidence with its commit hash.

Kind regards,
Dilmurod Tolipov
Student ID: 50000161
