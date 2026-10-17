-- secret_shop migration 001: Secret's own catalogue, fed from Secret's public Telegram channel.
--
-- Secret's prices are needed for the comparison (hypothesis H1). The owner does not use an admin
-- system, but publishes every bouquet with its price on a public Telegram channel (ADR-003).
-- Each post becomes a product; each time a run sees the post, a dated price observation is added.
-- A snapshot job copies current prices into market_intel as source_type 'own_system'.
--
-- Same conventions as market_intel: STRICT tables, UTC ISO-8601 timestamps, append-only evidence.

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    code        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL
) STRICT;

CREATE TABLE source_channels (
    channel_id        INTEGER PRIMARY KEY,
    code              TEXT    NOT NULL UNIQUE,
    kind              TEXT    NOT NULL CHECK (kind IN ('telegram_public')),
    preview_url       TEXT    NOT NULL UNIQUE CHECK (preview_url GLOB 'https://t.me/s/*'),
    is_active         INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    robots_status     TEXT    NOT NULL CHECK (robots_status IN ('allowed', 'partly_allowed', 'disallowed')),
    robots_checked_at TEXT    NOT NULL,
    crawl_delay_s     REAL    NOT NULL DEFAULT 5 CHECK (crawl_delay_s >= 5),
    consent_note      TEXT,
    CHECK (is_active = 0 OR robots_status <> 'disallowed')
) STRICT;

