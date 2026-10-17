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
sql/market_intel numbered schema migrations for the market database (001_core.sql, ...)
sql/secret_shop  numbered schema migrations for Secret's own catalogue database
config/          shops.json: shop registry with compliance status (ADR-001)
tests/           automated tests; all test data is synthetic and stays in temp databases
tools/recon/     dev-only reconnaissance scripts (not assessed collection)
data/            local databases (git-ignored); committed snapshots go in data/snapshots/
docs/            approval record, decisions (ADRs), compliance checks, evidence register, AI log
storefront/      React demo storefront + admin (pre-approval baseline, see docs/baseline)
```

## Setup

Requires Python 3.13 and Git. No API keys or accounts are needed.

On Windows, clone into a short path (e.g. `C:\dev\`): pip can fail inside very long folder paths.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

## Database

```bash
python -m priceintel init-db     # creates data/market_intel.db + data/secret_shop.db, loads shops and Secret's channel
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

## Collecting competitor prices

```bash
python -m priceintel collect --shop uzflora               # one shop, purpose=dev (default)
python -m priceintel collect --all --purpose assessed     # only after approval, from committed code
python -m priceintel listings --limit 20                  # latest price of each listing (retrieval)
python -m priceintel listings --run 1                     # what a given run collected
python -m priceintel runs                                 # run history: status, pages, commit
```

What one run does (`priceintel/collect/runner.py`):

1. Records a `scrape_runs` row with purpose, trigger, git commit and whether the code was modified.
2. Reads the shop's `robots.txt` (logged in `fetch_log`). Wildcard rules such as `/*?*` are applied
   (`priceintel/collect/robots.py`); if robots.txt cannot be read, the shop is not crawled.
3. Fetches catalogue pages one by one, at least 5 s apart (or the site's Crawl-delay if longer),
   with an identifying user agent. Network errors, 429 and 5xx are retried up to 3 times; every
   attempt is logged with HTTP status, size, SHA-256 of the content and timing.
4. Parses product cards (`priceintel/collect/parsers/`), validates each record
   (`priceintel/collect/validate.py`) and stores valid ones as listings + price observations.
   Invalid records go to `rejected_records` with the rule that failed and the raw payload.
5. Marks the run `success` (>= 80% of pages fetched and parsed), `partial` or `failed`.

Parsers available: `uzflora`. More shops are added at Checkpoint 2.

## Collecting Secret's own prices

Secret publishes every bouquet with its price on its public Telegram channel
(https://t.me/secret_flowersuz). The collector reads the public web preview into `secret_shop`,
then a snapshot copies the current prices into `market_intel` (ADR-003).

```bash
python -m priceintel collect-secret --days 14             # posts from the last 14 days -> secret_shop
python -m priceintel secret-prices --limit 20             # Secret's current prices (retrieval)
python -m priceintel snapshot-secret                      # copy into market_intel as own_system rows
python -m priceintel check-integrity                      # cross-database orphan check
```

Only labelled prices (`Стоимость:`, `Цена:`, `Все по:`) are accepted; posts without a price or with several
different prices go to `rejected_posts`. Phone numbers and @handles are removed before captions are stored.

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
