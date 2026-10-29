# ADR-006: Analysis categories from a versioned, price-independent rules file

- **Date:** 2026-10-29 (Week 8)
- **Status:** Accepted for implementation; the rules file is committed and tagged before any
  analysis run. **Rules 1.1.0** (2026-10-29) is the version in force; 1.0.0 was tagged earlier the
  same day and had been applied to development data only. The categories themselves were accepted by the Module Leader (email 26/10/2026,
  point 2: "Define categories independently of price").
- **Related:** ADR-001 (operator groups), ADR-004 (within-category comparison),
  Module Leader feedback 26/10/2026 points 2-4 and the addendum in preparation.
- **Files:** `config/category_rules.v1.json`, `priceintel/analysis/categories.py`,
  `sql/market_intel/003_listing_categories.sql`, `tests/test_categories.py`

## Context

The primary analysis compares Secret's median advertised price with each competitor group's median
**within a category**. The categories therefore decide the result, so they must be fixed in advance,
derived from something other than price, and explainable item by item in the viva.

## Decision

### 1. Rules live in a versioned file, not in code

`config/category_rules.v1.json` holds the categories, the exclusions, the section rules and the
flower-type lexicon. It carries a `rules_version` and is tagged in git before the first analysis run.
`priceintel/analysis/categories.py` only applies it. Every assignment stored in the database records
the rules version **and the SHA-256 of the rules file**; re-using a version for different content is
refused (`register_rules`), exactly as for schema migrations.

### 2. Only three inputs, none of them a price

A rule may match on the product **title**, the **section part of the URL** and the **shop's own
section slugs** (`listings.site_category`). `load_rules` rejects any other matcher key, so a rule that
looked at a price could not even be loaded (`test_rules_cannot_match_on_price`).

Three kinds of slug are deliberately **not** used as signals, because they describe price, a promotion
or an occasion rather than a product type:

| Not used | Example | Why |
|---|---|---|
| Price bands | `nedorogie-czvety` ("cheap flowers") | using it would make the category depend on price |
| Promotions | `aktsii-rozy`, `topsale` | depends on the current offer, not the product |
| Occasions | `8-marta`, `14-fevralya` | the same bouquet appears in and out of season |

A listing whose only slugs are of these kinds falls through to the title rules, and is counted as
`unclassified` if the title says nothing either (15 of 154 in the development crawl).

The **last segment of a product URL is also ignored**: it only repeats the title
(`/product/belye-rozy/`). Treating it as a section labelled the mixed bouquet "Розы и лилии" as a
mono-bouquet; the bug and its regression test (`test_product_slug_is_not_a_section`) are kept as
evidence of the correction.

### 3. Categories

| Code | Meaning |
|---|---|
| `roses_mono` | roses and mono-bouquets: exactly one flower type named |
| `mixed_bouquets` | two or more flower types named |
| `bouquets_unspecified` | a bouquet whose composition the listing or post does not state |
| `boxes_baskets` | flowers in a box or basket |
| `potted_plants` | potted / houseplants |
| `edible_sets` | edible and berry sets (strawberries in chocolate, sweets, fruit) |
| `out_of_scope` | explicitly excluded: balloons, vases, toys, cakes, cards (not flowers) |
| `unclassified` | no rule matched |

`bouquets_unspecified` is new relative to the proposal and is the honest consequence of feedback
point 3 ("Record missing flower types and stem counts as unknown"): the composition of a bouquet named
"Нежный флёр" is unknown, and is **not** assumed to be mixed. Under the count-only merge rule, the
three bouquet categories merge into one `bouquets` category **before any price is looked at** if any of
them has fewer than 10 distinct Secret offers; the development crawl (94 of 154 uzflora listings
unspecified, 3 mono, 0 mixed) suggests the merge will be needed, and the decision will be logged with
the counts that triggered it.

`out_of_scope` and `unclassified` are both excluded from the analysis but are **counted and reported**,
so coverage can be judged. Nothing is silently dropped.

### 4. Matching is whole-word and deterministic

Text is lower-cased, "ё" is folded to "е", every non-alphanumeric character becomes a space, and a
keyword must match between spaces. So "Розовое сердце" (pink heart) does not match the rose keyword
"розы", while "Белые розы" does. Rules are tried in file order, exclusions first, and the first match
wins, so a balloon listed in the bouquet section is out of scope rather than a bouquet.

### 5. One assignment per listing per rules version

`listing_categories (listing_id, rules_version)` is the primary key, with the rule id and the evidence
string ("site_category=rasteniya", "title~клубника") stored next to it. Re-classifying is idempotent;
a new rules version adds a new set of rows beside the old one instead of overwriting history.

## Consequences

- The roses / mixed split depends on the listing naming its flowers. On uzflora, and in Secret's
  Telegram captions, it usually does not, so the comparison will in practice be run on merged
  bouquet categories. The report must say so rather than present a mono-vs-mixed finding.
- Known over-inclusion risk: the generic words "сладкий / сладкое / сладкая" ("sweet") put gift
  listings such as "Сладкое свидание" into `edible_sets`. They sit in the shop's `podarki` section and
  are most likely sweet sets, but the title alone does not prove it. A sensitivity check that
  re-classifies without the generic sweetness words and recomputes the comparison is planned, and the
  count of listings it moves will be reported.
- Chocolates sold as bouquet add-ons (`k-buketu`) are `out_of_scope` while comparable sweets sold as
  products in `podarki` are `edible_sets`. The unit of analysis is a product, not an add-on.
- Changing a rule after results exist requires a new `rules_version`, which is visible in the database
  and in the report.
- The flower lexicon is reused for the flower-type-restricted secondary comparison (feedback point 3).

## Changes in rules 1.1.0 (2026-10-29)

All three came from running 1.0.0 against real text, and none of them uses price, a promotion or an
occasion, so the price-independence of the rules is unchanged.

1. **The words "букет" and "композиция" in a title** are now bouquet evidence (rule S05). Secret's
   channel captions are marketing lines with no section slug ("Прекрасные букеты для любимой"), so
   under 1.0.0 most of its offers were unclassified: 104 of 123 observed posts, against 64 under
   1.1.0.
2. **Inflected flower names** ("с тюльпанами и пионами") are listed in the lexicon. Matching is
   whole-word, so every form has to be spelled out; a missing form silently made a mixed bouquet look
   unspecified.
3. **Plain Russian section names** ("Букеты", "Растения", "Каталог букетов") were added beside the
   URL slugs, because kamilas.uz publishes its category as schema.org text rather than as a slug.

The counts each version produces are reported together in `docs/analysis_plan.md`, and
`listing_categories` keeps both sets of assignments side by side.
