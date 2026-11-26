# Competitive Price Intelligence for a Tashkent Flower Shop

> **DRAFT of 20 November 2026.** Every figure below is computed from assessed data collected
> 9–19 November 2026 and is reproducible by replaying the committed snapshot
> (`tools/load_snapshot.py data/snapshots/assessed-window --db data/report.db`, then
> `python -m priceintel analyse --db data/report.db --purpose assessed --replicates 5000`).
> Items that cannot be known yet are marked **[FINALISE]** and listed in `docs/report/TODO.md`.
> The submitted artefact is a PDF whose first page is the cover page below.

---

## Report cover page

| Required field | Value |
|---|---|
| University | University of Digital Economics and Agriculture (UDEA) |
| Module name | Data Science for Developers |
| Module code | UDE5014CM |
| Coursework type | Individual Coursework |
| Assessment | Assessment 2 — Individual Data Science and Database Development Project |
| Name of the work | Competitive Price Intelligence for a Tashkent Flower Shop |
| Student ID | 50000161 |
| Module Leader | Sanjar Bekov |
| Academic year and semester | 2026/27 — Semester 1 |
| Submission date and time | **[FINALISE]** DD December 2026, HH:MM, Asia/Tashkent |
| Main report word count | **[FINALISE]** (excluding references and appendices) |
| Coursework approval | Approved 3 November 2026 by University email from the Module Leader (subject: "Re: UDE5014CM Assessment 2 — updated method and Telegram collection route"); transcript in `docs/emails/2026-11-03-approval-decision.md` |
| GitHub repository URL | https://github.com/dilmurod-tolipov/rep_for_UDE5014CM |
| Assessed branch | `main` |
| Full final commit hash | **[FINALISE]** 40-character hash of the final commit |
| AI Use Declaration | Yes — full declaration in Report Section 6 |

---

## Contents

1. Introduction, Stakeholder Problem, Personalised Objectives and Rationale
2. Data Collection System, Database, Pipeline and Feature Engineering
3. Statistical Analysis, Modelling, Evaluation, Results and Interpretation
4. Integrated Application, Automated Testing and Reproducibility
5. Critical Evaluation, Ethics, Security and Scalability
6. Conclusion, Professional Communication, Referencing and AI Use
- References
- Appendix A — Checkpoint evidence register
- Appendix B — LO1, LO2 and LO5 evidence map
- Appendix C — Entity-relationship diagram
- Appendix D — Data-quality checks and selected test results
- Appendix E — AI Use Declaration log references

---

## Report Section 1: Introduction, Stakeholder Problem, Personalised Objectives and Rationale

**Stakeholder and problem.** Secret is a small flower, berry and houseplant shop in Tashkent. Its
owner sets prices from memory and occasional glances at competitors' websites; Tashkent has no
published flower price index, so he has no dated evidence of where Secret sits against the shops his
customers compare it with. The decision this project supports is narrow: **which categories should
he examine first when reviewing prices.** It cannot recommend a price — it sees advertised prices
only, not demand or margin.

**Approved scope and boundaries.** The Module Leader approved the project on 3 November 2026 and set
the assessed collection window to 9 November – 6 December 2026 (`docs/approval/APPROVED-SCOPE.md`).
The design collects **primary data** from four independent competitor operator groups by reading
their public catalogues, and treated Secret's own prices as **reference data** from a single export
of the shop's public channel. They are **not** in the submitted analysis: the Module Leader
requires Secret's written confirmation for that use, and the shop could not be reached to ask
for it, so the comparison is between competitors only (ADR-010). Four mirror sites are registered and never
crawled, so one operator cannot be counted four times (ADR-001). Observations are advertised
catalogue prices in UZS excluding delivery; promotions are recorded but analysed separately.

**Objectives and success criteria** (as approved; achievement is the state on 19 November):

