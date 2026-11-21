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
- Appendix C — Data-quality checks and selected test results
- Appendix D — AI Use Declaration log references

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
their public catalogues, and treats Secret's own prices as **reference data** supplied once by the
owner as a consented Telegram Desktop export (ADR-007). Four mirror sites are registered and never
crawled, so one operator cannot be counted four times (ADR-001). Observations are advertised
catalogue prices in UZS excluding delivery; promotions are recorded but analysed separately.

**Objectives and success criteria** (as approved; achievement is the state on 19 November):

| # | Objective | Success criterion | Achieved to date |
|---|---|---|---|
| O1 | Reliable collection | ≥95% of 12-hourly runs reach every group | **Not met** — 11 of 22 (50%); last 11 clean |
| O2 | Enough evidence | ≥300 listings from ≥4 independent sources | **Met** — 2,571 products, four groups |
| O3 | Valid comparison | ≥10 usable products each side (plan v2.0) | **Partly** — two categories qualify; Secret's side empty |
| O4 | Honest evaluation | State whether a model beats the baseline | **Met** — both do (Section 3) |
| O5 | Decision support | Dashboard names the category to examine first | **Met** — `/decision`, CP4 |

**Analytical questions, rationale and value.** (Q1) Within a category, do the operator groups
advertise the same price level? (Q2) How far is Secret's median from each competitor's, with an
uncertainty interval? (Q3) What predicts a listing's price, and can a model beat a category-median
baseline? Q1 and Q3 are answered here from system-collected data; Q2 is implemented and tested but
reports `insufficient_evidence` until Secret's export is imported — stated, not estimated. The
owner's alternative is manual checking: slow, undated, unrepeatable. A collector that records
provenance for every price turns an impression into a record, and the minimum-evidence rule makes the
system say "not enough evidence" rather than invent a comparison — which is what makes it usable for
a real pricing decision.

## Report Section 2: Data Collection System, Database, Pipeline and Feature Engineering

**Collection method and provenance.** The collector (`priceintel/collect/`) is written from scratch
in Python 3.13 over the standard library plus `requests` and `BeautifulSoup`. For each operator group
it reads `robots.txt` first, through a hand-written parser rather than `urllib.robotparser`, which
ignores `*` wildcards and would have mis-read three of the four sites; it then requests only allowed
paths, with a per-host crawl delay of 5–6 s and an identifying user agent. GitHub Actions runs it twice a day and derives the run's `purpose` from the date, so assessed
and development data cannot be confused by hand (ADR-005). Every HTTP attempt is written to
`fetch_log` with its status, size, duration and SHA-256 content hash; every observation points at
the fetch that produced it, the run, and the run's git commit plus a dirty flag, and a `CHECK`
constraint refuses an assessed run from modified code. In the window 9–19 November the system
made **1,820 logged requests (1,755 returning HTTP 200)** across **22 assessed runs**, storing
**23,144 in-window observations of 2,571 distinct products** against an approved target of 300.
Records failing validation are not discarded but written to `rejected_records` with the rule that
failed: 478 of 23,840 parsed records (2.0%), 462 because the shop advertised no price.

**Database design.** Two SQLite databases are used. `market_intel` holds the collection entities
(`shops` → `listings` → `price_observations`, with `scrape_runs`, `fetch_log`, `rejected_records` and
`data_quality_checks` recording how each row came to exist) and eight analysis tables from
`listing_features` to `model_metrics`, plus dated `shop_delivery_terms`; `secret_shop` holds
Secret's catalogue and its operational core (`clients`, `addresses`, `orders`, `order_items`,
`payments`, `admin_users`). SQLite cannot enforce a foreign key between two files, so the link
between them — one shared category vocabulary, plus the rule that no own-shop, reference or
synthetic row may enter the primary data — is checked in code by the pipeline, by every dashboard
page load, by `check-integrity` and by the tests (`priceintel/integrity.py`). The per-product
`product_matches` table in the proposal is **not built**: comparison is by category, which is what
the approved analysis plan v2.0 tests, so it would be unused scaffolding (ADR-009). Every table is
`STRICT`, so SQLite's permissive typing cannot silently store a string in a price column.
Integrity is enforced by the schema rather than application code: foreign keys on every relationship
(the self-referencing `offer_group_id` is `DEFERRABLE INITIALLY DEFERRED` so a group's first member
can be inserted), `CHECK` constraints on price range and currency, a partial unique index permitting
only one active canonical domain per operator group, and `UNIQUE (listing_id, run_id)`, which makes
a re-run idempotent and duplicate observations structurally impossible. Schema changes are numbered
migrations whose SHA-256 is stored on application, so editing an applied one stops `init-db`.
Retrieval is through five named stakeholder queries in `sql/queries/` and a JSON API. Two parts of
the schema hold no real rows, and are built so that cannot be faked: Secret records no orders
digitally, so every operational row carries a `NOT NULL` `is_synthetic` flag that triggers propagate
and the dashboard reports in its own column, and `shop_delivery_terms` ships empty because an
invented fee would be fabricated evidence about a named business (ADR-009).

