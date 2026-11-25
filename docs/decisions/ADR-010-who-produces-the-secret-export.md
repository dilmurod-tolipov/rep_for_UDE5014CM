# ADR-010: the Secret export is produced by me, from the public channel

- **Date:** 2026-11-25 (Week 11)
- **Status:** accepted
- **Amends:** ADR-007 §"Consent and sharing" and its sentence "Public visibility does not establish
  a right to reuse". Everything else in ADR-007 stands: one export, after the window, into
  `reference_offers`, never into a model.
- **Related:** `priceintel/reference/offers.py`, migration `market_intel/005`, Module Leader
  26/10/2026 point 1.

## Context

ADR-007 withdrew the automated collector that read Secret's public Telegram channel twice a day, and
replaced it with a single export taken with Telegram Desktop's own "Export chat history" function.
It assumed the **shop owner** would produce that file and hand it over with written consent, and it
justified the route on that basis, writing that public visibility alone "does not establish a right
to reuse".

That assumption does not hold. The owner does not use any system of ours and is not part of the
workflow; waiting on him to produce a file is the kind of scheduled human action ADR-007 set out to
remove in the first place. **I will produce the export myself.**

The addendum sent to the Module Leader on 29 October 2026 says only "one export after the collection
window closes" and does not state who produces it, so nothing that was put to him becomes incorrect.
The inconsistency was internal to this repository, which is what this record fixes.

## Decision

I export the history of Secret's public channel myself, once, after the approved window closes on
6 December 2026, using Telegram Desktop's own export function (JSON, no media), and import it with
`python -m priceintel import-reference`.

**The basis for using the data is that Secret publishes these prices publicly itself.** The channel
is a public shop window: Secret posts each bouquet with its price so that customers can read them.
The project uses them as published, for a descriptive academic price comparison, and nothing more.
The `consent_note` recorded with the import states that basis in those terms rather than claiming a
permission that was not given.

What keeps that proportionate, and all of it was already true in ADR-007:

- **Minimal fields.** Only the post's publication date, link, price and a short title. Captions,
  media and descriptions are not stored, and contact lines (phone numbers, @handles, links) are
  stripped before a title is taken.
- **No personal data.** The posts are a business's own product advertisements. No customer, author
  or individual is recorded anywhere in the project.
- **One manual export, not scraping.** The act ADR-007 objected to was automated, repeated
  collection at a schedule; this is a single use of the platform's own export feature on a channel
  anyone may read. That distinction is the whole reason ADR-007 chose the export route, and it does
  not depend on who presses the button.
- **Not redistributed.** The export file is not committed (`.gitignore`); it travels in the
  submission package only. The repository carries a synthetic sample in the same shape so that a
  clean checkout and the tests work without it.
- **Reference data, never primary.** The offers live in their own table, do not count towards the
  primary-data target, and cannot reach a model matrix —
  `tests/test_no_reference_in_models.py` imports them and proves it.

## Consequences

- Secret's prices no longer depend on anyone else, so the comparison can be completed on 7 December
  whatever the owner does.
- **No written permission from the shop is held.** That is a deliberate position, not an oversight:
  the prices are published by the business itself, and the project stores a minimal, non-personal
  subset of what any customer can read. ADR-007's stricter sentence is amended by this record rather
  than quietly dropped, and Report Section 5 states the position and the residual exposure, which is
  that a business could still object to its published prices being reproduced in coursework even
  though they are public.
- Wording throughout the repository that said "the owner's export" is corrected to say who actually
  produces it: ADR-007's consent paragraph, the README, the report draft, the three checkpoint
  records that mention it, and the docstrings and CLI help in `priceintel/reference/`,
  `priceintel/analysis/` and `priceintel/cli.py`. The text inside applied migration
  `secret_shop/002` is left as it was written on 29 October: an applied migration is checksummed and
  is a historical record, and editing it would break the migration guard.
- `--exported-at` is now the date I produced the file, and `--consent-note` carries the
  public-publication basis above.