| # | Objective | Success criterion | Achieved to date |
|---|---|---|---|
| O1 | Reliable collection | ≥95% of **scheduled** runs reach every group, counting any that never started | **Not met** — 23 of 34 slots (67.6%); 22 consecutive clean |
| O2 | Enough evidence | ≥300 listings from ≥4 independent sources | **Met** — 2,571 products, four groups |
| O3 | Valid comparison | ≥10 usable products each side (plan v2.0) | **Partly** — two competitor categories qualify; Secret is absent, so no Secret comparison is made |
| O4 | Honest evaluation | State whether a model beats the baseline | **Met** — both do (Section 3) |
| O5 | Decision support | Dashboard names the category to examine first | **Met** — `/decision`, CP4 |

**Analytical questions, rationale and value.** (Q1) Within a category, do the operator groups
advertise the same price level? (Q2) How far is Secret's median from each competitor's, with an
uncertainty interval? (Q3) What predicts a listing's price, and can a model beat a category-median
baseline? Q1 and Q3 are answered here from system-collected data; Q2 is implemented and tested but
reports `insufficient_evidence` until Secret's export is imported — stated, not estimated.

## Report Section 2: Data Collection System, Database, Pipeline and Feature Engineering

**Collection method and provenance.** The collector (`priceintel/collect/`) is written from scratch
in Python 3.13 over the standard library plus `requests` and `BeautifulSoup`. It reads `robots.txt` before every crawl, through a hand-written
parser rather than `urllib.robotparser`, which ignores `*` wildcards and would have mis-read three
of the four sites, then requests only allowed paths with a 5-6 s delay and an identifying agent. GitHub Actions
runs it twice a day and derives the run's `purpose` from the date, so assessed and development data
cannot be confused by hand (ADR-005). Every HTTP attempt is logged with its status, size, duration
and SHA-256 content hash; every observation points at the fetch that produced it, the run, and the
run's git commit plus a dirty flag, and a `CHECK` constraint refuses an assessed run from modified
code. By 26 November the system had made 3,120 logged requests across 35 assessed runs, storing
45,852 observations of 2,571 distinct products against an approved target of 300. Records failing
validation are not discarded but written to `rejected_records` with the rule that failed: 1.5% of
parsed records, almost all because the shop advertised no price. **[FINALISE on the final dataset.]**

**Database design.** Two SQLite databases, drawn in Appendix C. `market_intel` holds the collection
chain `shops` -> `listings` -> `price_observations`, with `scrape_runs`, `fetch_log` and
`rejected_records` recording how each row came to exist, the derived analysis tables, dated
`shop_delivery_terms`, and Secret's `reference_offers`; `secret_shop` holds Secret's catalogue and
its operational core. Every table is `STRICT`, so SQLite's permissive typing cannot store a string
in a price column, and integrity is enforced by the schema rather than by application code. The constraints that carry the most weight are `UNIQUE (listing_id, run_id)`, which makes a re-run
idempotent and a duplicate observation structurally impossible; a partial unique index allowing
only one active canonical domain per operator group, so one business cannot be counted four times
(ADR-001); and `NOT NULL` `is_synthetic` on every operational table, propagated by triggers, so a
fabricated row cannot pass as real. SQLite cannot enforce a foreign key between two files, so the single link between the
databases - one shared category vocabulary - is checked in code by the pipeline, by every dashboard
page load, by `check-integrity` and by the tests. Schema changes are numbered migrations whose SHA-256 is stored
on application; retrieval is through five named stakeholder queries and a JSON API. Two parts of the schema hold no real rows and are built so that cannot be faked: Secret's
operational rows are declared fixtures, and `shop_delivery_terms` ships empty because an invented
fee would be fabricated evidence about a named business (ADR-009). 

**Cleaning, transformation and features.** `python -m priceintel pipeline` builds one analysis row
per product and records every decision it makes: of 2,571 products, 119 matched no analysis
category, 298 are priced per stem and so are not comparable with whole arrangements, 1,396 advertise
only a starting price ("от"), and 47 were flagged as outliers - leaving **758 usable products**.
Three choices were corrected after seeing real data. Starting prices are **kept and labelled**, not
dropped: dropping them silently removed most of the largest operator group. Outliers are **flagged,
never removed**, and judged within one category and one operator group, because judging them across
all groups flagged all 19 of one shop's rose bouquets; the median absolute deviation falls back to
IQR/1.349 when it is zero. Nothing is imputed. Features derive the price unit, stem count, size and flower types from the title and composition
text, using a versioned, **price-independent** rules file whose SHA-256 is registered in the
database and whose loader rejects any rule key it does not recognise, so price cannot reach the
feature that decides comparability. Leakage is prevented structurally - splits are grouped so every
observation of a listing falls in one fold, the baseline and all preprocessing are fitted on
training folds only, and reference offers cannot reach a model matrix, which a test proves.

