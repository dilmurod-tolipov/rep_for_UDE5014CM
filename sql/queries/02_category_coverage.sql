-- Q2. "Which categories do I have enough evidence to talk about at all?"
--     Asked by: the owner, before trusting any comparison, and by me when deciding what to display.
--
-- One row per category and competitor group: distinct products, distinct Secret offers, and whether
-- the pair clears the minimum of :min_items on both sides. Counting is over listings and offer
-- groups, never over observations or posts, so repeated snapshots and reposts cannot inflate it.
--
-- Parameters: :rules_version, :purpose, :min_items

WITH competitor AS (
    SELECT c.category, s.operator_group, COUNT(DISTINCT l.listing_id) AS n_products
    FROM listing_categories c
    JOIN listings l ON l.listing_id = c.listing_id
    JOIN shops    s ON s.shop_id    = l.shop_id
    WHERE c.rules_version = :rules_version
      AND s.is_own_shop = 0
      AND EXISTS (SELECT 1 FROM price_observations o
                  JOIN scrape_runs r ON r.run_id = o.run_id
                  WHERE o.listing_id = l.listing_id AND r.purpose = :purpose)
    GROUP BY c.category, s.operator_group
),
secret AS (
    SELECT category, COUNT(*) AS n_offers
    FROM v_reference_distinct_offers
    GROUP BY category
)
SELECT c.category,
       c.operator_group,
       c.n_products,
       COALESCE(s.n_offers, 0) AS secret_offers,
       CASE WHEN c.n_products >= :min_items AND COALESCE(s.n_offers, 0) >= :min_items
            THEN 'comparison can be displayed'
            WHEN c.n_products <  :min_items AND COALESCE(s.n_offers, 0) <  :min_items
            THEN 'too few on both sides'
            WHEN c.n_products <  :min_items
            THEN 'too few competitor products'
            ELSE 'too few Secret offers' END AS verdict
FROM competitor c
LEFT JOIN secret s ON s.category = c.category
ORDER BY c.category, c.operator_group;