**Cleaning, transformation and features.** `python -m priceintel pipeline` builds one analysis row
per product from the stored observations and records every decision it makes
(`pipeline_runs`): of 2,571 products, 119 matched no analysis category, 298 are priced per stem and
so are not comparable with whole arrangements, 1,396 advertise only a starting price ("от"), and 47
were flagged as outliers — leaving **758 usable products**. Three choices were corrected after seeing
real data. Starting prices are **kept and labelled**, not dropped: dropping them silently removed
most of the largest operator group. Outliers are **flagged, never removed**, and judged within one
category and one operator group, because judging them across all groups flagged all 19 of one shop's
rose bouquets; the median absolute deviation falls back to IQR/1.349 when it is zero. Nothing is
imputed. Feature engineering (`priceintel/analysis/features.py`) derives `price_unit` (per item,
bundle or stem), `stem_count`, `size_cm` and flower types from the title and composition text, using
a versioned, **price-independent** rules file whose SHA-256 is registered in the database; the loader
rejects any rule key it does not recognise, which is how price is kept out of the feature deciding
comparability. Leakage is prevented structurally: splits are grouped so every observation of a
listing falls in one fold, the baseline and all preprocessing are fitted on training folds only, and
reference offers are excluded from model matrices by a test that fails if one appears.

**Difficult conditions and corrections.** Three failures are on the record. Scheduled collection
failed silently for eleven days in October, because expired artifacts could not be distinguished
from a failed download (`1cd776d`). Five early assessed runs lost an entire operator group to
`robots.txt` timeouts yet reported success, because the skipped shop's pages were never requested
and so never counted; migration 011 records groups expected and reached, and 11 runs were re-marked
`partial` (`88b75d2`). On 13 November the largest site redesigned its theme: pages returned 200, the
parser found nothing, and every aggregate measure stayed green — so the parser now reads both
layouts and a **per-group** freshness check fails on the first run a source goes quiet (`60949a5`).
The value created is a dated competitor price record that did not exist before, in which every
number traces to the request, run and commit that produced it.

## Report Section 3: Statistical Analysis, Modelling, Evaluation, Results and Interpretation

**Exploratory analysis.** Six labelled figures are generated by `python -m priceintel analyse` into
`docs/analysis/figures/`: usable products and median price per category and group (Figures 1–2), the
price distribution (3), observations per day by group (4), the spread between the dearest and
cheapest group (5), and the share of products on sale (6). They show a market whose advertised
prices are extremely right-skewed: within usable products the roses category spans
25,000–31,031,000 UZS, and skewness inside a single group reaches 6.3. That fact drives every later
method choice — parametric tests are inappropriate here, so medians, rank tests and resampled
intervals are used throughout. Coverage is also very uneven: of the 758 usable products, 484 are
mono-flower roses, 134 unspecified bouquets, 105 boxes and baskets, 18 edible sets and 17 potted
plants; 2,346 of the 2,571 collected products come from LOVEFLOWERS_NET against 154, 64 and 7.

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

