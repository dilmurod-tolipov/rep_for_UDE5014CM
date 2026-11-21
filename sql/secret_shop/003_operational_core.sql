-- secret_shop migration 003: Secret's operational core (clients, orders, payments, staff)
--
-- Promised in the approved v2 proposal and announced in migration 002 ("the operational schema ...
-- is rewritten in a later migration"). This is that migration.
--
-- WHY IT EXISTS AT ALL. The owner does not use an ordering system: Secret takes orders by phone and
-- Telegram and keeps no digital record. So every row in these tables is SYNTHETIC - a fixture that
-- exercises the schema, the constraints and the storefront demo. The honest design question is
-- therefore not "how do we model orders" but "how do we model orders so that fabricated rows can
-- never be mistaken for evidence". The answer is the `is_synthetic` flag, which is:
--   * NOT NULL on every table here, so a row cannot be inserted without declaring what it is;
--   * propagated by triggers, so an order, its address, its lines and its payments must agree;
--   * blocked from the price analysis - a real order may not reference a synthetic product, and
--     `priceintel/integrity.py` fails the cross-database check if a synthetic row is ever reachable
--     from the analysis side.
--
-- PRIVACY. This schema holds no real personal data, and is built so that it could not quietly start
-- holding it: a non-synthetic client requires `consent_recorded_at`, and the only contact column is
-- the last four digits of a phone number (enough for staff to recognise a returning customer,
-- useless for contacting a stranger). Data minimisation by schema, not by policy.
--
-- Same conventions as the rest of the project: STRICT tables, UTC ISO-8601 text timestamps,
-- money as integer UZS, every rule in the database rather than in Python.

-- ---------------------------------------------------------------------------
-- Secret's own catalogue, rebuilt for a shop rather than for a Telegram channel
-- ---------------------------------------------------------------------------
-- Migration 002 emptied these tables when Telegram collection was withdrawn and said the
-- operational schema would be rewritten here. This is that rewrite. The tables are dropped and
-- recreated rather than altered, because the old shape REQUIRED a t.me post URL on every product -
-- a hand-entered product would have had to carry an invented Telegram link. They hold no rows
-- (002 deleted them), so nothing is lost; the children are dropped before the parent so no foreign
-- key is ever left pointing at a missing table.
DROP VIEW v_current_prices;
DROP TRIGGER trg_price_history_fetch_matches_run;
DROP TRIGGER trg_price_history_no_update;
DROP TRIGGER trg_price_history_no_delete;
DROP TABLE product_price_history;
DROP TABLE product_attributes;
DROP INDEX ix_products_published;
DROP TABLE products;

CREATE TABLE products (
    product_id        INTEGER PRIMARY KEY,
    origin            TEXT    NOT NULL DEFAULT 'manual' CHECK (origin IN ('telegram', 'manual')),
    title             TEXT    NOT NULL CHECK (length(trim(title)) > 0),
    caption           TEXT    NOT NULL DEFAULT '',
    category_id       INTEGER REFERENCES categories (category_id),
    is_active         INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    -- Provenance columns, used only by rows that were collected from somewhere.
    channel_id        INTEGER REFERENCES source_channels (channel_id),
    post_url          TEXT    UNIQUE CHECK (post_url IS NULL OR post_url GLOB 'https://t.me/*/[0-9]*'),
    post_id           INTEGER CHECK (post_id IS NULL OR post_id > 0),
    published_at      TEXT,
    first_seen_run_id INTEGER REFERENCES collection_runs (run_id),
    last_seen_at      TEXT,
    is_synthetic      INTEGER NOT NULL CHECK (is_synthetic IN (0, 1)),
    -- A collected product must be able to prove where it came from ...
    CHECK (origin <> 'telegram' OR (channel_id IS NOT NULL AND post_url IS NOT NULL
                                    AND post_id IS NOT NULL AND published_at IS NOT NULL
                                    AND first_seen_run_id IS NOT NULL AND last_seen_at IS NOT NULL)),
    -- ... and a hand-entered one may not dress itself up as collected.
    CHECK (origin <> 'manual' OR (channel_id IS NULL AND post_url IS NULL AND post_id IS NULL
                                  AND first_seen_run_id IS NULL)),
    -- Nothing invented may claim to have been collected.
    CHECK (is_synthetic = 0 OR origin = 'manual')
) STRICT;

CREATE INDEX ix_products_category ON products (category_id);

-- Comparison attributes (flower type, stem count, packaging). Missing values stay absent.
CREATE TABLE product_attributes (
    product_id   INTEGER NOT NULL REFERENCES products (product_id) ON DELETE CASCADE,
    attribute    TEXT    NOT NULL CHECK (attribute IN ('flower_type', 'stem_count', 'packaging',
                                                       'size', 'colour', 'addon')),
    value        TEXT    NOT NULL CHECK (length(trim(value)) > 0),
    method       TEXT    NOT NULL CHECK (method IN ('keyword', 'manual')),
    annotated_by TEXT    NOT NULL,
    annotated_at TEXT    NOT NULL,
    PRIMARY KEY (product_id, attribute, value)
) STRICT;

-- The catalogue price over time. There is deliberately NO price column on `products`: the current
-- price is the newest row here, so the two can never disagree. Append-only, like every other
-- evidence table in the project.
CREATE TABLE product_price_history (
    price_id       INTEGER PRIMARY KEY,
    product_id     INTEGER NOT NULL REFERENCES products (product_id) ON DELETE CASCADE,
    effective_from TEXT    NOT NULL
                           CHECK (effective_from GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z'),
    price_uzs      INTEGER NOT NULL CHECK (price_uzs BETWEEN 1000 AND 100000000),
    changed_by     INTEGER REFERENCES admin_users (admin_user_id),
    reason         TEXT,
    UNIQUE (product_id, effective_from)
) STRICT;

CREATE INDEX ix_price_history_product_time ON product_price_history (product_id, effective_from);

CREATE TRIGGER trg_price_history_no_update BEFORE UPDATE ON product_price_history
BEGIN SELECT RAISE(ABORT, 'product_price_history is append-only: add a new dated price'); END;

-- The price in force for every product now.
CREATE VIEW v_current_prices AS
SELECT p.product_id, p.title, p.origin, p.is_synthetic, c.code AS category,
       h.price_uzs, h.effective_from
FROM products p
JOIN product_price_history h ON h.product_id = p.product_id
LEFT JOIN categories c ON c.category_id = p.category_id
WHERE h.price_id = (SELECT h2.price_id FROM product_price_history h2
                    WHERE h2.product_id = p.product_id
                    ORDER BY h2.effective_from DESC, h2.price_id DESC LIMIT 1);

-- ---------------------------------------------------------------------------
-- Staff who may act in the system
-- ---------------------------------------------------------------------------
CREATE TABLE admin_users (
    admin_user_id INTEGER PRIMARY KEY,
    username      TEXT    NOT NULL UNIQUE
                          CHECK (username GLOB '[a-z]*' AND username NOT GLOB '*[^a-z0-9_.]*'),
    display_name  TEXT    NOT NULL CHECK (length(trim(display_name)) > 0),
    role          TEXT    NOT NULL CHECK (role IN ('owner', 'manager', 'florist', 'courier')),
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    -- No password column: this project never authenticates anyone. If the owner ever adopts the
    -- system, credentials belong in a dedicated store, not beside the catalogue.
    is_synthetic  INTEGER NOT NULL CHECK (is_synthetic IN (0, 1))
) STRICT;

-- Exactly one owner account may be active at a time.
CREATE UNIQUE INDEX ux_admin_users_single_owner ON admin_users (role)
    WHERE role = 'owner' AND is_active = 1;

-- ---------------------------------------------------------------------------
-- Customers, and where they want flowers delivered
-- ---------------------------------------------------------------------------
CREATE TABLE clients (
    client_id           INTEGER PRIMARY KEY,
    display_name        TEXT    NOT NULL CHECK (length(trim(display_name)) > 0),
    phone_last4         TEXT    CHECK (phone_last4 IS NULL OR phone_last4 GLOB '[0-9][0-9][0-9][0-9]'),
    preferred_channel   TEXT    NOT NULL DEFAULT 'phone'
                                CHECK (preferred_channel IN ('phone', 'telegram', 'walk_in')),
    first_order_at      TEXT,
    consent_recorded_at TEXT,
    note                TEXT,
    created_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    is_synthetic        INTEGER NOT NULL CHECK (is_synthetic IN (0, 1)),
    -- A real customer may only be stored once their consent has been recorded.
    CHECK (is_synthetic = 1 OR consent_recorded_at IS NOT NULL)
) STRICT;

CREATE TABLE addresses (
    address_id   INTEGER PRIMARY KEY,
    client_id    INTEGER NOT NULL REFERENCES clients (client_id),
    district     TEXT    NOT NULL CHECK (length(trim(district)) > 0),
    line1        TEXT    NOT NULL CHECK (length(trim(line1)) > 0),
    landmark     TEXT,
    is_default   INTEGER NOT NULL DEFAULT 0 CHECK (is_default IN (0, 1)),
    is_synthetic INTEGER NOT NULL CHECK (is_synthetic IN (0, 1))
) STRICT;

CREATE INDEX ix_addresses_client ON addresses (client_id);

-- One default address per client at most.
CREATE UNIQUE INDEX ux_addresses_one_default ON addresses (client_id) WHERE is_default = 1;

-- ---------------------------------------------------------------------------
-- Orders, their lines, and money received
-- ---------------------------------------------------------------------------
CREATE TABLE orders (
    order_id         INTEGER PRIMARY KEY,
    client_id        INTEGER NOT NULL REFERENCES clients (client_id),
    address_id       INTEGER REFERENCES addresses (address_id),   -- NULL = collected in the shop
    created_by       INTEGER NOT NULL REFERENCES admin_users (admin_user_id),
    channel          TEXT    NOT NULL CHECK (channel IN ('phone', 'telegram', 'walk_in', 'web')),
    placed_at        TEXT    NOT NULL
                             CHECK (placed_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z'),
    fulfil_at        TEXT,
    status           TEXT    NOT NULL DEFAULT 'new'
                             CHECK (status IN ('new', 'confirmed', 'in_delivery', 'completed',
                                               'cancelled')),
    currency         TEXT    NOT NULL DEFAULT 'UZS' CHECK (currency = 'UZS'),
    items_total_uzs  INTEGER NOT NULL DEFAULT 0 CHECK (items_total_uzs >= 0),
    delivery_fee_uzs INTEGER NOT NULL DEFAULT 0 CHECK (delivery_fee_uzs >= 0),
    -- Derived, so the total can never disagree with its parts.
    total_uzs        INTEGER GENERATED ALWAYS AS (items_total_uzs + delivery_fee_uzs) STORED,
    cancel_reason    TEXT,
    is_synthetic     INTEGER NOT NULL CHECK (is_synthetic IN (0, 1)),
    CHECK (fulfil_at IS NULL OR fulfil_at >= placed_at),
    -- A delivery fee needs somewhere to deliver to.
    CHECK (delivery_fee_uzs = 0 OR address_id IS NOT NULL),
    -- A cancelled order says why; anything else does not pretend to have been cancelled.
    CHECK ((status = 'cancelled') = (cancel_reason IS NOT NULL))
) STRICT;

CREATE INDEX ix_orders_placed ON orders (placed_at);
CREATE INDEX ix_orders_client ON orders (client_id, placed_at);

CREATE TABLE order_items (
    order_id       INTEGER NOT NULL REFERENCES orders (order_id) ON DELETE CASCADE,
    line_no        INTEGER NOT NULL CHECK (line_no BETWEEN 1 AND 50),
    product_id     INTEGER NOT NULL REFERENCES products (product_id),
    quantity       INTEGER NOT NULL CHECK (quantity BETWEEN 1 AND 100),
    -- The price charged on the day, copied onto the line: the catalogue price may change later and
    -- an order must still say what the customer actually paid.
    unit_price_uzs INTEGER NOT NULL CHECK (unit_price_uzs BETWEEN 1000 AND 100000000),
    line_total_uzs INTEGER GENERATED ALWAYS AS (quantity * unit_price_uzs) STORED,
    PRIMARY KEY (order_id, line_no)
) STRICT;

CREATE INDEX ix_order_items_product ON order_items (product_id);

CREATE TABLE payments (
    payment_id   INTEGER PRIMARY KEY,
    order_id     INTEGER NOT NULL REFERENCES orders (order_id),
    paid_at      TEXT    NOT NULL
                         CHECK (paid_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z'),
    method       TEXT    NOT NULL CHECK (method IN ('cash', 'card', 'transfer', 'click', 'payme')),
    amount_uzs   INTEGER NOT NULL CHECK (amount_uzs > 0),
    status       TEXT    NOT NULL CHECK (status IN ('pending', 'captured', 'refunded', 'failed')),
    reference    TEXT,
    is_synthetic INTEGER NOT NULL CHECK (is_synthetic IN (0, 1))
) STRICT;

CREATE INDEX ix_payments_order ON payments (order_id);

-- ---------------------------------------------------------------------------
-- The rules that keep synthetic and real data apart
-- ---------------------------------------------------------------------------
-- An address belongs to its client's world.
CREATE TRIGGER trg_addresses_synthetic_matches_client
BEFORE INSERT ON addresses
WHEN NEW.is_synthetic <> (SELECT c.is_synthetic FROM clients c WHERE c.client_id = NEW.client_id)
BEGIN
    SELECT RAISE(ABORT, 'synthetic flag: an address must match its client');
END;

-- An order belongs to its client's world, and is raised by a matching account.
CREATE TRIGGER trg_orders_synthetic_matches_parents
BEFORE INSERT ON orders
WHEN NEW.is_synthetic <> (SELECT c.is_synthetic FROM clients c WHERE c.client_id = NEW.client_id)
  OR NEW.is_synthetic <> (SELECT u.is_synthetic FROM admin_users u
                          WHERE u.admin_user_id = NEW.created_by)
  OR (NEW.address_id IS NOT NULL
      AND NEW.is_synthetic <> (SELECT a.is_synthetic FROM addresses a
                               WHERE a.address_id = NEW.address_id))
BEGIN
    SELECT RAISE(ABORT, 'synthetic flag: an order must match its client, its author and its address');
END;

-- The rule that matters most: a REAL order may not be built from invented products.
CREATE TRIGGER trg_order_items_real_order_needs_real_product
BEFORE INSERT ON order_items
WHEN (SELECT o.is_synthetic FROM orders o WHERE o.order_id = NEW.order_id) = 0
 AND (SELECT p.is_synthetic FROM products p WHERE p.product_id = NEW.product_id) = 1
BEGIN
    SELECT RAISE(ABORT, 'a real order cannot contain a synthetic product');
END;

CREATE TRIGGER trg_payments_synthetic_matches_order
BEFORE INSERT ON payments
WHEN NEW.is_synthetic <> (SELECT o.is_synthetic FROM orders o WHERE o.order_id = NEW.order_id)
BEGIN
    SELECT RAISE(ABORT, 'synthetic flag: a payment must match its order');
END;

-- Money received may not exceed what was ordered.
CREATE TRIGGER trg_payments_not_above_order_total
BEFORE INSERT ON payments
WHEN NEW.status = 'captured'
 AND NEW.amount_uzs + COALESCE((SELECT SUM(p.amount_uzs) FROM payments p
                                WHERE p.order_id = NEW.order_id AND p.status = 'captured'), 0)
     > (SELECT o.total_uzs FROM orders o WHERE o.order_id = NEW.order_id)
BEGIN
    SELECT RAISE(ABORT, 'captured payments would exceed the order total');
END;

-- ---------------------------------------------------------------------------
-- The order total is maintained from its lines, never typed in
-- ---------------------------------------------------------------------------
CREATE TRIGGER trg_order_items_total_after_insert AFTER INSERT ON order_items
BEGIN
    UPDATE orders SET items_total_uzs = COALESCE(
        (SELECT SUM(i.line_total_uzs) FROM order_items i WHERE i.order_id = NEW.order_id), 0)
    WHERE order_id = NEW.order_id;
END;

CREATE TRIGGER trg_order_items_total_after_update AFTER UPDATE ON order_items
BEGIN
    UPDATE orders SET items_total_uzs = COALESCE(
        (SELECT SUM(i.line_total_uzs) FROM order_items i WHERE i.order_id = NEW.order_id), 0)
    WHERE order_id = NEW.order_id;
END;

CREATE TRIGGER trg_order_items_total_after_delete AFTER DELETE ON order_items
BEGIN
    UPDATE orders SET items_total_uzs = COALESCE(
        (SELECT SUM(i.line_total_uzs) FROM order_items i WHERE i.order_id = OLD.order_id), 0)
    WHERE order_id = OLD.order_id;
END;

-- ---------------------------------------------------------------------------
-- Views the storefront demo and the dashboard read
-- ---------------------------------------------------------------------------
-- One row per order: what was ordered, what has been captured, what is still owed.
CREATE VIEW v_order_summary AS
SELECT o.order_id, o.placed_at, o.status, o.channel, o.is_synthetic,
       c.display_name AS client_name,
       a.district,
       (SELECT COUNT(*) FROM order_items i WHERE i.order_id = o.order_id)        AS lines,
       (SELECT COALESCE(SUM(i.quantity), 0) FROM order_items i
        WHERE i.order_id = o.order_id)                                            AS units,
       o.items_total_uzs, o.delivery_fee_uzs, o.total_uzs,
       COALESCE((SELECT SUM(p.amount_uzs) FROM payments p
                 WHERE p.order_id = o.order_id AND p.status = 'captured'), 0)     AS captured_uzs,
       o.total_uzs - COALESCE((SELECT SUM(p.amount_uzs) FROM payments p
                               WHERE p.order_id = o.order_id AND p.status = 'captured'), 0)
                                                                                  AS balance_uzs
FROM orders o
JOIN clients c ON c.client_id = o.client_id
LEFT JOIN addresses a ON a.address_id = o.address_id;

-- Secret's own realised prices per category and day: the operational counterpart of the market
-- data. It is NOT an input to the price comparison - that uses market_intel.reference_offers, which
-- holds prices the owner actually published (ADR-007).
CREATE VIEW v_sales_by_category AS
SELECT substr(o.placed_at, 1, 10) AS day,
       COALESCE(cat.code, 'uncategorised') AS category,
       o.is_synthetic,
       COUNT(DISTINCT o.order_id) AS orders,
       SUM(i.quantity)            AS units,
       SUM(i.line_total_uzs)      AS revenue_uzs
FROM orders o
JOIN order_items i ON i.order_id = o.order_id
JOIN products p ON p.product_id = i.product_id
LEFT JOIN categories cat ON cat.category_id = p.category_id
WHERE o.status <> 'cancelled'
GROUP BY day, category, o.is_synthetic;
