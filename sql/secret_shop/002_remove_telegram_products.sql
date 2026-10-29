-- secret_shop migration 002: remove the products imported from the Telegram channel (ADR-007)
--
-- secret_shop 001 modelled Secret's catalogue as one product per channel post, fed by the collector
-- that read the channel's public web preview. That collector is withdrawn, so its records go too.
-- Secret's offers now live in market_intel.reference_offers, imported from the owner's own export.
--
-- The channel-shaped tables are emptied here, not dropped: the operational schema (categories,
-- products, prices, synthetic orders for the storefront demo) is rewritten in a later migration, and
-- dropping tables other code still reads would break the clean-checkout run in the meantime.

-- The evidence tables are append-only; the guards are dropped for this migration and recreated
-- below, exactly as in 001, so the append-only rule holds again as soon as the migration ends.
DROP TRIGGER trg_price_history_no_update;
DROP TRIGGER trg_price_history_no_delete;
DROP TRIGGER trg_source_fetches_no_update;
DROP TRIGGER trg_source_fetches_no_delete;

DELETE FROM product_price_history;
DELETE FROM product_attributes;
DELETE FROM products;
DELETE FROM rejected_posts;
DELETE FROM source_fetches;
DELETE FROM collection_runs;
UPDATE source_channels SET is_active = 0,
       consent_note = 'Collection withdrawn 2026-10-29: Telegram Content Licensing and AI Scraping '
                      || 'Terms. Secret offers come from the owner export (market_intel.reference_offers).';

CREATE TRIGGER trg_price_history_no_update BEFORE UPDATE ON product_price_history
BEGIN SELECT RAISE(ABORT, 'product_price_history is append-only'); END;

CREATE TRIGGER trg_price_history_no_delete BEFORE DELETE ON product_price_history
BEGIN SELECT RAISE(ABORT, 'product_price_history is append-only'); END;

CREATE TRIGGER trg_source_fetches_no_update BEFORE UPDATE ON source_fetches
BEGIN SELECT RAISE(ABORT, 'source_fetches is append-only'); END;

CREATE TRIGGER trg_source_fetches_no_delete BEFORE DELETE ON source_fetches
BEGIN SELECT RAISE(ABORT, 'source_fetches is append-only'); END;
