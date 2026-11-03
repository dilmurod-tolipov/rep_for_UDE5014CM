-- market_intel migration 009: engineered features per listing (ADR-008)
--
-- The analysis needs more than a category and a price. Two listings in `roses_mono` can be a single
-- rose stem at 18,000 UZS and a 101-stem bundle at 2,500,000 UZS; comparing their medians without
-- separating them compares nothing. This table holds what the text of a listing states about the
-- thing being priced:
--
--   price_unit   per_stem (the price buys one flower), per_bundle (a stated number of stems) or
--                per_item (one arrangement: a bouquet, box, basket or plant). Only per_item and
--                per_bundle listings enter the category price comparison; per_stem listings are
--                reported separately, because a stem price is not an assortment price.
--   stem_count   the number of stems the listing states ("101 шт", "розы — 15 шт"). NULL when the
--                listing does not say: it is never estimated, and never guessed from a photograph.
--   size_cm      a stated stem length or height ("60 см"), NULL otherwise.
--   flower_types the canonical flower types named in the text, from the rules file's lexicon. This
--                is what the flower-type-restricted secondary comparison uses.
--   evidence     'stated' when the value was read from the text, 'inferred' when a rule concluded it
--                from the absence of a quantity (per_stem). A robustness check re-runs the
--                comparison with inferred rows excluded.
--
-- Features are derived from text only - title, the shop's own composition line and the section slug -
-- so they can be recomputed from the saved data without re-collecting, and no price is ever an input
-- (the same rule as the categories).

CREATE TABLE listing_features (
    listing_id    INTEGER NOT NULL REFERENCES listings (listing_id),
    rules_version TEXT    NOT NULL REFERENCES category_rule_sets (rules_version),
    price_unit    TEXT    NOT NULL CHECK (price_unit IN ('per_stem', 'per_bundle', 'per_item')),
    stem_count    INTEGER CHECK (stem_count IS NULL OR stem_count BETWEEN 1 AND 1001),
    size_cm       INTEGER CHECK (size_cm IS NULL OR size_cm BETWEEN 5 AND 300),
    flower_types  TEXT,
    evidence      TEXT    NOT NULL CHECK (evidence IN ('stated', 'inferred')),
    rule_id       TEXT    NOT NULL,
    source_text   TEXT,                 -- the text the features were read from
    computed_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    PRIMARY KEY (listing_id, rules_version)
) STRICT;

CREATE INDEX ix_listing_features_unit ON listing_features (rules_version, price_unit);

-- What the comparison may use: a listing with a category, priced per item or per stated bundle.
CREATE VIEW v_comparable_listings AS
SELECT l.listing_id,
       s.operator_group,
       c.category,
       c.rules_version,
       f.price_unit,
       f.stem_count,
       f.flower_types
FROM listings l
JOIN shops              s ON s.shop_id    = l.shop_id
JOIN listing_categories c ON c.listing_id = l.listing_id
JOIN listing_features   f ON f.listing_id = l.listing_id
                         AND f.rules_version = c.rules_version
WHERE s.is_own_shop = 0
  AND c.category NOT IN ('out_of_scope', 'unclassified')
  AND f.price_unit <> 'per_stem';