**Difficult conditions and corrections.** Three failures are on the record, each with its issue,
fix and test in the evidence register. Scheduled collection failed silently for eleven days in
October, because expired artifacts could not be distinguished from a failed download (`1cd776d`).
Early runs lost an entire operator group to `robots.txt` timeouts yet reported success, because the
skipped shop's pages were never requested and so never counted; migration 011 records groups
expected and reached, and 11 runs were re-marked `partial` (`88b75d2`). On 13 November the largest
site redesigned its theme: pages returned 200, the parser found nothing, and every aggregate measure
stayed green - so the parser now reads both layouts and a **per-group** freshness check fails on the
first run a source goes quiet (`60949a5`). 

## Report Section 3: Statistical Analysis, Modelling, Evaluation, Results and Interpretation

**Exploratory analysis.** Six labelled figures are generated by `python -m priceintel analyse` into
`docs/analysis/figures/` (coverage, median price, price distribution, observations per day,
the spread between groups, and discounting). They show a market whose advertised
prices are extremely right-skewed: within usable products the roses category spans
25,000–31,031,000 UZS, and skewness inside a single group reaches 6.3. Coverage is also very uneven: 484 of the 758 usable products are
mono-flower roses, and 2,346 of the 2,571 collected come from one operator group.

**Hypothesis test (Q1).** For each category, H0 is that the operator groups' price distributions are
the same, tested by Kruskal–Wallis (Kruskal and Wallis, 1952) across groups holding at least ten
usable products, with Holm correction across categories (Holm, 1979) and ε² as the effect size. Two
categories qualified and both reject H0: unspecified bouquets, H = 34.45, p = 4.4 × 10⁻⁹ (Holm-adjusted
8.8 × 10⁻⁹), ε² = 0.263, n = 129; mono-flower roses, H = 25.21, p = 5.1 × 10⁻⁷, ε² = 0.050, n = 484.
Assumptions are recorded with each result rather than assumed: for bouquets the group shapes are
comparable (skewness 3.9 and 5.9; IQR/median 1.07 and 0.69), so the result reads as a difference in
level, while for roses the shapes differ, so it is reported as stochastic dominance, not a median
difference. Pairwise permutation tests (10,000 permutations) size the gap: in bouquets PROBUKET's
median is 965,840 UZS above UZFLORA's (p = 1.0 × 10⁻⁴, probability of superiority 0.84), and in roses
PROBUKET is 1,152,350 UZS above LOVEFLOWERS_NET (p = 2.0 × 10⁻⁴). Three categories report
**insufficient evidence** with the reason, which is designed behaviour, not a failure.

**Secret's price position (Q2): not answered.** The approved estimand is 100 x (Secret median /
competitor median - 1) per category and group, with a percentile bootstrap interval (B = 5,000)
in which Secret's sample is drawn once per replicate, so the intervals share one draw. It is
implemented and tested, and it reports `insufficient_evidence` for all 13 category-and-group
cells, because Secret's offers were never imported. Secret publishes its prices on a public
channel, but publication records where a price came from, not permission to use it in assessed
work: the Module Leader ruled on 26 November 2026 that Secret's written confirmation was needed,
and the shop could not be reached to obtain it. Rather than use the prices anyway, they are left
out entirely, which is the course he directed. The importer is exercised by nine tests against a
labelled synthetic export. What remains is a comparison **between competitors**, and the
competitor medians are real: in roses, LOVEFLOWERS_NET 475,000 UZS against PROBUKET 1,627,350 UZS.

