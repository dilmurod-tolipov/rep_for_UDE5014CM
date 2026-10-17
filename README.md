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
docs/            approval record, decisions (ADRs), compliance checks, evidence register, AI log
storefront/      React demo storefront + admin (pre-approval baseline, see docs/baseline)
```

More folders (`priceintel/`, `sql/`, `tests/`, `data/`) are added at CP1.

## Setup

Requires Python 3.13 and Git.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

Collection, database and test commands are documented here as each checkpoint lands.

## Ethics in one paragraph

Only public product information is collected (title, price, old price, availability, URL, time).
No personal data, images or descriptions are stored. robots.txt is honoured on every run, requests
are rate-limited and identified, and every record keeps its source URL. Any customer, order or payment
records in `secret_shop` are synthetic, flagged `is_synthetic`, and never used in the analysis.
See `docs/compliance/`.
