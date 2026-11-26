# ADR-010: the Secret export is produced by me, from the public channel

> **Ruled on by the Module Leader, 2026-11-26.** The position recorded below — that public
> publication is a sufficient basis on its own — was **not accepted**. His words: "The channel's
> public status documents where the prices came from. It does not document Secret's consent to the
> proposed coursework use and sharing with assessors." The requirement is therefore:
>
> 1. obtain **short written confirmation from Secret** covering the coursework use and the sharing
>    of the prices with assessors, and keep it with this record; **or**
> 2. if it cannot be obtained by submission, **omit Secret's records and comparisons entirely**,
>    complete the competitor analysis, and explain the limitation. The reference importer may still
>    be demonstrated with the labelled synthetic fixtures.
>
> Who produces the export is unaffected and stands as decided below: I do. What changed is that
> provenance and permission are two different things, and only the first is settled by the channel
> being public. See the postscript at the end of this record.

- **Date:** 2026-11-25 (Week 11); amended 2026-11-26 after the Module Leader's ruling
- **Status:** accepted in part — the export route stands, the consent basis is superseded
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

---

## Postscript, 2026-11-26: what the Module Leader ruled, and what now happens

The reasoning above separated two things that the ruling puts back together. Publication settles
**where the prices came from**. It does not settle **whether Secret agrees to this use of them** —
being read by a customer in a shop window is not the same as being collected into a coursework
dataset and handed to an assessor. That distinction was ADR-007's original point, and dropping it
was the weak step in this record.

**Required before any import.** A short written confirmation from Secret, covering (a) the use of
its published prices in this coursework and (b) sharing them with the assessors. A message is
enough; it is stored with this record as `docs/approval/secret-consent.*` and quoted in
`reference_imports.consent_note`.

**If it does not arrive by submission.** Secret's records and comparisons are omitted entirely:

- no `import-reference` run against real data, so `reference_offers` stays empty;
- every Secret comparison already reports `insufficient_evidence`, so the analysis needs no change
  — this is the state the project has been in all along;
- the report states the limitation in Section 3 and Section 5: the price-position comparison the
  project was approved to produce could not be completed, and why;
- the importer is still demonstrated, with the labelled synthetic fixture export in
  `tests/fixtures/`, which is what the nine import tests already use.

Either way the competitor analysis — the primary data, the hypothesis tests, the models and the
decision output — is unaffected, because Secret's offers were never an input to any of it.

**What this costs if the confirmation does not arrive.** Analytical question Q2 goes unanswered.
Objective O3 is then partly met at best. The project still answers Q1 and Q3 from its own collected
data, which is where the assessed evidence lives.