**What the comparison does not establish.** A category median compares the *assortments* two shops
advertise, not two equivalent products. Secret's posts rarely name a flower type and never a stem
count, so no per-product matching is attempted (`product_matches` is deliberately not built,
ADR-009): a 243% gap in roses may reflect larger bouquets, better stems or more elaborate
presentation at the dearer shop as much as a higher price for the same thing. That is why the output
is "look here first" and not "you are overpriced".

**Models (Q3).** Target: a product's median advertised price. Features: category, operator group,
price unit, stem count, size and flower-type indicators — nothing price-derived. Baseline: the
category median, fitted on training folds only. Comparators: ridge regression (Hoerl and Kennard,
1970) and a decision tree (Breiman et al., 1984), both from scikit-learn (Pedregosa et al., 2011),
each tuned on an inner split of the training folds. Validation is 5-fold cross-validation grouped by listing, with
leave-one-group-out and chronological splits also stored. Pooled results:

| Model | MAE (UZS) | MdAPE (%) |
|---|---|---|
| Category-median baseline | 850,985 | 57.2 |
| Ridge regression | 368,570 | 32.9 |
| Decision tree | 395,797 | 25.1 |

Both beat the baseline. Ridge is better on absolute error, the tree on relative error — consistent
with a skewed target in which the tree isolates the cheapest segment well but is penalised on a few
very expensive bouquets. Error analysis by category shows where they are weak: for potted plants the
tree's MdAPE is 22.2% against ridge's 114.7%, on 17 products — too few to report as a finding.

**Robustness and uncertainty.** Nine checks run with the analysis. Dropping each operator group in
turn is the decisive one: **removing PROBUKET leaves no category with two qualifying groups, so every
significant result disappears.** Removing LOVEFLOWERS_NET or UZFLORA leaves one testable category,
which still differs; so does restricting to products whose price unit the shop stated rather than
inferred. Excluding the flagged outliers leaves both results significant. The window-half check
cannot yet discriminate, as all current products were first seen in the first half. The ninth check
asks whether the findings are an artefact of which shops happened to answer, since eleven runs lost
a group. Restricted to the 14 days on which **every** group reported - 7.7% of regular-price observations
discarded, every remaining product re-priced from those days alone - both categories still differ
and no category median moves at all. The conclusions do not depend on the incomplete days.

**Interpretation against the decision.** The honest reading is narrow. Two categories show that these
sampled shops demonstrably do not price alike, with a spread in roses of 243% between the dearest and
cheapest qualifying group, and that is what the dashboard tells the owner to examine first. But the
result rests on one shop, it describes four sampled operators over eleven days rather than the
Tashkent market, and it says nothing about whether **Secret** is dear or cheap, because
Secret's prices are not in the dataset and, on the evidence available, cannot be. It names a category to inspect; it is not evidence that changing a price would raise revenue.

## Report Section 4: Integrated Application, Automated Testing and Reproducibility

**Architecture and workflow.** The system is one Python package with five stages joined by the
database: `collect` → `classify` → `pipeline` → `analyse` → the dashboard. `python -m priceintel
refresh` runs the chain in order and **stops at the first stage that fails**, so a half-updated
dashboard is never presented as current, and prints the decision at the end. The principal
input-to-output workflow is: a competitor publishes a price → the scheduled collector stores it with
provenance → cleaning and feature extraction make it comparable → tests and models re-run → the
dashboard's "What to look at" page ranks the categories and the owner reads which one to examine,
with the evidence one click away on the Analysis and Models pages. The dashboard is a stdlib
`http.server` application with inline SVG charts and no front-end build step; routing is a pure
function, which is why most of it is testable without a running server, and where no analysis has
been built it names the command to run instead of showing a blank page.

