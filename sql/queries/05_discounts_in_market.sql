-- Q5. "Who is discounting right now, in which categories, and how deeply?"
--     Asked by: the owner, deciding whether a quiet week is a market-wide promotion period.
--
-- Uses only the latest observation of each listing, so a product counts once however often it was
-- seen. A listing is on sale when the shop shows an old price above the current one; the depth is
-- 100 * (1 - current / old). Delivery terms and conditional promotions are deliberately not mixed
-- into this: they are flags recorded per shop, not part of a price.
--
-- Parameters: :rules_version, :purpose

WITH latest AS (
    SELECT l.listing_id, s.operator_group, c.category, o.price_uzs, o.old_price_uzs,
           ROW_NUMBER() OVER (PARTITION BY l.listing_id
                              ORDER BY o.observed_at DESC, o.observation_id DESC) AS recency
    FROM price_observations o
    JOIN listings    l ON l.listing_id = o.listing_id
    JOIN shops       s ON s.shop_id    = l.shop_id
    JOIN scrape_runs r ON r.run_id     = o.run_id
    LEFT JOIN listing_categories c ON c.listing_id = l.listing_id
                                  AND c.rules_version = :rules_version
    WHERE o.source_type = 'scrape' AND r.purpose = :purpose
)
SELECT operator_group,
       COALESCE(category, 'unclassified')                         AS category,
       COUNT(*)                                                   AS products,
       SUM(CASE WHEN old_price_uzs IS NOT NULL THEN 1 ELSE 0 END) AS on_sale,
       ROUND(100.0 * SUM(CASE WHEN old_price_uzs IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
                                                                  AS on_sale_pct,
       ROUND(AVG(CASE WHEN old_price_uzs IS NOT NULL
                      THEN 100.0 * (1 - price_uzs * 1.0 / old_price_uzs) END), 1)
                                                                  AS mean_discount_pct
FROM latest
WHERE recency = 1
GROUP BY operator_group, category
ORDER BY on_sale_pct DESC, operator_group;
