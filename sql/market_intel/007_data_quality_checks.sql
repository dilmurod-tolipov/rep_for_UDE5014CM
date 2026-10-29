-- market_intel migration 007: recorded data-quality checks
--
-- The validator already refuses bad records one at a time (rejected_records). This table answers the
-- different question the brief asks for at Checkpoint 2: is the dataset as a whole fit to analyse?
-- Each check runs over the stored data, records a measured value against a threshold, and passes,
-- warns or fails. Results are kept, not printed and forgotten, so the report can show the quality of
-- the data on the day the analysis was run, and a check that starts failing is visible as a change.

CREATE TABLE data_quality_checks (
    check_run_id INTEGER PRIMARY KEY,
    run_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    purpose      TEXT    NOT NULL CHECK (purpose IN ('dev', 'assessed', 'test')),
    check_name   TEXT    NOT NULL,
    scope        TEXT    NOT NULL,            -- 'all', an operator group, or a category
    measured     REAL    NOT NULL,
    threshold    REAL,
    unit         TEXT    NOT NULL CHECK (unit IN ('count', 'percent', 'days')),
    status       TEXT    NOT NULL CHECK (status IN ('pass', 'warn', 'fail')),
    detail       TEXT
) STRICT;

CREATE INDEX ix_data_quality_run_at ON data_quality_checks (run_at, purpose);

-- The latest result of every check, which is what a dashboard shows.
CREATE VIEW v_data_quality_latest AS
SELECT q.*
FROM data_quality_checks q
WHERE q.check_run_id = (SELECT q2.check_run_id FROM data_quality_checks q2
                        WHERE q2.check_name = q.check_name
                          AND q2.scope      = q.scope
                          AND q2.purpose    = q.purpose
                        ORDER BY q2.run_at DESC, q2.check_run_id DESC
                        LIMIT 1);
