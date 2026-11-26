# What the report still needs

The draft is `docs/report/final-report.md`. Everything in it is computed from assessed data collected
9–19 November 2026. These items cannot be settled yet.

## Blocking (cannot be written before the date)

| # | Item | Earliest date | Who |
|---|---|---|---|
| 1 | Collection window closes; final assessed dataset complete | 6 Dec 2026 | automatic (the scheduled workflow stops by date) |
| 2 | ~~Secret's written confirmation~~ **Settled 26 Nov: it cannot be obtained** (no contact for the shop), so the Module Leader's fallback applies — no export, no import, Secret omitted, limitation explained (ADR-010) | done | — |
| 3 | ~~Import and re-run the comparison~~ **Not applicable.** If the shop is somehow reached before submission: obtain the confirmation, store it beside ADR-010, `import-reference`, re-run `analyse --replicates 5000`, and restore Section 3's Q2 paragraph, the O3 row in Section 1, and the limitation sentences in Sections 5 and 6 | only if reached | me |
| 4 | Re-run every figure in the report against the final dataset — Sections 2, 3, 5, 6 and Appendix C all cite counts that will change | 7 Dec | me |
| 5 | Clean-checkout verification of the **final** commit; record the date, the test count and the reproduced decision in Section 4 | after the last commit | me |
| 6 | Cover page: submission date and time, main report word count, full 40-character final commit hash | at submission | me |

## Non-blocking, before submission

- **Word budget.** Sections 1-6 are **3830** words (tables and headings included) against
  "approximately 3,500": 445 / 904 / 846 / 509 / 585 / 541 against the brief's guidance of
  400 / 750 / 900 / 500 / 550 / 400. Section 2 is the one over, after ADR-009 added the
  operational core and delivery terms; Section 3 has room to grow when the Secret comparisons
  land. Cut Section 2's table-by-table detail and Section 6's conclusion before the AI
  declaration, which is worth 1 of Section 6's 2 marks.
- **Figures.** Decide which of the six SVGs in `docs/analysis/figures/` go into the PDF. The brief
  requires clearly labelled visualisations in Section 3 and penalises unanalysed screenshots, so each
  one included must be referred to in the text.
- **Appendix A** is a reproduction of `docs/evidence-register.md`; regenerate it after the final
  commit so the four hashes and test counts match.
- **PDF build.** First page must be the cover page. A missing or unclear mandatory cover-page field
  caps the report at 10/20; a missing or invalid repository URL or final commit hash is 0/100 overall.
- **Built after cp4 (ADR-009):** the `secret_shop` operational core with synthetic fixtures, and
  dated `shop_delivery_terms`. Two things remain owed in the report: `shop_delivery_terms` is
  still **empty** until each competitor's delivery page is read and recorded with
  `record-delivery-terms`, and `product_matches` is deliberately not built (ADR-009 gives the
  reason, and Section 2 says so).
- **Still not built, and a statement is owed in Section 5 if they stay that way:** the ER
  diagram and the normalisation rationale (neither is required by the brief, which asks for
  entities, keys and constraints to be *explained*), and a dated backup/restore evidence run -
  the commands and tests exist, the written evidence does not.
- **Viva (40 marks).** Every method choice in `priceintel/analysis/hypothesis.py`, the cleaning
  decisions in `pipeline.py`, and every database constraint must be mine to explain and modify.
