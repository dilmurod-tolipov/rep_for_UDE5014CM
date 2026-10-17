# ADR-001: Which competitor sites count as independent sources

- **Date:** 2026-10-17 (Week 6)
- **Status:** Accepted; Module Leader to be informed (change to the backup list)
- **Related:** v2 proposal, "Collection plan"; `docs/compliance/COMPLIANCE-CHECK-2026-10-17.md`

## Context

The v2 proposal named four competitors (pro-buket.uz, loveflowers.uz, uzflowers.com,
dostavka-cvetov365.uz) and two backups (dostavka-cvetov24.uz, ultraflowers.uz), with the
rule: *"if sites share an operator or catalogue, they count as one source"*.
Reconnaissance on 2026-10-17 tested that rule.

## Evidence

1. **uzflowers.com = uzflora.com.** Both list the phone number +998 90 808 34 37.
2. **loveflowers.uz, dostavka-cvetov365.uz, dostavka-cvetov24.uz, ultraflowers.uz
   (and loveflowers24.uz) are one network:**
   - byte-identical robots.txt and identical user-agreement text (which refers to "Russian
     law", and ultraflowers.uz advertises a threshold in "tenge");
   - the same list of 24 Uzbek city subdomains on every site;
   - shared product URL slugs on the first 4 catalogue pages:

     | Pair | Shared slugs | Same price |
     |---|---|---|
     | cvetov365 × cvetov24 | 220 / 224 | 206 |
     | loveflowers × ultraflowers | 56 / 128 | 40 |
     | loveflowers × cvetov365 | 52 / 224 | 9 |
     | cvetov365 × ultraflowers | 19 / 128 | 15 |

## Decision

| Source (operator) | Site scraped | Why this site |
|---|---|---|
| Pro-Buket | pro-buket.uz | Independent, large catalogue |
| Uzflora | uzflora.com | Same operator as uzflowers.com; prices are in the HTML |
| "Love Flowers" network | loveflowers.uz | Largest catalogue in the network; one site so the network is not over-weighted |
| Kamila's | kamilas.uz | Independent (own phone, own platform), robots allows all |

dostavka-cvetov365.uz is **dropped as an independent competitor** and both original backups
fall away, because all three belong to the network. kamilas.uz becomes the fourth source.
The minimum of four competitor sources (excluding Secret) is still met.

The database records this in a `operator` column on `shops`; all "per shop" analysis
(clustering, leave-one-out) works at **operator** level.

## Consequences

- Kamila's catalogue is small (about 29 products), so most category coverage will come from
  the other three. Coverage per category is checked against the proposal's rule
  (≥20 listings from ≥3 sources) at Checkpoint 2.
- Possible extension (not in scope): the network sells the same product at different prices
  on different brands, which could be a later robustness check.
- Kamila's was not in the proposal's backup list, so the Module Leader is told by email.
