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

Parsers: `uzflora` (WooCommerce cards), `probuket` (three currencies on one card - the UZS span is
the one read), `loveflowers` (section pages; `/shop/` now builds its grid with a disallowed ajax
endpoint), `kamilas` (catalogue is built in the browser, so the collector follows the sitemap the shop
publishes and reads the schema.org Product block on each product page).

One domain per operator group is collected; mirrors are registered and never crawled
(`docs/compliance/source_groups.md`).

## Analysis categories

Categories are defined by a versioned rules file that is committed and tagged **before** any analysis
run, and are derived from text only - the product title, the section part of the URL and the shop's own
section slugs. Price, old price and sale state are never read; price-band slugs (`nedorogie-czvety`),
promotion slugs (`aktsii-*`, `topsale`) and occasion slugs (`8-marta`) are deliberately ignored
(ADR-006).

```bash
python -m priceintel classify --shop uzflora      # assign categories from config/category_rules.v1.json
python -m priceintel category-report --purpose dev  # Table 1: distinct listings per category and operator
```

Each assignment records the rules version, the SHA-256 of the rules file, which rule fired and on what
evidence (`listing_categories`). Re-running `classify` is idempotent; a new `rules_version` adds a new
set of assignments instead of overwriting the old one. Listings that no rule matches are stored as
`unclassified` and reported as a count - they are excluded from the analysis, never dropped.

## Dashboard

```bash
python -m priceintel dashboard            # http://127.0.0.1:8000/
python -m priceintel dashboard --port 8731
```

Six pages over **both** databases - overview, price position, coverage, price changes, market and
discounts, data quality - plus a JSON API at `/api/<query name>.json` for every stakeholder query.
The pages are driven by the same `sql/queries/*.sql` files as the command line, so a number on a page
and a number in the report have one source.

It is built on the standard library (`http.server`) with hand-written inline SVG charts, so nothing
beyond the pinned dependencies is needed to run it. Input is validated against what the database
actually holds: `?purpose=banana` returns 400 and lists the real options rather than silently showing
something else. The dashboard only ever reads; the cross-database integrity check runs on every load
of the overview page and is shown there.

## Stakeholder queries, data quality and snapshots

```bash
python -m priceintel query --list                      # the five questions and their files
python -m priceintel query price_position_by_category --purpose assessed
python -m priceintel quality --purpose assessed        # recorded in data_quality_checks
python -m priceintel snapshot --purpose assessed --label cp2   # CSV + MANIFEST.md under data/snapshots/
```

The queries live in `sql/queries/*.sql`, one file per stakeholder question, each with the question and
how to read the result in its header. They take named parameters (`:purpose`, `:rules_version`,
`:min_items`), and `query` refuses to run one with a parameter missing rather than guessing a default.
SQLite has no `median()`, so each median is computed by numbering the rows and averaging the middle
one or two.

`quality` runs nine checks over the stored data - data target, completed runs, run success rate,
quarantine rate, unclassified rate, price-outlier rate, freshness, duplicate observations and orphan
observations - and records every result in `data_quality_checks` with its threshold and status, so the
report can show how healthy the data was on the day the analysis ran.

`snapshot` writes the committed evidence of collection: CSV exports of the shops, runs, fetch log,
listings, price observations, quarantine, categories and quality checks for one purpose only, plus a
`MANIFEST.md` with row counts, each file's SHA-256 and the collecting commit. Secret's reference
offers are exported only with `--include-reference`, for the submission package.

## Secret's offers (reference data, not primary data)

Secret's own offers are **reference data**: they are imported from an export the owner produces with
Telegram Desktop, kept in their own table, and never written into `price_observations` or used by any
model (ADR-007). Reading the channel automatically was withdrawn on 2026-10-29.

```bash
python -m priceintel import-reference path/to/result.json     --exported-at 2026-11-30 --consent-note "owner's written consent, 2026-11-30"
python -m priceintel reference-report --since 2026-11-02 --until 2026-11-29   # Table 2
```

The import records the file's SHA-256, strips contact lines, groups reposts (same title and price
within 14 days) under one `offer_group_id`, and is idempotent: re-importing a longer export adds only
the new posts. The real export is not committed; `tests/fixtures/telegram_export_synthetic.json` is a
synthetic file in the same shape so the tests and a clean checkout work without it.

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
