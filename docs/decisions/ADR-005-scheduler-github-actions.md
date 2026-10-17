# ADR-005: Run the 12-hourly collection on GitHub Actions

- **Date:** 2026-10-17 (Week 6)
- **Status:** Accepted (dev purpose until approval is recorded)
- **Related:** objective O1 (every 12 h, >= 95% successful runs, missed runs count as failures); issues #6, #8

## Options

| Option | For | Against |
|---|---|---|
| Windows Task Scheduler on the student's laptop | Uzbek IP; simple | Laptop must be on at both times; every missed run counts as a failure against the 95% target |
| **GitHub Actions (chosen)** | Runs whether or not the laptop is on; every run is tied to an exact commit from a clean checkout (needed for `assessed` runs); logs kept by GitHub | Runners are outside Uzbekistan; databases must be carried between runs |

## Evidence from the probe workflow (`.github/workflows/probe.yml`, 2026-10-17)

1. t.me (Secret's channel) answers runners normally: 9 prices, 0 rejected.
2. uzflora.com shows **USD** to non-Uzbek visitors (vase $10, Ferrero Collection $20). The validator quarantined
   all 16 cards as `currency_not_uzs`, so no wrong price was stored.
3. With `?currency=UZS` the runner received **exactly** the UZS prices a run from Tashkent saved 40 minutes
   earlier (115,000 / 244,375 / 215,050). UZS is the shop's base currency; the USD figures are converted from it.
   The uzflora parser now always requests `currency=UZS` (regression test added). This also answers most of issue #8.

## Decision

- `.github/workflows/collect.yml` runs at 01:00 and 13:00 UTC (06:00 and 18:00 Tashkent) and on demand.
- Each run restores both databases from the previous successful run's artifact, runs `init-db` (migrations),
  collects competitors and Secret, snapshots Secret into market_intel (with the cross-database check),
  and uploads `backup`-verified copies as the next artifact (kept 90 days).
- If a previous run exists but its artifact cannot be downloaded, the job **fails** instead of starting from an
  empty database (no silent data loss).
- One run at a time (`concurrency: collector`).
- Purpose comes from the repository variable `COLLECT_PURPOSE` (default `dev`). After approval:
  `gh variable set COLLECT_PURPOSE --body assessed`.
- Dated database snapshots are committed to the repository at each checkpoint (`data/snapshots/`), so the
  marker never depends on GitHub artifacts.

## Consequences

- The success rate (O1) is computed from scheduled slots vs runs in `scrape_runs` with `triggered_by = 'scheduled'`.
  GitHub can delay or skip scheduled runs under load; such gaps count as failures, as the proposal says.
- The project still runs fully on a local machine (`python -m priceintel ...`); GitHub Actions is only the scheduler.
