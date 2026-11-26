# ADR-009: Secret's operational core and dated delivery terms

**Date:** 2026-11-21
**Status:** accepted
**Supersedes nothing. Completes:** the schema promised in the approved v2 proposal and announced in
`sql/secret_shop/002_remove_telegram_products.sql` ("the operational schema ... is rewritten in a
later migration").

## Context

The approved proposal listed two things this repository did not have:

1. **`secret_shop` operational core** — `clients`, `addresses`, `orders`, `order_items`, `payments`,
   `admin_users`, with synthetic fixtures flagged `is_synthetic`.
2. **`market_intel.shop_delivery_terms`** — delivery terms per shop, dated.

Neither affects the price comparison, which is why neither was needed for Checkpoints 1–4. Two
things make them worth building anyway: LO2 is assessed on the database solution, and the viva may
ask about any database object. A gap between the approved proposal and the delivered schema is also
a gap a marker can see, since the approval record is in the repository.

The complication is honesty. Secret has no ordering website and publishes only on its public Telegram
channel; a friend and I built a demonstration storefront and admin panel for the shop and offered
it in person, and the owner declined to adopt it. The shop therefore keeps no digital order record
that this project could draw on, and there is no prospect of one. So an operational core here can only ever hold invented rows.
Invented rows in a repository that also holds assessed evidence are a real risk: a marker, a future
reader, or a careless `JOIN` could mistake them for data.

## Decision

Build both, and make the invented data **structurally impossible to mistake for evidence**.

### `secret_shop` migration 003

- `is_synthetic` is `NOT NULL` on every operational table, so a row cannot be inserted without
  declaring what it is.
- Triggers propagate the declaration: an address must match its client, an order must match its
  client, its author and its address, a payment must match its order.
- The decisive rule: **a real order may not contain a synthetic product.** Fabricated products
  cannot produce real revenue.
- `priceintel/integrity.py` gains checks 5 and 6: flag disagreements (the `UPDATE` path the triggers
  cannot see) and a fixture title appearing in `reference_offers`, which is how a mistaken import
  would show up.
- The dashboard's overview prints an "of which synthetic" column beside every operational row count
  and says in words that Secret keeps no digital records. A count of five orders shown without that
  column would read as real trade.

Two further decisions inside that migration, both defensible in a viva:

- **`products` and its children are dropped and recreated, not altered.** The old shape required a
  `t.me` post URL on every product, because the table was designed for the withdrawn Telegram
  collector; a hand-entered product would have had to carry an invented Telegram link. The tables
  were emptied by migration 002, so nothing is lost, and the children are dropped before the parent
  so no foreign key is ever left pointing at a missing table. The new table carries a pair of
  constraints instead: a collected product must prove its provenance, and a hand-entered one may not
  pretend to have any.
- **There is no price column on `products`.** The catalogue price is a dated row in
  `product_price_history`, and the current price is a view over it — the same append-only pattern as
  `price_observations` in `market_intel`, and it makes a stale copy impossible.

Order totals are derived, never typed: `order_items.line_total_uzs` and `orders.total_uzs` are
`GENERATED` columns, and triggers maintain `orders.items_total_uzs` from the lines.

### `market_intel` migration 014

`shop_delivery_terms` records one dated reading per shop: the date the page was read, its URL, the
fee and threshold (`NULL` meaning "the page does not say", which is not zero), and the sentence from
the page. It is append-only, refuses mirror domains (ADR-001), and allows one reading per shop per
day.

**The table ships empty, and nothing seeds it.** These are facts about real companies; an invented
delivery fee would be fabricated evidence about a named business. Readings are entered by hand from
each shop's own delivery page through `python -m priceintel record-delivery-terms`, which requires
the URL, the date and the quoted text.

The approved analysis plan says delivery fees are "recorded per shop with a date and reported
descriptively, never added to a price". Keeping the terms in their own table makes that structural:
the comparison reads `analysis_products`, which cannot see this table.
`test_recording_delivery_terms_changes_no_price` asserts the dataset is byte-identical before and
after a fee is recorded.

## Consequences

- 40 new tests (316 total, from 276). The operational tests are mostly about what the database
  **refuses**: a real client without recorded consent, a full phone number, a delivery fee with no
  address, a cancelled order with no reason, captured payments above the order total, a synthetic
  product in a real order, a fixture title reaching the analysis data.
- Privacy improves rather than worsens, even though a customer table now exists: a non-synthetic
  client requires `consent_recorded_at`, and the only contact column is `phone_last4` — enough for
  staff to recognise a returning customer, useless for contacting a stranger. Data minimisation by
  schema instead of by policy.
- `clients`, `orders` and `payments` are **not** part of the assessed data pipeline and are not in
  the committed snapshot, which covers `market_intel` only. They are demonstration and schema
  evidence, and the report says so.
- The fixtures are loadable and clearable (`python -m priceintel fixtures --load / --clear`), and
  loading twice is refused so the demo revenue cannot double.

## Alternatives considered

- **Leave both unbuilt and explain the deviation in Report Section 5.** Honest and cheaper, and it
  stays the fallback position if anything here proves fragile. Rejected because LO2 is assessed on
  the database and the proposal is in the repository: an explained gap still reads as a gap, where a
  built schema with declared fixtures reads as a decision.
- **Build the operational core with "realistic" order data.** Rejected outright. Invented orders
  that are not labelled are fabricated evidence, which is the one thing this project must not
  produce. Every row is flagged, and the flag is enforced by the database.
- **Seed `shop_delivery_terms` from the competitor sites now.** Rejected: the delivery pages have
  not been read and dated yet, and inventing their contents would be fabrication. An empty table is
  the honest state, and the command exists to fill it.
- **Add `product_matches` as well.** Not done. The approved analysis plan v2.0 compares by category,
  not per product (Secret's posts rarely state flower type and never stem count, ADR-004), so a
  per-product matching table would be unused scaffolding. `integrity.py` names the place where its
  checks go if it is ever added.
