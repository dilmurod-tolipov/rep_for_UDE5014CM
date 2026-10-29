-- market_intel migration 005: Secret's offers as a separate reference dataset (ADR-007)
--
-- Module Leader, 26/10/2026, point 1: the owner-provided export is "a small, separately identified
-- reference dataset for Secret's descriptive comparison"; it does not count towards the primary-data
-- target, and it must stay out of machine learning.
--
-- Hence a table of its own, in no way joined to price_observations:
--   * no row here is ever a price observation, and nothing writes Secret prices into
--     price_observations any more (the own_system path is gone);
--   * only the fields the comparison needs are stored: date, link, price, a short title;
--   * every offer points at the import that produced it, with the file's SHA-256, so a figure in
--     the report can be traced to one export file;
--   * reposts of the same offer share an offer_group_id and are counted once.

CREATE TABLE reference_imports (
    import_id    INTEGER PRIMARY KEY,
    source_kind  TEXT    NOT NULL CHECK (source_kind IN ('telegram_export', 'csv')),
    file_name    TEXT    NOT NULL,
    file_sha256  TEXT    NOT NULL UNIQUE CHECK (length(file_sha256) = 64),
    exported_at  TEXT    NOT NULL,          -- date the owner produced the file
    imported_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    purpose      TEXT    NOT NULL CHECK (purpose IN ('dev', 'assessed', 'test')),
    rows_read    INTEGER NOT NULL DEFAULT 0 CHECK (rows_read >= 0),
    rows_stored  INTEGER NOT NULL DEFAULT 0 CHECK (rows_stored >= 0),
    rows_skipped INTEGER NOT NULL DEFAULT 0 CHECK (rows_skipped >= 0),
    consent_note TEXT    NOT NULL CHECK (length(trim(consent_note)) > 0)
) STRICT;

CREATE TABLE reference_offers (
    offer_id       INTEGER PRIMARY KEY,
    import_id      INTEGER NOT NULL REFERENCES reference_imports (import_id),
    post_id        INTEGER NOT NULL CHECK (post_id > 0),
    post_url       TEXT    NOT NULL UNIQUE CHECK (post_url GLOB 'https://t.me/*'),
    published_at   TEXT    NOT NULL
                           CHECK (published_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T*'),
    title          TEXT    NOT NULL CHECK (length(trim(title)) > 0 AND length(title) <= 200),
    price_uzs      INTEGER NOT NULL CHECK (price_uzs BETWEEN 1000 AND 100000000),
    raw_price_text TEXT,
    -- Reposts of one offer share this id; the first post of the group owns it. The reference is
    -- deferred because the first post of a group points at itself: it is written, then pointed at,
    -- inside one transaction.
    offer_group_id INTEGER NOT NULL REFERENCES reference_offers (offer_id)
                           DEFERRABLE INITIALLY DEFERRED,
    category       TEXT    REFERENCES analysis_categories (code),
    rules_version  TEXT    REFERENCES category_rule_sets (rules_version),
    CHECK ((category IS NULL) = (rules_version IS NULL))
) STRICT;

CREATE INDEX ix_reference_offers_published ON reference_offers (published_at);
CREATE INDEX ix_reference_offers_group ON reference_offers (offer_group_id);

-- Reference data is evidence too: it is not edited in place.
CREATE TRIGGER trg_reference_offers_no_update
BEFORE UPDATE OF post_url, published_at, price_uzs, title ON reference_offers
BEGIN SELECT RAISE(ABORT, 'reference_offers is append-only; re-import instead'); END;

-- One row per distinct offer: reposts collapsed, dated by first publication.
CREATE VIEW v_reference_distinct_offers AS
SELECT o.offer_group_id        AS offer_id,
       MIN(o.published_at)     AS first_published_at,
       MAX(o.published_at)     AS last_seen_at,
       COUNT(*)                AS posts,
       MIN(o.price_uzs)        AS price_uzs,
       MIN(o.title)            AS title,
       MIN(o.category)         AS category,
       MIN(o.rules_version)    AS rules_version
FROM reference_offers o
GROUP BY o.offer_group_id;
