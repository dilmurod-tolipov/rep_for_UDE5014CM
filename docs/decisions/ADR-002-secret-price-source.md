# ADR-002: Where Secret's own prices come from

- **Date:** 2026-10-17 (Week 6)
- **Status:** Accepted by the student; to be included in the reply to the Module Leader
- **Related:** v2 proposal "Secret's prices"; approval feedback point 2; issue #7

## Context

The hypothesis compares Secret's prices with the competitor median, and the Module Leader asked
for **fresh, dated observations of Secret's prices collected through our own system**, kept apart
from competitor data and from any pre-existing reference data.

Facts on 2026-10-17:

- The owner does not use the demo storefront or admin panel.
- The demo catalogue prices (`storefront/src/data/products.ts`) are placeholders, not real prices.
- Secret publishes prices on its own public pages (social media posts / price posts). The exact
  pages are listed in `config/secret_sources.json` once confirmed by the student.

Rejected alternatives:

| Alternative | Why rejected |
|---|---|
| Use the demo placeholder prices | Not real prices; using them in the analysis would be fabricated data |
| Invent "realistic" prices | Fabrication, prohibited by the brief |
| Scrape Instagram automatically | Instagram's terms forbid automated collection; pages need a login |
| Ask the owner to use the admin panel | The owner does not use the system |

## Decision

Secret's prices are **observed by the student on Secret's own public pages and recorded through
our admin entry form**, one observation per product per check, at least weekly from approval to the
end of the comparison window.

Every recorded price stores:

- the product (`secret_shop.products`) and its comparison attributes (type, stem count, packaging, size);
- the price in UZS and whether it is a sale price;
- `source_url`: the exact public post or page the price was read from;
- `source_published_at`: when that post was published (if shown);
- `observed_at`: when the student checked it; `entered_by`; `entered_at`.

A snapshot job then copies the current Secret prices into `market_intel` as
`source_type = 'own_system'` rows on the own shop (`is_own_shop = 1`). The database already
refuses own-system rows on competitor shops and scraped rows on the own shop
(trigger `trg_price_obs_source_matches_shop`).

## Rules that keep this honest

1. Only prices **visible on Secret's public pages on the day of the check** are recorded.
   No price is entered from memory or estimated.
2. If a product's price is not shown publicly, it is **not** entered. It is missing, not imputed.
3. A price whose post is older than the comparison window is flagged `stale` and excluded from the
   main analysis (sensitivity analysis only).
4. Demo placeholder prices are kept only as `reference` rows and never enter the comparison.

## Consequences

- Collection of Secret's side is a **manual form workflow** (one of the brief's accepted methods);
  the competitor side stays automated.
- The number of comparable Secret products depends on how many prices Secret publishes. The proposal
  requires at least 5 comparable products per analysable category; categories below that are reported
  descriptively only. This is checked at Checkpoint 2.
- Observation frequency is lower for Secret (weekly) than for competitors (12-hourly); the comparison
  uses each listing's median regular price over the window, so this does not bias the ratio.
