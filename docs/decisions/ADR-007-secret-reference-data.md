# ADR-007: Secret's offers as reference data from one owner export

- **Date:** 2026-10-29 (Week 8)
- **Status:** Accepted; to be confirmed by the Module Leader with the final approval decision.
- **Supersedes:** ADR-003 (collect Secret's prices from the channel's public web preview).
- **Related:** Module Leader 26/10/2026 point 1; migrations `market_intel/005`, `market_intel/006`,
  `secret_shop/002`; `priceintel/reference/offers.py`.

## Context

ADR-003 collected Secret's prices by reading the public web preview of its Telegram channel twice a
day. Two things ended that route:

1. Telegram's Content Licensing and AI Scraping Terms restrict scraping and reuse of platform data.
   Public visibility does not establish a right to reuse.
2. The Module Leader ruled (26/10/2026, point 1) that importing an exported file **does not count as
   primary data collection** at all: the competitor scrapers are the primary data, and Secret's
   offers are "a small, separately identified reference dataset".

The collector was also still running on the schedule after it was described as disabled: 23
development runs between 18 and 29 October 2026, all `purpose = dev`. It was removed on 2026-10-29
(commit `c75aee9`), the records were deleted (migrations 006 and secret_shop 002), and the
discrepancy was reported to the Module Leader.

## Decision

### One export, not a weekly chore

Because reference imports earn no primary-data credit, their **frequency carries no assessment
weight**. So the owner exports the channel history **once**, after the 28-day competitor collection
window closes, with Telegram Desktop's own "Export chat history" (JSON, no media). One file covers the
whole window, dated by each post's publication date.

This replaces the "weekly export" of the earlier draft. It also removes the only part of the design
that needed a human action on a schedule, which was a reproducibility risk: an assessor can rerun
everything from the file.

If the window has to be extended (the Day 21 check), a second export is taken then; the importer is
idempotent, so re-importing an overlapping file adds only the posts that are new.

### Minimal, separate, never in a model

- New tables in `market_intel` (migration 005): `reference_imports` (file name, SHA-256, export date,
  consent note, row counts) and `reference_offers` (post id, post link, publication date, short
  title, price, repost group, category + rules version).
- Stored fields are only what the descriptive comparison needs. Contact lines (phone numbers,
  @handles, links) are stripped before a title is taken; captions, media and descriptions are not
  stored.
- Nothing writes Secret prices into `price_observations` any more: the `own_system` path and the
  `snapshot-secret` command are gone, and migration 006 deleted the rows they had produced.
- `priceintel/analysis/model_data.py` is the only source of model rows and reads scraped competitor
  observations only; `tests/test_no_reference_in_models.py` imports reference offers and then asserts
  they cannot appear in a model matrix.

### Reposts

A different message id is not a new product. Posts with the same normalised title and the same price
within 14 days share an `offer_group_id`; the view `v_reference_distinct_offers` counts one offer per
group, dated by its first publication. Re-reading an old post creates nothing and is never evidence of
current availability.

### Consent and sharing

The export is the owner's own channel content, handed over for this coursework. The consent note is
recorded with every import (`reference_imports.consent_note`) and must cover the academic use and the
sharing of the file with the assessors. The real export is **not** committed to the public repository
(`.gitignore`); it travels in the submission package. The repository contains a synthetic sample
export in the same shape (`tests/fixtures/telegram_export_synthetic.json`) so the tests and a clean
checkout work without it.

A CSV price log from the owner is accepted through the same importer as a fallback.

## Consequences

- Secret's offers are reference data: they appear in the descriptive category comparison and nowhere
  else. The report must not describe them as primary data collected by the system.
- The project needs no Telegram account, API key or private credential to reproduce.
- The 28-day comparison uses Secret offers dated inside the window; offers outside it are available
  for context only and are labelled as historical.
- Secret's captions name a flower type in a minority of posts and never a stem count, so the
  comparison stays a category-level price-position comparison (ADR-004, ADR-006).
- `secret_shop` still carries the channel-shaped tables from migration 001, now empty. The reduced
  operational core (categories, products, prices, synthetic clients and orders for the storefront
  demo) replaces them in a later migration.