**Testing.** **331 automated tests pass** (`python -m pytest -q`), spanning unit tests of the robots
parser, price validation, category rules and feature extraction; data-validation tests for invalid,
boundary and failure cases (out-of-range prices, missing prices, a currency served in USD, a run
refused from modified code, a shop that returns 200 with no products); and 14 end-to-end tests in
`tests/test_end_to_end.py`. The central one is the checkpoint's own claim: it collects from a scripted
fetcher standing in for the four shops, reads the decision, lets one shop double its prices, collects
again, and asserts that the decision the dashboard shows moves with it — everything downstream of
the fetcher is the real code. The reason to trust these tests is that they have caught real defects:
a classifier reading a URL product slug as a section, the silent-source condition that went unnoticed
for five runs, and the decision page's single-product ranking defect.

**Reproducibility.** Repository `https://github.com/dilmurod-tolipov/rep_for_UDE5014CM`, assessed
branch `main`, full final commit hash **[FINALISE]**. No API key, account or paid service is needed.
From a clean checkout: `python -m venv .venv`, `pip install -r requirements.txt` (pinned),
`python -m priceintel init-db`, `python -m pytest -q`, then either `python -m priceintel refresh` to
collect live or — the route a marker should prefer, because it needs no network and reproduces the
reported numbers — `python tools/load_snapshot.py data/snapshots/assessed-window --db data/report.db`
followed by `python -m priceintel refresh --db data/report.db --no-collect` and
`python -m priceintel dashboard`. The snapshot is committed CSV with a manifest and a SHA-256 per
file, and a round-trip test asserts it is self-contained, after an earlier version was found not to
be. This procedure was run from a clean `git worktree` checkout of `cp4` on 20 November: 276 tests
passed, replay reported `integrity: OK`, and the decision reproduced as *"look at roses_mono first —
the dearest group's median is 243% above the cheapest"*. **[FINALISE: repeat from a clean checkout of
the final commit and record the date and result.]**

## Report Section 5: Critical Evaluation, Ethics, Security and Scalability

**Technical and methodological limits.** The sample is four operator groups over eleven days of a
28-day window, and it is badly unbalanced: 91% of collected products come from one group, while
another publishes prices for only seven. Of 2,571 products just 758 are usable, mainly because 1,396
advertise a starting price only — so the usable set is not a random sample of the market but the
subset whose shops publish a definite price, which plausibly skews towards simpler, standardised
items. Every significant result depends on one shop: dropping PROBUKET removes them all, and only two
of five categories could be tested. Advertised prices are not transaction prices, and nothing here
measures demand or margin. The models are evaluated on unseen listings rather than a future period, so their numbers are not
forecast accuracy. Finally, the comparison the project was approved to produce - Secret
against the market - is absent, because the shop's written confirmation could not be obtained
and its prices were therefore not used. That is the single largest limitation here: one of three
analytical questions goes unanswered, and the stakeholder value is correspondingly narrower.

**Ethics, legality and privacy.** Only public catalogue pages are read, `robots.txt` obeyed before every
crawl, and the one site that disallows crawling is never crawled. No personal data is collected
anywhere: the data are product titles and prices, no real customer or order record exists, and a
real client could not be stored without recorded consent while the only contact column is the
last four digits of a phone number. A
prior design that scraped Secret's own public Telegram channel twice a day was withdrawn and the
data deleted after the Module Leader questioned whether it was primary data; the replacement is a
single manual export of that public channel, storing only each post's date, link, price and short
title, with contact lines stripped and no personal data at all. I first judged that Secret's own
publication of the prices was a sufficient basis on its own; the Module Leader ruled otherwise on
26 November 2026, and he is right that publication documents provenance rather than permission.
Secret's prices are therefore used only with its written confirmation covering this use and the
sharing with assessors, and are omitted entirely without it (ADR-010). The audit that found the scheduler still calling the
withdrawn collector for eleven days was disclosed in writing rather than quietly fixed. Remaining
exposure: a site's terms may change after the date recorded in
`docs/compliance/`, and the export, once imported, is commercially sensitive pricing in a local
database. **Security.** The system has no users, no credentials and no
listener beyond a localhost dashboard, which removes most of the attack surface rather than
defending it; the dashboard bounds every query parameter and parameterises all SQL. It binds to
`127.0.0.1` and must not be exposed as-is: with no authentication, publishing it would publish the
owner's price position.

