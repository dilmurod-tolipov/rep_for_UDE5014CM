# AI use log

Representative, dated record of material AI assistance (brief: "Use of Generative AI").
Each entry gives the tool, the purpose, what was produced, and how it was checked by the student.

| Date | Tool | Purpose | AI output | How it was checked / changed | Commit(s) |
|---|---|---|---|---|---|
| before 2026-09-21 | Google AI Studio (Gemini) | Scaffold the pre-approval demo storefront | React/Vite storefront + admin UI | Edited by the student; disclosed as existing work, not checkpoint evidence | `baseline-demo` |
| 2026-10-17 | Claude Code (Opus) | Review the revised proposal against the brief | Gaps list (Secret price source, Wilcoxon minimum n, evidence map) | Student compared each point with the brief | — |
| 2026-10-17 | Claude Code (Opus) | Compliance reconnaissance of competitor sites | robots.txt/terms summary, catalogue-overlap script | Student to open each robots.txt/terms page and confirm the table in `docs/compliance/` | scaffold commit |
| 2026-10-17 | Claude Code (Opus) | Repository scaffold and docs | `.gitignore`, requirements, ADR-001, scope summary | Student to review every document; approval date filled in by the student | scaffold commit |
| 2026-10-17 | Claude Code (Opus) | market_intel schema v1, migration runner, `init-db`/`db-info` CLI, schema tests (issue #2) | `sql/market_intel/001_core.sql`, `priceintel/db.py`, `priceintel/cli.py`, `tests/test_schema.py` | 12 tests pass; `init-db` run twice to confirm idempotence. AI corrected itself: the column `trigger` was renamed `triggered_by` (SQL keyword). Student to read every constraint and be able to explain each in the viva | schema commit |

> Prompt/output excerpts that are material go in `docs/ai-log/YYYY-MM-DD-topic.md`.
