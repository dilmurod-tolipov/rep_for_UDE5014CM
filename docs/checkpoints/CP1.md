# Checkpoint 1 — Data-Mining Lifecycle and Data Collection MVP (Week 7)

> Draft prepared in Week 6. Final values (commit hash, deadline, results from the clean-checkout run)
> are filled in when the `cp1` tag is created. Items marked **TODO** are not done yet.

## Submission fields

| Field | Value |
|---|---|
| Repository | https://github.com/dilmurod-tolipov/rep_for_UDE5014CM |
| Branch | `main` |
| Tag | `cp1` (TODO) |
| Full commit hash | TODO |
| Deadline | TODO (from the LMS) |
| Approval record | `docs/approval/APPROVED-SCOPE.md` (status and dated email history) |

## Independently executable component

A two-sided price collector that **accepts new input, validates it, saves it with provenance and lets the
new records be retrieved**:

- competitor catalogue scraper (uzflora.com) → `market_intel` (listings, price observations, fetch log);
- Secret's own prices from its public Telegram channel → `secret_shop`, copied to `market_intel` as `own_system`.

## Value statement

This component enables **the owner of Secret** to **see Secret's current prices next to dated competitor
prices** by **automatically collecting, validating and storing public product prices with their source,
time and collection run**, resulting in **a comparison dataset that refreshes itself without manual
price-checking** (first dev runs: 154 competitor prices in 52 s and 123 Secret prices in 70 s, unattended).

### Stakeholder-value measures (baseline vs achieved)

| Measure | Baseline (manual) | Achieved | Status |
|---|---|---|---|
| Time to record 100 prices with source and date | TODO: student times a manual copy of 20 prices and scales | about 34 s of collector time per 100 competitor prices (run 1), no attention needed | baseline to measure |
| Share of recorded prices traceable to a source page and time | TODO: manual notes usually keep no URL/time | 100% (database constraint) | done |

## Commands to reproduce (from a clean checkout)

```bash
python -m venv .venv
.venv\Scripts\activate                       # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest                              # automated tests
python -m priceintel init-db                  # both databases + shop registry
python -m priceintel collect --shop uzflora --max-pages 2   # new competitor records (dev)
python -m priceintel listings --limit 10      # retrieve them
python -m priceintel collect-secret --days 2  # new Secret records (dev)
python -m priceintel secret-prices --limit 10 # retrieve them
python -m priceintel snapshot-secret          # copy into market_intel; runs the cross-database check
```

## Test specification

| Purpose | Input | Expected output | Command | Acceptance criterion | Actual result |
|---|---|---|---|---|---|
| Valid input is saved | synthetic uzflora page with 2 valid cards | 2 listings + 2 observations | `pytest tests/test_collect_integration.py` | rows exist with price, URL, time | pass |
| Invalid input is quarantined | card without price; card priced in USD | 2 `rejected_records` rows with rules `missing_price`, `currency_not_uzs` | same | no observation stored for them | pass |
| Persistence and provenance | any saved observation | links to `fetch_log` (HTTP 200, SHA-256) and `scrape_runs` (40-char commit) | same + `tests/test_schema.py` | DB refuses observations without a matching fetch | pass |
| Polite collection | robots.txt disallowing page 2 | page 2 never requested; refusal logged | `pytest tests/test_collect_integration.py::test_robots_disallowed_page_is_never_requested` | no HTTP request to a disallowed URL | pass |
| Recovery | server answers 503 then 200 | both attempts logged; page saved | `...::test_server_error_is_retried_and_every_attempt_logged` | run status `success` | pass |
| Secret's prices | synthetic channel pages | 3 prices; 2 posts rejected; stop at 14-day cutoff | `pytest tests/test_secret_pipeline.py` | contacts not stored; dev never in assessed snapshot | pass |
| Live demo | real uzflora.com and t.me/secret_flowersuz | new records appear in `listings` / `secret-prices` | commands above | new rows with today's timestamp | pass on a fresh clone (2026-10-17); repeat at tag time |

Full suite at the time of writing: **62 passed** (also on a fresh clone).

## Substantive change (since project start)

Everything in `priceintel/`, `sql/`, `config/`, `tests/` and `docs/decisions/` is new after approval was
requested; `storefront/` is the disclosed pre-approval baseline (`git diff baseline-demo -- storefront/`
is empty at this checkpoint).

## Linked issues and decisions

| Item | Issue | Commit | Verification |
|---|---|---|---|
| Independent sources (ADR-001) | #1 (closed) | `fc9c5a0`, `f0ec61c` | recon script; schema test |
| market_intel schema | #2 (closed) | `f0ec61c` | 12 schema tests |
| Competitor scraper | #3 (closed) | `43b48bc` | integration tests; dev run 1 |
| Validation and quarantine | #4 (closed) | `43b48bc` | validation tests; mutation check |
| Secret's prices (ADR-002/003) | #7 (closed) | `f250170`, `c94c59d` | pipeline tests; dev run |
| Hypothesis design (ADR-004) | — | `b18bbf1` | awaiting Module Leader |
| Scheduler (ADR-005) | #6 (closed) | `d13bf3a`, `290a0ba` | two GitHub Actions runs; second restored the first's databases |
| Clean-checkout reproduction | #5 (open) | `1d00219` | `docs/evidence/clean-checkout-2026-10-17.md` (62 passed) |

## Known limitations / next steps

- Only one competitor parser (uzflora); pro-buket, loveflowers and kamilas follow at CP2.
- uzflora shows USD to foreign visitors; the collector forces UZS (ADR-005). Stability of UZS prices over days is checked at CP2 (issue #8).
- Scheduled runs (06:00/18:00 Tashkent) are in `dev` mode until approval is recorded.
- All data so far is `purpose = dev`; assessed collection starts only after approval is recorded.
- Secret captions rarely give flower type or stem count (ADR-003/004).

## AI assistance in this period

Claude Code (Opus) was used for reconnaissance, schema, collector, tests and documentation; see
`docs/ai-use-log.md` for what was produced and how it was checked.
