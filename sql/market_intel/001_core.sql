-- market_intel migration 001: core collection schema (Checkpoint 1)
--
-- Design rules enforced here, in the database, not only in Python:
--   * STRICT tables: SQLite rejects values of the wrong type.
--   * Every price observation traces to a run, a fetch (HTTP request), a source URL
--     and a UTC timestamp. Observations are append-only.
--   * Re-running collection is idempotent: UNIQUE (listing_id, run_id).
--   * A competitor shop can only be active if its robots.txt check allowed it.
--   * Secret's own prices (source_type 'own_system') can only belong to the own shop.
--
-- Timestamps are UTC ISO-8601 text: YYYY-MM-DDTHH:MM:SSZ.

-- ---------------------------------------------------------------------------
-- shops: one row per website (or Secret's own system), with compliance status
-- ---------------------------------------------------------------------------
CREATE TABLE shops (
    shop_id           INTEGER PRIMARY KEY,
    code              TEXT    NOT NULL UNIQUE
                              CHECK (code GLOB '[a-z]*' AND code NOT GLOB '*[^a-z0-9_]*'),
    name              TEXT    NOT NULL,
    base_url          TEXT    NOT NULL UNIQUE
                              CHECK (base_url GLOB 'https://*' OR base_url GLOB 'internal://*'),
    operator          TEXT    NOT NULL,          -- independence unit (ADR-001)
    is_own_shop       INTEGER NOT NULL DEFAULT 0 CHECK (is_own_shop IN (0, 1)),
    is_active         INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    robots_status     TEXT    NOT NULL DEFAULT 'unchecked'
                              CHECK (robots_status IN ('unchecked', 'allowed', 'partly_allowed',
                                                       'disallowed', 'not_applicable')),
    robots_checked_at TEXT,
    terms_url         TEXT,
    terms_checked_at  TEXT,
    crawl_delay_s     REAL    NOT NULL DEFAULT 5 CHECK (crawl_delay_s >= 5),
    compliance_notes  TEXT,
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    -- Secret's own system is not crawled, so robots.txt does not apply to it.
    CHECK (is_own_shop = 0 OR robots_status = 'not_applicable'),
    -- An active competitor must have passed the compliance check.
    CHECK (is_active = 0 OR is_own_shop = 1
           OR (robots_status IN ('allowed', 'partly_allowed') AND robots_checked_at IS NOT NULL))
) STRICT;

-- At most one shop can be "ours".
CREATE UNIQUE INDEX ux_shops_single_own_shop ON shops (is_own_shop) WHERE is_own_shop = 1;

-- ---------------------------------------------------------------------------
-- scrape_runs: one execution of the collector (scheduled or manual)
-- ---------------------------------------------------------------------------
CREATE TABLE scrape_runs (
    run_id             INTEGER PRIMARY KEY,
    kind               TEXT    NOT NULL CHECK (kind IN ('competitor_scrape', 'own_snapshot')),
    purpose            TEXT    NOT NULL CHECK (purpose IN ('dev', 'assessed', 'test')),
    triggered_by       TEXT    NOT NULL CHECK (triggered_by IN ('manual', 'scheduled')),
    started_at         TEXT    NOT NULL
                               CHECK (started_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z'),
    finished_at        TEXT,
    status             TEXT    NOT NULL DEFAULT 'running'
                               CHECK (status IN ('running', 'success', 'partial', 'failed')),
    git_commit         TEXT    NOT NULL CHECK (length(git_commit) = 40 OR git_commit = 'unknown'),
    git_dirty          INTEGER NOT NULL CHECK (git_dirty IN (0, 1)),
    scraper_version    TEXT    NOT NULL,
    runner_host        TEXT    NOT NULL,
    pages_requested    INTEGER NOT NULL DEFAULT 0 CHECK (pages_requested >= 0),
    pages_ok           INTEGER NOT NULL DEFAULT 0 CHECK (pages_ok BETWEEN 0 AND pages_requested),
    observations_saved INTEGER NOT NULL DEFAULT 0 CHECK (observations_saved >= 0),
    records_rejected   INTEGER NOT NULL DEFAULT 0 CHECK (records_rejected >= 0),
    error_message      TEXT,
    CHECK (finished_at IS NULL OR finished_at >= started_at),
    CHECK ((status = 'running') = (finished_at IS NULL)),
    -- Assessed data must come from committed, unmodified code so it can be reproduced.
    CHECK (purpose <> 'assessed' OR (git_dirty = 0 AND git_commit <> 'unknown'))
) STRICT;

CREATE INDEX ix_scrape_runs_purpose_started ON scrape_runs (purpose, started_at);

-- ---------------------------------------------------------------------------
-- fetch_log: one row per HTTP request attempt (or per robots.txt refusal)
-- ---------------------------------------------------------------------------
CREATE TABLE fetch_log (
    fetch_id        INTEGER PRIMARY KEY,
    run_id          INTEGER NOT NULL REFERENCES scrape_runs (run_id),
    shop_id         INTEGER NOT NULL REFERENCES shops (shop_id),
    url             TEXT    NOT NULL CHECK (url GLOB 'https://*'),
    requested_at    TEXT    NOT NULL
                            CHECK (requested_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z'),
    attempt         INTEGER NOT NULL DEFAULT 1 CHECK (attempt BETWEEN 1 AND 5),
    robots_allowed  INTEGER NOT NULL CHECK (robots_allowed IN (0, 1)),
    http_status     INTEGER CHECK (http_status BETWEEN 100 AND 599),
    elapsed_ms      INTEGER CHECK (elapsed_ms >= 0),
    bytes           INTEGER CHECK (bytes >= 0),
    content_sha256  TEXT    CHECK (content_sha256 IS NULL OR length(content_sha256) = 64),
    parse_ok        INTEGER CHECK (parse_ok IN (0, 1)),
    items_found     INTEGER CHECK (items_found >= 0),
    error           TEXT,
    -- A URL refused by robots.txt is never requested, so it cannot have a response.
    CHECK (robots_allowed = 1 OR (http_status IS NULL AND bytes IS NULL))
) STRICT;

CREATE INDEX ix_fetch_log_run ON fetch_log (run_id);
CREATE INDEX ix_fetch_log_shop_time ON fetch_log (shop_id, requested_at);

-- ---------------------------------------------------------------------------
-- listings: one distinct product page per shop (the unit of analysis)
-- ---------------------------------------------------------------------------
CREATE TABLE listings (
    listing_id        INTEGER PRIMARY KEY,
    shop_id           INTEGER NOT NULL REFERENCES shops (shop_id),
    url               TEXT    NOT NULL
                              CHECK (url GLOB 'https://*' OR url GLOB 'internal://*'),
    external_id       TEXT,                       -- shop's own product id, if shown
    first_seen_run_id INTEGER NOT NULL REFERENCES scrape_runs (run_id),
    first_seen_at     TEXT    NOT NULL,
    last_seen_at      TEXT    NOT NULL,
    last_title        TEXT    NOT NULL CHECK (length(trim(last_title)) > 0),
    UNIQUE (shop_id, url),
    CHECK (last_seen_at >= first_seen_at)
) STRICT;

CREATE INDEX ix_listings_shop_last_seen ON listings (shop_id, last_seen_at);

-- ---------------------------------------------------------------------------
-- price_observations: what one listing cost in one run (append-only)
-- ---------------------------------------------------------------------------
CREATE TABLE price_observations (
    observation_id INTEGER PRIMARY KEY,
    listing_id     INTEGER NOT NULL REFERENCES listings (listing_id),
    run_id         INTEGER NOT NULL REFERENCES scrape_runs (run_id),
    fetch_id       INTEGER REFERENCES fetch_log (fetch_id),
    observed_at    TEXT    NOT NULL
                           CHECK (observed_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z'),
    source_type    TEXT    NOT NULL CHECK (source_type IN ('scrape', 'own_system', 'reference')),
    title          TEXT    NOT NULL CHECK (length(trim(title)) > 0),
    -- Hard sanity bounds; stricter plausibility rules live in the validator.
    price_uzs      INTEGER NOT NULL CHECK (price_uzs BETWEEN 1000 AND 100000000),
    old_price_uzs  INTEGER CHECK (old_price_uzs IS NULL OR old_price_uzs > price_uzs),
    is_from_price  INTEGER NOT NULL DEFAULT 0 CHECK (is_from_price IN (0, 1)),  -- "от 22 000 сум"
    is_on_sale     INTEGER GENERATED ALWAYS AS (old_price_uzs IS NOT NULL) VIRTUAL,
    availability   TEXT    NOT NULL DEFAULT 'unknown'
                           CHECK (availability IN ('in_stock', 'out_of_stock', 'unknown')),
    raw_price_text TEXT,
    UNIQUE (listing_id, run_id),
    -- Scraped rows must point at the HTTP request they came from; own/reference rows have none.
    CHECK ((source_type = 'scrape') = (fetch_id IS NOT NULL))
) STRICT;

CREATE INDEX ix_price_obs_run ON price_observations (run_id);
CREATE INDEX ix_price_obs_listing_time ON price_observations (listing_id, observed_at);

-- ---------------------------------------------------------------------------
-- rejected_records: quarantine for records that failed validation
-- ---------------------------------------------------------------------------
CREATE TABLE rejected_records (
    reject_id   INTEGER PRIMARY KEY,
    run_id      INTEGER NOT NULL REFERENCES scrape_runs (run_id),
    fetch_id    INTEGER REFERENCES fetch_log (fetch_id),
    shop_id     INTEGER NOT NULL REFERENCES shops (shop_id),
    rejected_at TEXT    NOT NULL,
    rule        TEXT    NOT NULL,   -- e.g. 'price_missing', 'price_out_of_range', 'foreign_host'
    detail      TEXT,
    raw_payload TEXT    NOT NULL CHECK (json_valid(raw_payload))
) STRICT;

CREATE INDEX ix_rejected_run ON rejected_records (run_id);

-- ---------------------------------------------------------------------------
-- Integrity triggers
-- ---------------------------------------------------------------------------

-- Provenance: an observation's fetch must belong to the same run and the same shop.
CREATE TRIGGER trg_price_obs_fetch_matches_run
BEFORE INSERT ON price_observations
WHEN NEW.fetch_id IS NOT NULL
 AND NOT EXISTS (
       SELECT 1
       FROM fetch_log f
       JOIN listings l ON l.listing_id = NEW.listing_id
       WHERE f.fetch_id = NEW.fetch_id
         AND f.run_id   = NEW.run_id
         AND f.shop_id  = l.shop_id)
BEGIN
    SELECT RAISE(ABORT, 'provenance: fetch_id must come from the same run and shop as the observation');
END;

-- Own-shop separation: own_system rows only for the own shop; scraped rows never for it.
CREATE TRIGGER trg_price_obs_source_matches_shop
BEFORE INSERT ON price_observations
WHEN (SELECT s.is_own_shop FROM listings l JOIN shops s ON s.shop_id = l.shop_id
      WHERE l.listing_id = NEW.listing_id) <> (NEW.source_type = 'own_system')
 AND NEW.source_type <> 'reference'
BEGIN
    SELECT RAISE(ABORT, 'separation: own_system observations must belong to the own shop, and only to it');
END;

-- Append-only evidence tables.
CREATE TRIGGER trg_price_obs_no_update BEFORE UPDATE ON price_observations
BEGIN SELECT RAISE(ABORT, 'price_observations is append-only'); END;

CREATE TRIGGER trg_price_obs_no_delete BEFORE DELETE ON price_observations
BEGIN SELECT RAISE(ABORT, 'price_observations is append-only'); END;

CREATE TRIGGER trg_fetch_log_no_update BEFORE UPDATE ON fetch_log
BEGIN SELECT RAISE(ABORT, 'fetch_log is append-only'); END;

CREATE TRIGGER trg_fetch_log_no_delete BEFORE DELETE ON fetch_log
BEGIN SELECT RAISE(ABORT, 'fetch_log is append-only'); END;

-- ---------------------------------------------------------------------------
-- Retrieval view: the most recent observation of every listing
-- ---------------------------------------------------------------------------
CREATE VIEW v_latest_prices AS
SELECT s.code        AS shop,
       s.operator,
       l.listing_id,
       o.title,
       o.price_uzs,
       o.old_price_uzs,
       o.is_from_price,
       o.availability,
       o.source_type,
       o.observed_at,
       o.run_id,
       r.purpose,
       l.url
FROM price_observations o
JOIN listings    l ON l.listing_id = o.listing_id
JOIN shops       s ON s.shop_id    = l.shop_id
JOIN scrape_runs r ON r.run_id     = o.run_id
WHERE o.observation_id = (SELECT o2.observation_id
                          FROM price_observations o2
                          WHERE o2.listing_id = o.listing_id
                          ORDER BY o2.observed_at DESC, o2.observation_id DESC
                          LIMIT 1);
