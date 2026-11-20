# What the report still needs

The draft is `docs/report/final-report.md`. Everything in it is computed from assessed data collected
9–19 November 2026. These items cannot be settled yet.

## Blocking (cannot be written before the date)

| # | Item | Earliest date | Who |
|---|---|---|---|
| 1 | Collection window closes; final assessed dataset complete | 6 Dec 2026 | automatic (the scheduled workflow stops by date) |
| 2 | Owner's Telegram Desktop export + written consent wording | any time before 7 Dec | the owner (one file, once — he does not use the app) |
| 3 | `python -m priceintel import-reference` then re-run `analyse --replicates 5000`; fill in Section 3's Secret comparisons with their bootstrap intervals, and the pooled unweighted figure | 7 Dec | me |
| 4 | Re-run every figure in the report against the final dataset — Sections 2, 3, 5, 6 and Appendix C all cite counts that will change | 7 Dec | me |
| 5 | Clean-checkout verification of the **final** commit; record the date, the test count and the reproduced decision in Section 4 | after the last commit | me |
| 6 | Cover page: submission date and time, main report word count, full 40-character final commit hash | at submission | me |

## Non-blocking, before submission

- **Word budget.** Sections 1–6 are **3,691** words (tables and headings included) against
  "approximately 3,500": 445 / 786 / 846 / 509 / 564 / 541 against the brief's guidance of
  400 / 750 / 900 / 500 / 550 / 400. Section 3 has room to grow when the Secret comparisons land;
  Section 6 is the one over guidance, and its AI declaration is worth 1 of that section's 2 marks, so
  cut the conclusion or the development story there rather than the declaration.
- **Figures.** Decide which of the six SVGs in `docs/analysis/figures/` go into the PDF. The brief
  requires clearly labelled visualisations in Section 3 and penalises unanalysed screenshots, so each
  one included must be referred to in the text.
- **Appendix A** is a reproduction of `docs/evidence-register.md`; regenerate it after the final
  commit so the four hashes and test counts match.
- **PDF build.** First page must be the cover page. A missing or unclear mandatory cover-page field
  caps the report at 10/20; a missing or invalid repository URL or final commit hash is 0/100 overall.
- **Still missing from the v2 proposal's promised schema**, and so a statement is owed in Section 5
  if they stay unbuilt: `shop_delivery_terms`, `product_matches`, and the `secret_shop` operational
  core (`clients`, `addresses`, `orders`, `order_items`, `payments`, `admin_users`) with
  `is_synthetic` fixtures; also the ER diagram, the normalisation rationale, and a dated
  backup/restore evidence run.
- **Viva (40 marks).** Every method choice in `priceintel/analysis/hypothesis.py`, the cleaning
  decisions in `pipeline.py`, and every database constraint must be mine to explain and modify.
