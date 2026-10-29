-- market_intel migration 006: remove the Telegram-derived rows (ADR-007)
--
-- Until 2026-10-29 a scheduled job read Secret's prices from the channel's public web preview and
-- copied them into price_observations as source_type 'own_system'. That route is withdrawn
-- (Telegram's Content Licensing and AI Scraping Terms; Module Leader 26/10/2026, point 1), so the
-- records it produced are deleted here rather than left in the database.
--
-- price_observations is append-only by design, so the two guard triggers are dropped for the length
-- of this migration and recreated identically at the end. Doing it as a numbered migration keeps it
-- auditable and reproducible: anyone replaying the migrations reaches the same state, and the reason
-- is in this file rather than in a shell command someone ran once.
--
-- All deleted rows were purpose = 'dev'. No assessed data existed, and none is affected.

DROP TRIGGER trg_price_obs_no_update;
DROP TRIGGER trg_price_obs_no_delete;

DELETE FROM price_observations
 WHERE source_type IN ('own_system', 'reference')
    OR listing_id IN (SELECT l.listing_id FROM listings l
                      JOIN shops s ON s.shop_id = l.shop_id WHERE s.is_own_shop = 1);

DELETE FROM listing_categories
 WHERE listing_id IN (SELECT l.listing_id FROM listings l
                      JOIN shops s ON s.shop_id = l.shop_id WHERE s.is_own_shop = 1);

DELETE FROM listings
 WHERE shop_id IN (SELECT shop_id FROM shops WHERE is_own_shop = 1);

DELETE FROM scrape_runs
 WHERE kind = 'own_snapshot'
   AND run_id NOT IN (SELECT run_id FROM price_observations)
   AND run_id NOT IN (SELECT run_id FROM fetch_log);

CREATE TRIGGER trg_price_obs_no_update BEFORE UPDATE ON price_observations
BEGIN SELECT RAISE(ABORT, 'price_observations is append-only'); END;

CREATE TRIGGER trg_price_obs_no_delete BEFORE DELETE ON price_observations
BEGIN SELECT RAISE(ABORT, 'price_observations is append-only'); END;