**Scalability, maintainability and operations.** SQLite at twice-daily writes is comfortable at this scale
and would remain so at ten times it, though the append-only observation table would need archival
within a year. The real fragility is not volume but **source drift**: collection depends on four third-party HTML layouts,
and one redesign silently emptied the largest source for five runs. The per-group freshness check now
catches that class of failure on the first run, which is the most valuable piece of operational
engineering in the project. Prioritised improvements: import Secret's export and complete the comparison, which is the
project's purpose; alert on a failing quality check rather than only recording it, since the
13-day silent failure was found by hand; and widen the sample to more operators publishing
definite prices, which is what would make more than two categories testable. 

## Report Section 6: Conclusion, Professional Communication, Referencing and AI Use

**Conclusion.** Objectives O2–O5 were met: the system collects its own primary data (2,571 distinct
products, 23,144 observations, each traceable to its request, run and commit), and produces a dated
answer to the owner's question of where to look — two categories in which the sampled shops
demonstrably do not price alike, a 243% spread in roses, and three where the evidence is explicitly
too thin. Both models beat the category-median baseline (MAE 368,570 UZS, MdAPE 25.1%, against
850,985 UZS and 57.2%). O1 was **not** met: 23 of 34 scheduled runs reached every operator group,
67.6% against the approved 95%, counting one slot that never started at all, from `robots.txt`
timeouts and a site redesign; both are fixed and the last 22 runs are clean, but with 11 failures on
the record the target would need 220 runs to recover and is unreachable inside the window. The main limitation is that Secret's own prices are absent: the
price-position comparison the project exists to produce is implemented and tested but could not
be run, because the shop could not be reached for the written confirmation the Module Leader
requires. The recommendation is to treat the findings as a statement about four
sampled shops, act on them only as a prompt to inspect a category, and obtain the shop's written
confirmation before any future run that would put Secret's own prices back into the comparison.

**Development story.** The four checkpoints are git tags, each runnable from a clean checkout: `cp1`
(`1cd776d`, 187 tests) collection MVP; `cp2` (`35ba260`, 215 tests) reliable collection, quality
checks and cleaning; `cp3` (`82b5f29`, 259 tests) the statistics; `cp4` (`7341057`, 276 tests) the
integrated system. Appendix A links each decision and failure to its evidence: Telegram collection withdrawn
(ADR-007), the approval clarifications implemented before collection began (ADR-008), the
dishonest run status (migration 011), the silent parser breakage and the single-product decision
ranking. Two tags were moved after landing on the
wrong commit, documented rather than rewritten out of the history.

**AI Use Declaration.** AI assistance was material and is declared. **Google AI Studio (Gemini)**
scaffolded the pre-approval React demo storefront, disclosed as existing work and not checkpoint
evidence. **Claude Code (Opus)** was used throughout the assessed work: to review the proposal
against the brief, to write the collector, migrations, category rules, feature extraction, cleaning
pipeline, statistics, dashboard and tests, and to draft documentation and emails for my review. I directed the design decisions, chose the hypothesis
design, and sent all correspondence myself. AI output was verified, not accepted: by tests (331, several written to reproduce a defect before
fixing it), by running the code against live pages, and by mutation checks in which a deliberately
broken rule was confirmed to fail tests. Errors
caught that way are logged — a classifier reading a URL slug as a section, a potted orchid read as a
single cut stem, an outlier rule that flagged all 19 of one shop's rose bouquets, and a permutation
test whose passing was a lucky seed. It also declined twice: to invent Secret's prices, and to write
unverified counts into correspondence. The dated, per-commit record is `docs/ai-use-log.md`.

---

## References

Breiman, L., Friedman, J.H., Olshen, R.A. and Stone, C.J. (1984) *Classification and Regression
Trees*. Belmont, CA: Wadsworth.

Efron, B. and Tibshirani, R.J. (1993) *An Introduction to the Bootstrap*. New York: Chapman & Hall.

Hoerl, A.E. and Kennard, R.W. (1970) 'Ridge regression: biased estimation for nonorthogonal
problems', *Technometrics*, 12(1), pp. 55–67.