**Secret's price position (Q2).** The approved estimand is
100 × (Secret median ÷ competitor median − 1) per category and operator group, with a percentile
bootstrap interval (B = 5,000) in which Secret's sample is drawn once per replicate and reused across
that category's groups so the intervals share the same Secret draw. All **13** comparisons currently
return `insufficient_evidence` ("needs 10 of each") because Secret's export has not yet been
imported. The competitor medians are nevertheless informative and are shown: in roses,
LOVEFLOWERS_NET 475,000 UZS against PROBUKET 1,627,350 UZS. **[FINALISE after 6 December: import the
owner's export and report the Secret comparisons with their intervals.]**

**Models (Q3).** Target: a product's median advertised price. Features: category, operator group,
price unit, stem count, size and flower-type indicators — nothing price-derived. Baseline: the
category median, fitted on training folds only. Comparators: ridge regression (Hoerl and Kennard,
1970) and a decision tree (Breiman et al., 1984), both from scikit-learn (Pedregosa et al., 2011),
each tuned on an inner split of the training folds. Validation is 5-fold cross-validation grouped by
listing (n_train 3,032, n_validation 758), with leave-one-operator-group-out and chronological splits
also stored. Pooled results:

| Model | MAE (UZS) | MdAPE (%) |
|---|---|---|
| Category-median baseline | 850,985 | 57.2 |
| Ridge regression | 368,570 | 32.9 |
| Decision tree | 395,797 | 25.1 |

Both beat the baseline. Ridge is better on absolute error, the tree on relative error — consistent
with a skewed target in which the tree isolates the cheapest segment well but is penalised on a few
very expensive bouquets. Error analysis by category shows where they are weak: for potted plants the
tree's MdAPE is 22.2% against ridge's 114.7%, on 17 products — too few to report as a finding.

**Robustness and uncertainty.** Eight checks run with the analysis. Dropping each operator group in
turn is the decisive one: **removing PROBUKET leaves no category with two qualifying groups, so every
significant result disappears.** Removing LOVEFLOWERS_NET or UZFLORA leaves one testable category,
which still differs; so does restricting to products whose price unit the shop stated rather than
inferred. Excluding the flagged outliers leaves both results significant. The window-half check
cannot yet discriminate, as all current products were first seen in the first half.

**Interpretation against the decision.** The honest reading is narrow. Two categories show that these
sampled shops demonstrably do not price alike, with a spread in roses of 243% between the dearest and
cheapest qualifying group, and that is what the dashboard tells the owner to examine first. But the
result rests on one shop, it describes four sampled operators over eleven days rather than the
Tashkent market, and it cannot yet say whether **Secret** is dear or cheap, because Secret's prices
are not in the dataset. The finding is actionable in one way only — it names the category to inspect,
and the category pages list the comparable products — and it is not evidence that changing a price
would increase revenue.

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

**Testing.** **316 automated tests pass** (`python -m pytest -q`), spanning unit tests of the robots
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
measures demand or margin. The models are evaluated on unseen listings, not a future period — the
window holds too few price changes — so their numbers are not forecast accuracy. Finally, the
comparison the project was approved to produce, Secret against the market, is not yet computed, and
the report says `insufficient_evidence` rather than estimating it.

**Ethics, legality and privacy.** Only public catalogue pages are read; `robots.txt` is parsed and
obeyed before every crawl, with polite delays, an identifying user agent and a recorded compliance
status per shop, and one site that disallows crawling is registered and never crawled. No personal
data is collected: the data are product titles and prices, and no customer, courier or order record
from Secret is used, and a real client could not be stored without recorded consent while the only
contact column is the last four digits of a phone number — data minimisation by schema, not policy. A
prior design that scraped Secret's own public Telegram channel was withdrawn and the data deleted
after the Module Leader questioned whether it was primary data; the replacement is a one-off export
the owner supplies with written consent (ADR-007), and the audit that found the scheduler had kept
calling the withdrawn collector for eleven days was disclosed in writing rather than quietly fixed.
Remaining exposure: a site's terms may change after the date recorded in `docs/compliance/`, and the
owner's export, once imported, is commercially sensitive pricing in a local database. **Security.**
The system has no users, no credentials and no network listener beyond a localhost dashboard, which
removes most of the attack surface rather than defending it. The dashboard bounds every query
parameter, returns 400 with a message on bad input, and parameterises all SQL. It binds to
`127.0.0.1` and must not be exposed as-is: with no authentication, publishing it would publish the
owner's price position.

**Scalability, maintainability and operations.** SQLite with twice-daily writes is comfortable at the
current scale (23,144 observations) and would remain so at ten times it, but the append-only
observation table grows without bound and would need archival within a year of running. The real
fragility is not volume but **source drift**: collection depends on four third-party HTML layouts,
and one redesign silently emptied the largest source for five runs. The per-group freshness check now
catches that class of failure on the first run, which is the most valuable piece of operational
engineering in the project. Prioritised improvements: (1) import the owner's export and complete the
Secret comparison — it is the project's purpose; (2) alert on a failing quality check rather than only
recording it, since the 13-day silent failure was found by hand; (3) widen the sample to more
operators publishing definite prices, which is what would make more than two categories testable.

## Report Section 6: Conclusion, Professional Communication, Referencing and AI Use

**Conclusion.** Objectives O2–O5 were met: the system collects its own primary data (2,571 distinct
products, 23,144 observations, each traceable to its request, run and commit), and produces a dated
answer to the owner's question of where to look — two categories in which the sampled shops
demonstrably do not price alike, a 243% spread in roses, and three where the evidence is explicitly
too thin. Both models beat the category-median baseline (MAE 368,570 UZS, MdAPE 25.1%, against
850,985 UZS and 57.2%). O1 was **not** met: 11 of 22 assessed runs reached every operator group, 50%
against the approved 95%, from `robots.txt` timeouts and a site redesign; both are fixed and the last
11 runs are clean, but the target cannot be recovered inside the window. The value is a standing,
twice-daily answer to "where should I look?" that previously required manual checking and left no
record. The main limitation is that Secret's own prices are not yet in the dataset, so the
price-position comparison the project exists to produce is implemented, tested — and empty. The
recommendation is to import the owner's export once the window closes, treat the findings as a
statement about four sampled shops, and act on them only as a prompt to inspect a category.

**Development story.** The four checkpoints are git tags, each runnable from a clean checkout: `cp1`
(`1cd776d`, 187 tests) collection MVP; `cp2` (`35ba260`, 215 tests) reliable collection, quality
checks and cleaning; `cp3` (`82b5f29`, 259 tests) the statistics; `cp4` (`7341057`, 276 tests) the
integrated system. They differ in kind: CP1 could store a price, CP4 turns a new price into changed
advice. Appendix A links each decision and failure to its evidence — Telegram collection withdrawn
(ADR-007, issues #7 and #9), the approval clarifications implemented before collection began
(ADR-008, `ecac792`), the dishonest run status (migration 011, `88b75d2`), the silent parser breakage
(`60949a5`) and the single-product decision ranking (`cp4`). Two tags were moved after landing on the
wrong commit, documented rather than rewritten out of the history.

**AI Use Declaration.** AI assistance was material and is declared. **Google AI Studio (Gemini)**
scaffolded the pre-approval React demo storefront, disclosed as existing work and not checkpoint
evidence. **Claude Code (Opus)** was used throughout the assessed work: to review the proposal
against the brief, to write the collector, migrations, category rules, feature extraction, cleaning
pipeline, statistics, dashboard and tests, and to draft documentation and emails for my review. I
directed the design decisions, chose the hypothesis design, supplied the sources and consent
arrangements, and sent all correspondence myself. AI output was verified, not accepted: by tests
(316, several written to reproduce a defect before fixing it), by running the code against live
pages, and by mutation checks in which a deliberately broken rule was confirmed to fail tests. Errors
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

## Appendix C — Data-quality checks and selected test results

Ten checks on the assessed data, 19 November 2026, recorded as 13 rows because per-group freshness is
measured once per operator group: products collected 2,571 (threshold 300) **pass**; runs completed
22 (threshold 50) **fail**; run success rate 50% (threshold 95%) **fail**; quarantine rate 2.0% (≤5%)
pass; unclassified rate 4.6% (≤25%) pass; price-outlier rate 1.4% (≤2%, 35 products above ten times
their category median — a wider rule than the pipeline's within-group MAD flag) pass; freshness 0.67
days (≤1) pass; per-group freshness, four groups, all pass; duplicate observations 0 pass; orphan
observations 0 pass. Overall status **fail**, driven by the two collection-volume criteria. Test suite: 316 passing tests; selected results in Section 4.

## Appendix D — AI Use Declaration log references

`docs/ai-use-log.md` — 21 dated entries from 21 September to 20 November 2026, each naming the tool,
purpose, output, the check applied and the commit.
