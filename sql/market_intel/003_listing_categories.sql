-- market_intel migration 003: analysis categories (ADR-006)
--
-- Categories are assigned from text only (title, URL path, the shop's own section slugs) by a
-- versioned rules file, never from price. The database stores:
--   * which rules file produced an assignment (version + SHA-256 of the file), so a result in the
--     report can be traced back to the exact rules that were in force;
--   * which rule fired and on what evidence, so every assignment can be explained;
--   * one assignment per listing per rules version, so re-classifying is idempotent and a new
--     rules version can be compared against the old one instead of overwriting it.

-- The category vocabulary, seeded from the rules file (`python -m priceintel classify`).
CREATE TABLE analysis_categories (
    code TEXT PRIMARY KEY
         CHECK (code GLOB '[a-z]*' AND code NOT GLOB '*[^a-z0-9_]*'),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0)
) STRICT;

-- One row per rules file version that has ever been applied to this database.
CREATE TABLE category_rule_sets (
    rules_version  TEXT PRIMARY KEY,
    effective_from TEXT,
    source_file    TEXT NOT NULL,
    sha256         TEXT NOT NULL CHECK (length(sha256) = 64),
    registered_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
) STRICT;

CREATE TABLE listing_categories (
    listing_id    INTEGER NOT NULL REFERENCES listings (listing_id),
    rules_version TEXT    NOT NULL REFERENCES category_rule_sets (rules_version),
    category      TEXT    NOT NULL REFERENCES analysis_categories (code),
    rule_id       TEXT    NOT NULL,   -- which rule fired, e.g. 'S02' or 'none'
    evidence      TEXT,               -- why, e.g. 'site_category=rasteniya'
    flower_types  TEXT,               -- canonical types named in the title, e.g. 'lily,rose'
    classified_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    PRIMARY KEY (listing_id, rules_version)
) STRICT;

CREATE INDEX ix_listing_categories_version_category
    ON listing_categories (rules_version, category);

-- Coverage of the latest classification, by operator group (the independence unit, ADR-001) and
-- category. Counts distinct listings, so repeated price snapshots cannot inflate them.
CREATE VIEW v_category_coverage AS
SELECT c.rules_version,
       s.operator,
       s.is_own_shop,
       c.category,
       COUNT(DISTINCT l.listing_id) AS n_listings
FROM listing_categories c
JOIN listings l ON l.listing_id = c.listing_id
JOIN shops    s ON s.shop_id    = l.shop_id
GROUP BY c.rules_version, s.operator, s.is_own_shop, c.category;
