# Clean-checkout verification — 2026-10-17

Fresh `git clone` of https://github.com/dilmurod-tolipov/rep_for_UDE5014CM into an empty folder on Windows 11,
new virtual environment, only the commands in the README. No files copied from the development folder.

| Step | Command | Result |
|---|---|---|
| Commit | `git rev-parse HEAD` | `290a0ba040bc741f78f1065a37be06c7a349c8bf` |
| Install | `python -m venv .venv` + `pip install -r requirements.txt` | OK (Python 3.13) |
| Tests | `python -m pytest` | **62 passed** |
| Databases | `python -m priceintel init-db` | market_intel: 001, 002 applied, 10 shops; secret_shop: 001 applied, 1 channel |
| New competitor records | `python -m priceintel collect --shop uzflora --max-pages 2` | run 1 success, 2/2 pages, 32 observations, 0 rejected |
| Retrieval | `python -m priceintel listings --limit 2` | new rows shown with price, time, run, URL |
| New Secret records | `python -m priceintel collect-secret --days 1` | run 1 success, 9 prices |
| Retrieval | `python -m priceintel secret-prices --limit 2` | new rows shown with post link and times |
| Snapshot + integrity | `python -m priceintel snapshot-secret` | 9 own_system rows; cross-database check OK |
| Provenance | `python -m priceintel runs` | both runs carry commit `290a0ba040…`, not marked dirty |

Problem found: creating the virtual environment failed inside a very long folder path (Windows 260-character
limit while pip unpacks). Cloning into a short path worked; the README now says so.