CREATE TABLE collection_runs (
    run_id          INTEGER PRIMARY KEY,
    purpose         TEXT    NOT NULL CHECK (purpose IN ('dev', 'assessed', 'test')),
    triggered_by    TEXT    NOT NULL CHECK (triggered_by IN ('manual', 'scheduled')),
    started_at      TEXT    NOT NULL
                            CHECK (started_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z'),
    finished_at     TEXT,
    status          TEXT    NOT NULL DEFAULT 'running'
                            CHECK (status IN ('running', 'success', 'partial', 'failed')),
    git_commit      TEXT    NOT NULL CHECK (length(git_commit) = 40 OR git_commit = 'unknown'),
    git_dirty       INTEGER NOT NULL CHECK (git_dirty IN (0, 1)),
    collector_version TEXT  NOT NULL,
    since_days      INTEGER NOT NULL CHECK (since_days BETWEEN 1 AND 90),
    pages_requested INTEGER NOT NULL DEFAULT 0 CHECK (pages_requested >= 0),
    pages_ok        INTEGER NOT NULL DEFAULT 0 CHECK (pages_ok BETWEEN 0 AND pages_requested),
    prices_saved    INTEGER NOT NULL DEFAULT 0 CHECK (prices_saved >= 0),
    posts_rejected  INTEGER NOT NULL DEFAULT 0 CHECK (posts_rejected >= 0),
    error_message   TEXT,
    CHECK (finished_at IS NULL OR finished_at >= started_at),
    CHECK ((status = 'running') = (finished_at IS NULL)),
    CHECK (purpose <> 'assessed' OR (git_dirty = 0 AND git_commit <> 'unknown'))
) STRICT;

CREATE TABLE source_fetches (
    fetch_id       INTEGER PRIMARY KEY,
    run_id         INTEGER NOT NULL REFERENCES collection_runs (run_id),
    channel_id     INTEGER NOT NULL REFERENCES source_channels (channel_id),
    url            TEXT    NOT NULL CHECK (url GLOB 'https://*'),
    requested_at   TEXT    NOT NULL,
    attempt        INTEGER NOT NULL DEFAULT 1 CHECK (attempt BETWEEN 1 AND 5),
    http_status    INTEGER CHECK (http_status BETWEEN 100 AND 599),
    elapsed_ms     INTEGER CHECK (elapsed_ms >= 0),
    bytes          INTEGER CHECK (bytes >= 0),
    content_sha256 TEXT    CHECK (content_sha256 IS NULL OR length(content_sha256) = 64),
    parse_ok       INTEGER CHECK (parse_ok IN (0, 1)),
    items_found    INTEGER CHECK (items_found >= 0),
    error          TEXT
) STRICT;

CREATE INDEX ix_source_fetches_run ON source_fetches (run_id);

-- One product per channel post. Captions are stored without contact lines (data minimisation).
CREATE TABLE products (
    product_id        INTEGER PRIMARY KEY,
    channel_id        INTEGER NOT NULL REFERENCES source_channels (channel_id),
    origin            TEXT    NOT NULL DEFAULT 'telegram' CHECK (origin IN ('telegram', 'manual')),
    post_url          TEXT    NOT NULL UNIQUE CHECK (post_url GLOB 'https://t.me/*/[0-9]*'),
    post_id           INTEGER NOT NULL CHECK (post_id > 0),
    published_at      TEXT    NOT NULL,
    title             TEXT    NOT NULL CHECK (length(trim(title)) > 0),
    caption           TEXT    NOT NULL,
    category_id       INTEGER REFERENCES categories (category_id),
    first_seen_run_id INTEGER NOT NULL REFERENCES collection_runs (run_id),
    last_seen_at      TEXT    NOT NULL
) STRICT;

CREATE INDEX ix_products_published ON products (published_at);

-- Comparison attributes (flower type, stem count, packaging...). Several values per attribute are
-- allowed (e.g. roses + callas). 'keyword' = extracted from the caption; 'manual' = annotated by a
-- person looking at the post; missing attributes are simply absent, never imputed.
CREATE TABLE product_attributes (
    product_id   INTEGER NOT NULL REFERENCES products (product_id),
    attribute    TEXT    NOT NULL CHECK (attribute IN ('flower_type', 'stem_count', 'packaging',
                                                       'size', 'colour', 'addon')),
    value        TEXT    NOT NULL CHECK (length(trim(value)) > 0),
    method       TEXT    NOT NULL CHECK (method IN ('keyword', 'manual')),
    annotated_by TEXT    NOT NULL,
    annotated_at TEXT    NOT NULL,
    PRIMARY KEY (product_id, attribute, value)
) STRICT;

-- A dated price observation of one product (append-only).
CREATE TABLE product_price_history (
    price_id            INTEGER PRIMARY KEY,
    product_id          INTEGER NOT NULL REFERENCES products (product_id),
    run_id              INTEGER NOT NULL REFERENCES collection_runs (run_id),
    fetch_id            INTEGER REFERENCES source_fetches (fetch_id),
    observed_at         TEXT    NOT NULL
                                CHECK (observed_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z'),
    price_uzs           INTEGER NOT NULL CHECK (price_uzs BETWEEN 1000 AND 100000000),
    raw_price_text      TEXT    NOT NULL,
    method              TEXT    NOT NULL CHECK (method IN ('telegram_collector', 'manual_form')),
    entered_by          TEXT    NOT NULL,
    UNIQUE (product_id, run_id),
    CHECK ((method = 'telegram_collector') = (fetch_id IS NOT NULL))
) STRICT;

CREATE INDEX ix_price_history_product_time ON product_price_history (product_id, observed_at);

CREATE TABLE rejected_posts (
    reject_id   INTEGER PRIMARY KEY,
    run_id      INTEGER NOT NULL REFERENCES collection_runs (run_id),
    fetch_id    INTEGER REFERENCES source_fetches (fetch_id),
    post_url    TEXT,
    rejected_at TEXT    NOT NULL,
    rule        TEXT    NOT NULL,   -- e.g. 'no_price', 'multiple_prices', 'price_out_of_range'
    detail      TEXT,
    raw_payload TEXT    NOT NULL CHECK (json_valid(raw_payload))
) STRICT;

-- Provenance: a collector price must come from a fetch of the same run.
CREATE TRIGGER trg_price_history_fetch_matches_run
BEFORE INSERT ON product_price_history
WHEN NEW.fetch_id IS NOT NULL
 AND NOT EXISTS (SELECT 1 FROM source_fetches f WHERE f.fetch_id = NEW.fetch_id AND f.run_id = NEW.run_id)
BEGIN
    SELECT RAISE(ABORT, 'provenance: fetch_id must come from the same run as the price');
END;

CREATE TRIGGER trg_price_history_no_update BEFORE UPDATE ON product_price_history
BEGIN SELECT RAISE(ABORT, 'product_price_history is append-only'); END;

CREATE TRIGGER trg_price_history_no_delete BEFORE DELETE ON product_price_history
BEGIN SELECT RAISE(ABORT, 'product_price_history is append-only'); END;

CREATE TRIGGER trg_source_fetches_no_update BEFORE UPDATE ON source_fetches
BEGIN SELECT RAISE(ABORT, 'source_fetches is append-only'); END;

CREATE TRIGGER trg_source_fetches_no_delete BEFORE DELETE ON source_fetches
BEGIN SELECT RAISE(ABORT, 'source_fetches is append-only'); END;

-- Current price of every product = its most recent observation.
CREATE VIEW v_current_prices AS
SELECT p.product_id, p.post_url, p.post_id, p.title, p.published_at, h.price_uzs, h.observed_at, h.run_id,
       r.purpose
FROM products p
JOIN product_price_history h ON h.product_id = p.product_id
JOIN collection_runs r ON r.run_id = h.run_id
WHERE h.price_id = (SELECT h2.price_id FROM product_price_history h2
                    WHERE h2.product_id = p.product_id
                    ORDER BY h2.observed_at DESC, h2.price_id DESC LIMIT 1);