Holm, S. (1979) 'A simple sequentially rejective multiple test procedure', *Scandinavian Journal of
Statistics*, 6(2), pp. 65–70.

Koster, M., Illyes, G., Zeller, H. and Sassman, L. (2022) *Robots Exclusion Protocol*. RFC 9309.
Internet Engineering Task Force. Available at: https://www.rfc-editor.org/rfc/rfc9309 (Accessed:
20 November 2026).

Kruskal, W.H. and Wallis, W.A. (1952) 'Use of ranks in one-criterion variance analysis', *Journal of
the American Statistical Association*, 47(260), pp. 583–621.

Pedregosa, F. et al. (2011) 'Scikit-learn: machine learning in Python', *Journal of Machine Learning
Research*, 12, pp. 2825–2830.

SQLite Consortium (2026) *STRICT Tables*. Available at: https://www.sqlite.org/stricttables.html
(Accessed: 20 November 2026).

Vargha, A. and Delaney, H.D. (2000) 'A critique and improvement of the CL common language effect size
statistic of McGraw and Wong', *Journal of Educational and Behavioral Statistics*, 25(2), pp. 101–132.

Wirth, R. and Hipp, J. (2000) 'CRISP-DM: towards a standard process model for data mining', in
*Proceedings of the 4th International Conference on the Practical Applications of Knowledge Discovery
and Data Mining*, pp. 29–39.

---

## Appendix A — Checkpoint evidence register

Reproduced from `docs/evidence-register.md` in the assessed repository, which holds the four
checkpoint states with full commit hashes, the substantive change and verified test results at each,
the value statement per checkpoint, and nine requirement/defect → issue → implementation →
verification → closure chains.

## Appendix B — LO1, LO2 and LO5 evidence map

| LO | Evidence | Where |
|---|---|---|
| LO1 data-mining lifecycle | ADR-001–008, approval record, four checkpoint records | Sections 1, 5, 6; `docs/decisions/` |
| LO2 database and collection | Two schemas with STRICT tables and constraints, 13 migrations, provenance chain, ten recorded quality checks, five stakeholder queries, snapshot replay | Section 2, 4; CP1, CP2 |
| LO5 statistical analysis | Kruskal–Wallis with Holm and assumption checks, permutation tests, bootstrap B = 5,000, baseline plus two models under grouped CV, eight robustness checks | Section 3; CP3 |

## Appendix C — Entity-relationship diagram

`docs/analysis/figures/er_diagram.svg`, one page, generated by `python tools/er_diagram.py` and
checked against the live schema by `tests/test_er_diagram.py`. It is laid out by what the data
**is**, so the three kinds cannot be confused: collected competitor data (primary), derived analysis
tables, Secret's reference offers, and the synthetic operational core. The keys and constraints that
matter are explained in Section 2.

## Appendix D — Data-quality checks and selected test results

Twelve checks on the assessed data, recorded as 15 rows because per-group freshness is measured
once per operator group. **[FINALISE: re-run on the final dataset.]** On 26 November 2026: products
collected 2,571 (threshold 300) **pass**; runs completed 35 (threshold 50) **fail**;
scheduled-slot completion 67.6% (threshold 95%) **fail** — 23 of 34 elapsed slots, one of which
never started; run success rate of the runs that started 68.6% **fail**; consecutive complete runs
22 (reported, not judged); quarantine rate 1.5% (≤5%) pass; unclassified rate 4.6% (≤25%) pass;
price-outlier rate 1.2% (≤2%) pass; freshness and per-group freshness, four groups, all pass;
duplicate observations 0 pass; orphan observations 0 pass. Overall **fail**, driven by the
collection-volume and reliability criteria.

Full test output, run logs and per-run coverage are in the repository rather than here:
`python -m pytest -q` (331 passing), `docs/evidence-register.md`, and the `v_run_coverage` view.

## Appendix E — AI Use Declaration log references

`docs/ai-use-log.md` — 21 dated entries from 21 September to 20 November 2026, each naming the tool,
purpose, output, the check applied and the commit.
