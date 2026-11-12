-- market_intel migration 012: the analysis dataset, and the record of how it was made
--
-- The brief requires an automated pipeline that performs "ingestion, schema checking, cleaning,
-- integration, transformation and feature engineering" and that addresses "missing values,
-- duplicates, invalid records, data types and outliers using justified decisions". Until now the
-- project collected and validated records, and each query computed its own medians. That is not a
-- pipeline: the decisions were implicit in five SQL files and could drift apart.
--
-- These three tables make the dataset and its construction explicit.
--
--   pipeline_runs     one row per build: the code version, the window, the rules version, the git
--                     commit, and how many rows each stage kept or dropped. A reader can see, in
--                     numbers, what cleaning did - and a later build can be compared with an earlier
--                     one instead of silently replacing it.
--   analysis_products one row per competitor product per build: its summarised price and the reason
--                     it is or is not used. Excluded rows are KEPT with their reason rather than
--                     deleted, so "excluded" is a number the report can show, not an absence.
--   dataset_splits    which fold each product belongs to, written once per build, so model
--                     evaluation cannot quietly reshuffle them.

CREATE TABLE pipeline_runs (
    pipeline_run_id INTEGER PRIMARY KEY,
    pipeline_version TEXT   NOT NULL,
    purpose         TEXT    NOT NULL CHECK (purpose IN ('dev', 'assessed', 'test')),
    window_start    TEXT    NOT NULL,
    window_end      TEXT    NOT NULL,
    rules_version   TEXT    NOT NULL REFERENCES category_rule_sets (rules_version),
    git_commit      TEXT    NOT NULL,
    git_dirty       INTEGER NOT NULL CHECK (git_dirty IN (0, 1)),
    built_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    -- Stage counts: every row is accounted for, so the numbers add up in the report.
    observations_in           INTEGER NOT NULL DEFAULT 0,
    observations_from_price   INTEGER NOT NULL DEFAULT 0,  -- "от 22 000": dropped, not a product price
    observations_used         INTEGER NOT NULL DEFAULT 0,
    products_in               INTEGER NOT NULL DEFAULT 0,
    products_no_category      INTEGER NOT NULL DEFAULT 0,  -- unclassified / out_of_scope
    products_per_stem         INTEGER NOT NULL DEFAULT 0,  -- a stem price is not an assortment price
    products_starting_price_only INTEGER NOT NULL DEFAULT 0, -- only ever advertised "от X"
    products_outliers_flagged INTEGER NOT NULL DEFAULT 0,  -- flagged, never dropped
    products_included         INTEGER NOT NULL DEFAULT 0,
    CHECK (window_end >= window_start),
    CHECK (observations_used = observations_in - observations_from_price),
    CHECK (products_included = products_in - products_no_category - products_per_stem
                             - products_starting_price_only)
) STRICT;

CREATE TABLE analysis_products (
    pipeline_run_id   INTEGER NOT NULL REFERENCES pipeline_runs (pipeline_run_id),
    listing_id        INTEGER NOT NULL REFERENCES listings (listing_id),
    operator_group    TEXT    NOT NULL,
    category          TEXT,
    price_unit        TEXT,
    stem_count        INTEGER,            -- NULL stays NULL: a stem count is never imputed
    -- The regular price is the median over the window of the shop's own regular price
    -- (its old price where a sale is shown). One product contributes one value, however
    -- many times it was observed.
    regular_price_uzs INTEGER,
    sale_price_uzs    INTEGER,            -- median of the current prices, for the sensitivity check
    n_observations    INTEGER NOT NULL CHECK (n_observations > 0),
    observed_days     INTEGER NOT NULL CHECK (observed_days > 0),
    first_observed_at TEXT    NOT NULL,
    last_observed_at  TEXT    NOT NULL,
    price_changes     INTEGER NOT NULL DEFAULT 0,
    days_on_sale      INTEGER NOT NULL DEFAULT 0,
    availability_last TEXT,
    is_outlier        INTEGER NOT NULL DEFAULT 0 CHECK (is_outlier IN (0, 1)),
    included          INTEGER NOT NULL CHECK (included IN (0, 1)),
    exclusion_reason  TEXT,
    PRIMARY KEY (pipeline_run_id, listing_id),
    CHECK ((included = 1) = (exclusion_reason IS NULL)),
    CHECK (included = 0 OR regular_price_uzs IS NOT NULL)
) STRICT;

CREATE INDEX ix_analysis_products_run_category
    ON analysis_products (pipeline_run_id, category, operator_group);

CREATE TABLE dataset_splits (
    pipeline_run_id INTEGER NOT NULL REFERENCES pipeline_runs (pipeline_run_id),
    listing_id      INTEGER NOT NULL REFERENCES listings (listing_id),
    split_kind      TEXT    NOT NULL CHECK (split_kind IN ('grouped_cv', 'leave_one_group_out',
                                                           'chronological')),
    fold            INTEGER NOT NULL CHECK (fold >= 0),
    part            TEXT    NOT NULL CHECK (part IN ('train', 'validation', 'test')),
    PRIMARY KEY (pipeline_run_id, listing_id, split_kind, fold)
) STRICT;

CREATE INDEX ix_dataset_splits_lookup ON dataset_splits (pipeline_run_id, split_kind, fold, part);

-- The dataset of the most recent build: what the analysis and the dashboard read.
CREATE VIEW v_analysis_dataset AS
SELECT p.*
FROM analysis_products p
WHERE p.pipeline_run_id = (SELECT MAX(pipeline_run_id) FROM pipeline_runs)
  AND p.included = 1;
