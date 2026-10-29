# Draft email to the Module Leader, 29 October 2026 (not sent yet)

Status: draft prepared by the student with AI assistance (see `docs/ai-use-log.md`).
One date is left for the student to decide and is marked `[...]`. Everything else is factual and
verifiable in this repository.

---

**Subject:** Re: UDE5014CM Assessment 2 - correction about the Telegram collector, and the remaining
addendum figures

Dear Mr Bekov,

Thank you for your decision of 26 October. Two matters: a correction I must make straight away, and
the state of the addendum you asked for.

## 1. Correction: the Telegram collector kept running until today

When I wrote on 26 October that I had disabled the collector that read the channel's public web
preview, that was accurate for how I run the collector by hand, but not for the scheduled job that
runs it every 12 hours on GitHub Actions. That job went on calling it: 23 scheduled runs between
18 and 29 October 2026.

- Every one of those runs is recorded with `purpose = dev`. None of them is part of an assessed
  dataset, and no assessed collection has begun.
- I found this today while reviewing the repository before writing the addendum. I have removed the
  Telegram step, and the step that copied Secret's prices into the market database, from the
  scheduled job (commit `c75aee9`, 29 October 2026). The schedule now collects competitor
  catalogues only.
- I will delete the Telegram-derived development data, in my local databases and in the stored run
  artifacts, and remove the collector code itself.

I am sorry for the inaccurate statement. It was an oversight on my part rather than a deliberate
misdescription, and I would rather correct it now than let it stand in the record.

## 2. Primary data and the reference dataset (your point 1)

Accepted without reservation. The assessed primary data is what my competitor scrapers collect from
the four operator groups. Secret's own offers will be a small, separately identified reference
dataset in its own table (`reference_offers`), holding only the post date, post link, price, a short
product title, the derived category, the export date, the file hash and a repost group id. They will
never be written into `price_observations`, they do not count towards the primary-data target, and
neither do the CSV fallback imports. Secret's data is excluded from model training, tuning and
evaluation, and an automated test will prove that no reference row can reach a model matrix.

## 3. Categories are now fixed, and independent of price (your point 2)

The category rules are committed and tagged before any analysis: rules version 1.0.0, git tag
`category-rules-v1.0.0`, commit `7db976a20276863ee56fd77e2f877ad0e3e82bd2`.

- The only inputs are the product title, the section part of the product URL and the shop's own
  section slugs. Price, old price and sale state are never read, and the loader refuses any rule
  that tries to match on anything else.
- Three kinds of section are deliberately not used as evidence, because they describe price, a
  promotion or an occasion rather than a product type: price bands such as "nedorogie-czvety"
  (cheap flowers), promotion sections such as "aktsii-..." and "topsale", and occasions such as
  "8-marta".
- Categories: roses and mono-bouquets; mixed bouquets; bouquets of unstated composition; boxes and
  baskets; potted plants; edible and berry sets. Items that no rule matches are counted as
  unclassified and excluded, never silently dropped.
- Following your point 3, a bouquet whose composition the listing does not state is recorded as
  unstated rather than assumed to be mixed. In the development crawl of the one group my parsers
  already cover (uzflora, 17 October 2026, 154 distinct products), 94 products were bouquets of
  unstated composition, 3 were mono-bouquets and none named two or more flower types; 12 were
  edible sets, 8 potted plants, 22 out of scope (balloons, vases, toys, cakes) and 15 unclassified.
  I therefore expect to merge the three bouquet categories into one, by the count-only rule and
  before any price is examined, and to report the counts that triggered the merge.

## 4. Percentage comparison and bootstrap (your point 3)

- Percentage difference, stated exactly as you asked:
  100 x (Secret median price / competitor median price - 1), reported together with the median
  difference in UZS. A difference in log prices is never reported as a percentage.
- Bootstrap: B = 5,000 replicates within each category. Whole products are resampled, so all
  repeated observations of one product stay together. In each replicate the Secret reference sample
  is drawn once and reused for every competitor comparison, so the pooled result keeps their shared
  dependence; each competitor group's products are resampled independently. 95% percentile
  intervals. I do not bootstrap over the four businesses.
- Temporal dependence: with a 28-day window there are only four weekly blocks, so I report weekly
  medians descriptively and state that limitation, rather than claiming a week-block interval.
- The pooled summary uses only displayed comparisons and is the unweighted mean of the
  per-competitor percentages, so the largest catalogue does not dominate.

## 5. Modelling plan (your point 4)

Unchanged and explicit: a category-median baseline, ridge regression and a tree-based model, all on
competitor scraper data only. Grouped cross-validation keeps every observation of one product in the
same fold, with leave-one-operator-group-out as a sensitivity check; chronological evaluation is used
for future prices if enough price changes are observed, and I will say plainly if they are too rare.
Preprocessing and the baseline are fitted on training data only. I report MAE in UZS, the median
absolute percentage error and performance by category, and I evaluate whether either model improves
on the baseline and explain the result, including if the baseline wins. The LO evidence map now
includes the sampling rules and the primary/reference distinction.

## 6. Sampling plan (your point 2), and what is still missing

- Window: 28 days, starting on the first Monday after the date of your Approved decision.
- Cadence: competitor scrapers at 08:00 and 20:00 Asia/Tashkent, that is 56 scheduled runs. Targets:
  at least 50 completed runs and at least 300 distinct competitor products across the four groups. A
  completed run attempts all active shops' catalogue pages and finishes with a recorded status; a run
  is successful if at least 80% of requested pages return HTTP 200 and parse; the success rate is
  successful runs divided by scheduled runs, with missed runs counted as failures.
- Minimum evidence per displayed comparison: at least 10 distinct Secret offers and at least 10
  distinct products from that competitor group in that category. Below that I display "insufficient
  evidence" with the counts, rather than a comparison.
- Secret's offers: one distinct offer per publication date; reposts (normalised caption and the same
  price within 14 days) share a repost group id and count once. Older posts stay dated reference
  material and are never presented as new offers or as evidence of current availability.
- If Secret publishes too few relevant offers: at Day 21 I check each category, and extend the window
  to Day 42 only if the timeline allows; otherwise that category is reported as insufficient
  evidence.

The figures I cannot yet give honestly are the two tables of expected counts. My parsers currently
cover one of the four groups, so a four-group estimate would not be grounded in anything I have
collected. I am adding the three remaining parsers and will then run one development crawl across all
four groups, after which I will send the completed addendum with Table 1 (distinct products per
category and operator group, with the crawl date) and Table 2 (distinct Secret offers per category
per 28 days, estimated from an eight-week export divided by two). I expect to send it by
[date the student commits to].

No assessed data has been collected, and none will be until you record an Approved decision.

Kind regards,
Dilmurod Tolipov
Student ID: 50000161
