# Competitive Price Intelligence for a Tashkent Flower Shop

UDE5014CM Data Science for Developers, Assessment 2. Student: Dilmurod Tolipov (50000161).

A data system that helps the owner of **Secret** (a Tashkent flower, berry and houseplant shop)
see how Secret's prices compare with a sample of competitors, and which product categories
warrant further investigation. It collects its own primary data: a polite, scheduled scraper
reads public competitor catalogues every 12 hours, and Secret's own prices are recorded through
Secret's admin system.

## Status

| Stage | Tag | State |
|---|---|---|
| Pre-approval demo (reused, not assessed) | `baseline-demo` | done |
| CP1 collection MVP (Week 7) | `cp1` | in progress |
| CP2 reliable collection and data quality (Week 8) | `cp2` | planned |
| CP3 statistical analysis (Week 9) | `cp3` | planned |
| CP4 integrated system and dashboard (Week 10) | `cp4` | planned |

## Repository layout

```
priceintel/      Python package: database layer and command line (python -m priceintel)
sql/market_intel numbered schema migrations (001_core.sql, ...)
config/          shops.json: shop registry with compliance status (ADR-001)
tests/           automated tests; all test data is synthetic and stays in temp databases
tools/recon/     dev-only reconnaissance scripts (not assessed collection)
data/            local databases (git-ignored); committed snapshots go in data/snapshots/
docs/            approval record, decisions (ADRs), compliance checks, evidence register, AI log
storefront/      React demo storefront + admin (pre-approval baseline, see docs/baseline)
```

## Setup

Requires Python 3.13 and Git. No API keys or accounts are needed.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

## Database

```bash
python -m priceintel init-db     # creates data/market_intel.db, applies migrations, loads shops
python -m priceintel db-info     # migrations, row counts, shop registry
```

`init-db` is safe to run again: applied migrations are skipped and shops are upserted.
If an applied migration file is edited, `init-db` stops with an error (checksums are stored
in `schema_migrations`); schema changes go in a new numbered file.

What the database enforces itself (`sql/market_intel/001_core.sql`):

| Rule | How |
|---|---|
| Correct types | `STRICT` tables |
| Prices positive and plausible; old price above current price | `CHECK` |
| One observation per listing per run (idempotent re-runs) | `UNIQUE (listing_id, run_id)` |
| Every scraped price points at the HTTP request it came from, in the same run and shop | `CHECK` + trigger `trg_price_obs_fetch_matches_run` |
| Evidence cannot be edited or deleted | append-only triggers on `price_observations` and `fetch_log` |
| Secret's own prices only on the own shop, never mixed with scraped rows | trigger `trg_price_obs_source_matches_shop` |
| Assessed runs only from committed, unmodified code | `CHECK` on `scrape_runs` |
| A shop can only be active if robots.txt allowed it | `CHECK` on `shops` |

## Tests

```bash
python -m pytest
```

## Ethics in one paragraph

Only public product information is collected (title, price, old price, availability, URL, time).
No personal data, images or descriptions are stored. robots.txt is honoured on every run, requests
are rate-limited and identified, and every record keeps its source URL. Any customer, order or payment
records in `secret_shop` are synthetic, flagged `is_synthetic`, and never used in the analysis.
See `docs/compliance/`.
