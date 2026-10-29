# Operator groups and mirror domains

Module Leader, 26/10/2026, point 1: *"Record the evidence supporting each grouping, assign an
operator/catalogue identifier, and map the related domains to it. Mirrored listings must not increase
the number of independent competitors or products."*

The analysis counts **operator groups**, not domains. One domain per group is collected; the others
are registered as mirrors and never crawled. This is enforced in three places: the shop registry
(`config/shops.json`), the database (unique index `ux_shops_one_active_domain_per_group`, migration
004) and the test suite (`tests/test_source_groups.py`).

| Group id | Domain collected | Mirrors (not collected) | Evidence for the grouping | Checked |
|---|---|---|---|---|
| `PROBUKET` | pro-buket.uz | — | Independent operator, own catalogue and terms | 2026-10-17, re-checked 2026-10-29 |
| `UZFLORA` | uzflora.com | uzflowers.com | Both sites publish the same telephone number (+998 90 808 34 37). uzflowers.com is a Tilda store whose prices are not in the page HTML | 2026-10-17 |
| `LOVEFLOWERS_NET` | loveflowers.uz | dostavka-cvetov365.uz, dostavka-cvetov24.uz, ultraflowers.uz | Byte-identical robots.txt and identical user-agreement text; the same list of 24 Uzbek city subdomains; shared product slugs measured on the first four catalogue pages: cvetov365 × cvetov24 220/224 slugs (206 at the same price), loveflowers × ultraflowers 56/128 (40), loveflowers × cvetov365 52/224, cvetov365 × ultraflowers 19/128 | 2026-10-17 (`tools/recon/catalogue_overlap.py`, ADR-001) |
| `KAMILAS` | kamilas.uz | — | Independent operator: own telephone number, own platform, own terms | 2026-10-17, re-checked 2026-10-29 |

`SECRET` is the shop the analysis is about, not a competitor group: its offers are reference data
(`reference_offers`), separate from the scraped competitor observations.

`FIORI` (fiori.uz) is registered but inactive: its robots.txt is `Disallow: /`.

## What the rule means for the counts

- A product that appears on loveflowers.uz and on two of its mirrors is **one** product, because only
  loveflowers.uz is collected.
- "At least 300 distinct competitor products" and "at least 10 products per displayed comparison" are
  counted per operator group, over distinct listings, after repeated observations of the same listing
  have been collapsed.
- Robustness check "leave one operator group out" removes a whole group, mirrors included, since the
  mirrors hold no separate records.

## If a grouping turns out to be wrong

The evidence above is dated. If a mirror later publishes a different catalogue or different prices,
the finding is recorded here with its date, the domain is re-registered as its own group with a new
`operator_group` id, and the change is noted in the report; records already collected keep the group
they were collected under, because `shops` is the provenance of every listing.
