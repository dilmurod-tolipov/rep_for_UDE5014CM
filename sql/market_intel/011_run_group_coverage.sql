-- market_intel migration 011: how many operator groups a run actually collected
--
-- Found on 2026-11-13, four days into the approved window: in five of the first seven assessed runs
-- loveflowers.uz (and once kamilas.uz) contributed nothing, because their robots.txt did not answer
-- within the timeout. The collector then refuses to crawl that shop, which is the right thing to do -
-- but the run still reported `success`, because the skipped shop's pages were never *requested* and
-- the page success rate stayed at 100%.
--
-- So the run status was measuring the wrong thing. These two columns record what the run set out to
-- collect and what it reached, and `collect()` now marks a run `partial` when a group is missing. The
-- approved success rate is computed from runs that reached every active group.
ALTER TABLE scrape_runs ADD COLUMN shops_expected  INTEGER NOT NULL DEFAULT 0
    CHECK (shops_expected >= 0);
ALTER TABLE scrape_runs ADD COLUMN shops_collected INTEGER NOT NULL DEFAULT 0
    CHECK (shops_collected >= 0);

-- Per-run coverage, including the runs collected before this migration: for those the counts are
-- recomputed from the observations, so the history stays honest rather than starting at zero.
UPDATE scrape_runs
   SET shops_collected = (SELECT COUNT(DISTINCT l.shop_id)
                          FROM price_observations o JOIN listings l ON l.listing_id = o.listing_id
                          WHERE o.run_id = scrape_runs.run_id),
       shops_expected  = (SELECT COUNT(*) FROM shops
                          WHERE is_active = 1 AND is_own_shop = 0)
 WHERE kind = 'competitor_scrape';

-- A run that missed an operator group is not a successful run, whatever its page rate.
UPDATE scrape_runs
   SET status = 'partial'
 WHERE kind = 'competitor_scrape'
   AND status = 'success'
   AND shops_collected < shops_expected;

CREATE VIEW v_run_coverage AS
SELECT r.run_id, r.purpose, r.started_at, r.status,
       r.shops_collected, r.shops_expected,
       r.pages_ok, r.pages_requested,
       (SELECT GROUP_CONCAT(s.operator_group, ', ')
        FROM shops s
        WHERE s.is_active = 1 AND s.is_own_shop = 0
          AND NOT EXISTS (SELECT 1 FROM price_observations o
                          JOIN listings l ON l.listing_id = o.listing_id
                          WHERE o.run_id = r.run_id AND l.shop_id = s.shop_id)) AS groups_missing
FROM scrape_runs r
WHERE r.kind = 'competitor_scrape';
