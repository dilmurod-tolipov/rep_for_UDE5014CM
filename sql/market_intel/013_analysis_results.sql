-- market_intel migration 013: analysis and model results (Checkpoint 3)
--
-- The proposal promised these tables and the brief asks for reproducible estimates: a figure in the
-- report must be traceable to the build that produced it, the data it used and the code that was
-- running. Results are stored, not printed and lost, so re-running the analysis after more data has
-- arrived produces a new row rather than a silently different number.

CREATE TABLE comparison_results (
    comparison_id    INTEGER PRIMARY KEY,
    pipeline_run_id  INTEGER NOT NULL REFERENCES pipeline_runs (pipeline_run_id),
    computed_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    variant          TEXT    NOT NULL,   -- 'main' or the robustness check that produced it
    category         TEXT    NOT NULL,
    operator_group   TEXT    NOT NULL,   -- a competitor group, or 'ALL' for the pooled figure
    n_products       INTEGER NOT NULL CHECK (n_products >= 0),
    n_secret_offers  INTEGER NOT NULL DEFAULT 0 CHECK (n_secret_offers >= 0),
    competitor_median_uzs INTEGER,
    secret_median_uzs     INTEGER,
    difference_uzs        INTEGER,
    difference_pct        REAL,
    ci_low_pct            REAL,          -- 95% percentile bootstrap interval
    ci_high_pct           REAL,
    bootstrap_replicates  INTEGER,
    evidence         TEXT    NOT NULL CHECK (evidence IN ('displayed', 'insufficient_evidence')),
    note             TEXT
) STRICT;

CREATE INDEX ix_comparison_results_run ON comparison_results (pipeline_run_id, variant);

CREATE TABLE hypothesis_tests (
    test_id         INTEGER PRIMARY KEY,
    pipeline_run_id INTEGER NOT NULL REFERENCES pipeline_runs (pipeline_run_id),
    computed_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    question        TEXT    NOT NULL,   -- the hypothesis, in words
    scope           TEXT    NOT NULL,   -- the category it was tested in
    method          TEXT    NOT NULL,   -- e.g. 'kruskal_wallis', 'permutation_median_difference'
    statistic       REAL,
    p_value         REAL    CHECK (p_value IS NULL OR (p_value >= 0 AND p_value <= 1)),
    p_adjusted      REAL    CHECK (p_adjusted IS NULL OR (p_adjusted >= 0 AND p_adjusted <= 1)),
    effect_name     TEXT,
    effect_size     REAL,
    effect_ci_low   REAL,
    effect_ci_high  REAL,
    n_groups        INTEGER,
    n_observations  INTEGER,
    assumptions     TEXT,               -- what was checked, and what it showed
    conclusion      TEXT    NOT NULL
) STRICT;

CREATE TABLE model_runs (
    model_run_id    INTEGER PRIMARY KEY,
    pipeline_run_id INTEGER NOT NULL REFERENCES pipeline_runs (pipeline_run_id),
    trained_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    model_name      TEXT    NOT NULL,   -- 'category_median_baseline', 'ridge', 'decision_tree'
    split_kind      TEXT    NOT NULL,   -- which dataset_splits rows were used
    hyperparameters TEXT,               -- JSON, chosen on training folds only
    n_train         INTEGER NOT NULL CHECK (n_train > 0),
    n_validation    INTEGER NOT NULL CHECK (n_validation > 0),
    notes           TEXT
) STRICT;

CREATE TABLE model_metrics (
    model_run_id INTEGER NOT NULL REFERENCES model_runs (model_run_id),
    scope        TEXT    NOT NULL,      -- 'all' or a category
    metric       TEXT    NOT NULL,      -- 'mae_uzs', 'mdape_pct'
    value        REAL    NOT NULL,
    -- The fold the figure comes from, or POOLED (-1) for the figure over all folds together. A
    -- sentinel rather than NULL because these four columns are the primary key, and a STRICT
    -- table's key columns cannot be NULL.
    fold         INTEGER NOT NULL,
    PRIMARY KEY (model_run_id, scope, metric, fold)
) STRICT;

-- The headline of the most recent analysis: what the owner is shown.
CREATE VIEW v_latest_comparison AS
SELECT c.*
FROM comparison_results c
WHERE c.pipeline_run_id = (SELECT MAX(pipeline_run_id) FROM comparison_results)
  AND c.variant = 'main';
