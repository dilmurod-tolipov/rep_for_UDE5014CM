-- market_intel migration 014: dated delivery terms per shop
--
-- Promised in the approved v2 proposal ("delivery terms per shop (dated)") and required by the
-- approved analysis plan, which says: "Delivery fees and free-delivery thresholds are recorded per
-- shop with a date and reported descriptively, never added to a price."
--
-- WHY A SEPARATE TABLE, AND WHY DATED. A shop's delivery policy is a property of the shop at a
-- moment in time, not of a product, and it changes without warning. Storing it beside the price
-- would invite exactly the mistake the analysis plan forbids - quietly adding a fee to a price and
-- comparing shops on a number neither of them advertises. Keeping it in its own dated table makes
-- the policy reportable ("free over 500,000 UZS as of 21 November") while making it structurally
-- impossible for the comparison, which reads `analysis_products`, to pick it up.
--
-- WHY IT SHIPS EMPTY. These are facts about other businesses. They are entered only from each
-- shop's own public delivery page, with the URL and the date they were read, through
-- `python -m priceintel record-delivery-terms`. Nothing is inferred, and nothing is seeded: an
-- invented delivery fee would be fabricated evidence about a real company. An empty table is the
-- honest state until each page has been read.

CREATE TABLE shop_delivery_terms (
    term_id                     INTEGER PRIMARY KEY,
    shop_id                     INTEGER NOT NULL REFERENCES shops (shop_id),
    -- The date the published page was read, not the date it was written.
    observed_on                 TEXT    NOT NULL
                                        CHECK (observed_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
    source_url                  TEXT    NOT NULL CHECK (source_url GLOB 'https://*'),
    -- NULL means "the page does not say", which is different from zero.
    delivery_fee_uzs            INTEGER CHECK (delivery_fee_uzs IS NULL
                                               OR delivery_fee_uzs BETWEEN 0 AND 1000000),
    free_delivery_threshold_uzs INTEGER CHECK (free_delivery_threshold_uzs IS NULL
                                               OR free_delivery_threshold_uzs BETWEEN 0 AND 100000000),
    same_day                    INTEGER CHECK (same_day IS NULL OR same_day IN (0, 1)),
    zone_note                   TEXT,
    -- The sentence on the page, so the reading can be checked without visiting it again.
    raw_text                    TEXT    NOT NULL CHECK (length(trim(raw_text)) > 0),
    recorded_by                 TEXT    NOT NULL,
    recorded_at                 TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    -- One reading per shop per day; re-reading the same page on the same day replaces nothing.
    UNIQUE (shop_id, observed_on)
) STRICT;

CREATE INDEX ix_delivery_terms_shop ON shop_delivery_terms (shop_id, observed_on);

-- A reading is evidence: it may be added, never edited.
CREATE TRIGGER trg_delivery_terms_no_update BEFORE UPDATE ON shop_delivery_terms
BEGIN SELECT RAISE(ABORT, 'shop_delivery_terms is append-only: record a new dated reading'); END;

-- Mirror domains are never crawled (ADR-001), so they have no terms of their own to record.
CREATE TRIGGER trg_delivery_terms_not_for_mirrors
BEFORE INSERT ON shop_delivery_terms
WHEN (SELECT s.is_mirror FROM shops s WHERE s.shop_id = NEW.shop_id) = 1
BEGIN
    SELECT RAISE(ABORT, 'delivery terms belong to the canonical domain of an operator group, not a mirror');
END;

-- The latest reading per shop, which is what a report quotes.
CREATE VIEW v_shop_delivery_terms_latest AS
SELECT s.code, s.operator_group, t.observed_on, t.delivery_fee_uzs,
       t.free_delivery_threshold_uzs, t.same_day, t.zone_note, t.source_url
FROM shop_delivery_terms t
JOIN shops s ON s.shop_id = t.shop_id
WHERE t.term_id = (SELECT t2.term_id FROM shop_delivery_terms t2
                   WHERE t2.shop_id = t.shop_id
                   ORDER BY t2.observed_on DESC, t2.term_id DESC LIMIT 1);
