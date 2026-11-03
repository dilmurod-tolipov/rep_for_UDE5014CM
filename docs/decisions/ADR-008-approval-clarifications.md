# ADR-008: Implementing the four clarifications in the approval decision

- **Date:** 2026-11-03 (Week 9)
- **Status:** Accepted. The project is **approved** (Sanjar Bekov, 2026-11-03,
  `docs/emails/2026-11-03-approval-decision.md`); these are the clarifications the decision attaches.
- **Related:** ADR-001 (operator groups), ADR-006 (category rules), ADR-007 (reference data),
  `docs/analysis_plan.md`.

## 1. Calendar

| | |
|---|---|
| Approved collection window | **9 November – 6 December 2026** (28 days) |
| Cadence | 08:00 and 20:00 Asia/Tashkent = **56 scheduled runs** |
| Success criterion | at least **54 of 56** successful runs (95%) |
| Submission deadline | **14 December 2026** |
| Day-42 extension | **removed** – it would end on 20 December, after the deadline |

The workflow works the window out from the date (`.github/workflows/collect.yml`): a run inside it is
`assessed`, a run outside it is `dev`. No repository variable to set, nothing to remember on 9
November, and no way to relabel a test record as assessed data afterwards. If a category ends the
window below the minimum, it is reported as insufficient evidence — there is no longer an extension
to fall back on.

## 2. Feasibility figures: three different counts

The Module Leader's arithmetic is right, and the figures were being reported at the wrong level.
Three counts are now reported separately, from the development crawl of 2026-10-29 (rules 1.2.2):

| Count | Meaning | Total |
|---|---|---|
| Collected | every distinct product the crawl stored | **586** |
| Eligible | in an analysable category (68 `out_of_scope` / `unclassified` removed) | **518** |
| **Usable** | eligible **and** priced for a whole item or a stated bundle (per-stem listings removed) | **405** |

The third line is new and it changes the picture: `roses_mono` for LOVEFLOWERS_NET falls from 121 to
**11** once single stems are excluded, because most of that section is sold by the stem. Reporting
only the first number would have overstated the evidence behind the most important category.

For Secret: **119 offers were observed** in 14 days of pre-approval development, from which about
**238 are projected** over the 28-day window. The two are never shown as one number, and the
projection is labelled as a projection. Unclassified offers (about half of Secret's captions identify
no product type) stay out of every category comparison and are reported as a count.

## 3. Comparable prices: an explicit rule, and no conversion

**Price selection.** A price enters the database only when the shop itself publishes it in UZS:

1. pro-buket prints UZS, USD and RUB on one card — the parser reads the element the shop labels UZS;
2. uzflora serves USD to visitors outside Uzbekistan — the collector requests `?currency=UZS`;
3. loveflowers and kamilas publish UZS only (kamilas states `priceCurrency` in its Product block);
4. anything else is quarantined as `currency_not_uzs` and counted.

**No conversion, ever.** The project holds no exchange rate and no rate date, so a comparison can
never depend on when a rate was taken. The currency label that was read is stored on every
observation (`currency_shown`, migration 008) and a database trigger refuses a scraped row in any
other currency, so the rule is auditable rather than merely asserted.

**Variant.** What one price buys is now a stored feature (`listing_features`, migration 009):
`per_item`, `per_bundle` with the stated `stem_count`, or `per_stem`. Per-stem listings are excluded
from category medians and reported separately. Where the shop states a composition
("Состав: розы — 15 шт"), it is stored verbatim and is the source of the stem count — which is never
estimated from a price or a photograph.

**Discount status and availability** were already stored and are preserved per observation: the main
comparison uses the regular price (the old price where a sale is shown), with the current sale price
as a sensitivity check.

**Wording.** Merged-bouquet results are described as comparisons of the **observed assortments** of
the sampled shops. They do not establish a price difference between equivalent products, and the
report says so wherever a figure appears.

## 4. Identity and weighting

**Offer identity.** A repost is the same offer, however long the gap and whatever the price
(migration 010). Identity is the normalised caption, checked against the whole import:

| Case | `match_confidence` |
|---|---|
| same caption, same price | `exact` |
| same caption, different price | `uncertain` — grouped, flagged, excluded in a robustness check |
| no earlier match | `unique` |

A distinct offer is dated by its first publication and summarised by the **median of the prices it
was posted at**; the lowest and highest are kept beside it so a moving price is visible rather than
averaged away.

**Repeated prices.** A competitor product is summarised by the **median of its observations in the
window**, so twice-daily snapshots cannot make one product count more than another. A product
observed once and a product observed 56 times each contribute exactly one value.

**Weighting.** Per-group comparisons are the primary output. The pooled figure is the **unweighted
mean of the per-group percentages**, so LOVEFLOWERS_NET (354 products) does not outweigh KAMILAS
(14). The weighting is stated beside every pooled figure.

**Bootstrap interpretation.** Intervals describe the uncertainty of a median within **the four
sampled operator groups and the 28-day window** — resampling products, not businesses. They are not
confidence intervals for the Tashkent market, and the report says this next to each interval.
