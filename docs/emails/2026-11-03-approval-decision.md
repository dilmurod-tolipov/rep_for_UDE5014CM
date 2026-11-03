# Approval decision — Sanjar Bekov, 3 November 2026

Received by University email. Kept here as the written approval record required by the brief
("Keep the written approval record and identify it in your Checkpoint 1 evidence"). The original
email in Outlook is the authoritative copy; this is a verbatim transcript.

---

Dear Dilmurod,

Thank you. Approved.

The revised separation of primary competitor data from Secret's reference offers, together with the
grouped modelling and revised bootstrap procedure, addresses the main concerns. Approval covers the
four operator groups and the reference-only arrangement described.

Please incorporate these clarifications during implementation:

1. **Calendar.** With approval recorded this week, your 28-day collection window is 9 November–6
   December 2026. A 42-day window would end on 20 December, so remove that extension from the current
   plan. The submission deadline remains 14 December 2026.
2. **Feasibility figures.** Table 1 contains 586 products in total, including 68 exclusions, leaving
   518 in eligible categories before missing-price and other quality checks. Report the usable, priced
   counts separately. For Secret, distinguish the 119 observed offers from the approximately 238
   projected offers over 28 days. Unclassified offers must remain excluded from category comparisons.
   Also specify the success-rate denominator: 95% of 56 scheduled runs requires at least 54 successful
   runs.
3. **Comparable prices.** Preserve currency, product variant, discount status and availability.
   Uzflora displays USD prices, while PROBUKET displays multiple currencies and bouquet sizes, so your
   UZS comparisons must use an explicit, reproducible price-selection and conversion rule. Describe
   merged-bouquet results as comparisons of the observed assortments; they do not establish price
   differences between equivalent products.
4. **Identity and weighting.** An identifiable offer should not become a new independent item solely
   because its price changes or 14 days pass. Check reposts across the full window and document
   uncertain matches. Specify how repeated prices contribute to each product's summary and how
   operator groups are weighted in the pooled comparison. Interpret bootstrap intervals within the
   sampled operators and collection window.

Retain the consent evidence, reference-data exclusion test, training-only preprocessing and separation
of tuning from evaluation. The final assessed system must reproduce the analysis from its saved data
without your Telegram account or credentials.

You may proceed with implementation and begin assessed collection within the approved window. Keep
this decision with the approved proposal and its repository version.

Kind regards,
Sanjar Bekov

---

## What this changes in the project

| Clarification | Where it is implemented |
|---|---|
| 1. Calendar | `.github/workflows/collect.yml` (the window decides the purpose), `docs/analysis_plan.md`; the Day-42 extension is removed |
| 2. Feasibility figures | `docs/analysis_plan.md` Tables 1 and 2, with usable priced counts separate from eligible counts; success-rate denominator 54 of 56 |
| 3. Comparable prices | migration 008 (currency, variant, composition on every observation), the price-selection rule in `docs/decisions/ADR-008-approval-clarifications.md`, parsers and validator |
| 4. Identity and weighting | `priceintel/reference/offers.py` (repost identity over the whole window), `docs/analysis_plan.md` (price summary, weighting, bootstrap interpretation) |

The approved proposal version is the repository at the approval date; the figures the decision refers
to are those of the development crawl of 2026-10-29, commit `0200a0a9c3d901fb3ad85b89afcfbbe2c9dbc2f8`.
