-- Q1. "In each category, how does my advertised price level compare with each competitor group?"
--     Asked by: the owner of Secret. The headline question of the whole project.
--
-- Read it as: for one category and one competitor group, the percentage is
--     100 * (Secret median regular price / that group's median regular price - 1),
-- positive meaning Secret advertises higher. A row counts as displayable only when there are at
-- least :min_items distinct Secret offers AND at least :min_items distinct products in that group
-- (docs/analysis_plan.md); otherwise it reads insufficient_evidence and the counts explain why.
--
-- SQLite has no median(), so every median here uses the same pattern: number the rows in order with
-- ROW_NUMBER(), count them with COUNT(*) OVER (), then average the middle one or two rows.
--
-- Parameters: :rules_version, :purpose (dev or assessed), :min_items (10 in the plan)

WITH
-- One row per observation, with the regular price: when a sale is shown the old price is the
-- regular one.
observation AS (
    SELECT l.listing_id,
           s.operator_group,
           COALESCE(o.old_price_uzs, o.price_uzs) AS regular_price_uzs
    FROM price_observations o
    JOIN listings    l ON l.listing_id = o.listing_id
    JOIN shops       s ON s.shop_id    = l.shop_id
    JOIN scrape_runs r ON r.run_id     = o.run_id
    WHERE o.source_type = 'scrape'
      AND o.is_from_price = 0          -- "from X" is not the price of one specific bouquet
      AND s.is_own_shop = 0
      AND r.purpose = :purpose
),
observation_ranked AS (
    SELECT listing_id, operator_group, regular_price_uzs,
           ROW_NUMBER() OVER (PARTITION BY listing_id ORDER BY regular_price_uzs) AS rn,
           COUNT(*)     OVER (PARTITION BY listing_id)                            AS n
    FROM observation
),
product AS (                            -- repeated observations collapsed to one price per product
    SELECT r.listing_id, r.operator_group, c.category,
           AVG(r.regular_price_uzs) AS price_uzs
    FROM observation_ranked r
    JOIN listing_categories c ON c.listing_id = r.listing_id
                             AND c.rules_version = :rules_version
    WHERE r.rn IN ((r.n + 1) / 2, (r.n + 2) / 2)
    GROUP BY r.listing_id, r.operator_group, c.category
),
product_ranked AS (
    SELECT category, operator_group, price_uzs,
           ROW_NUMBER() OVER (PARTITION BY category, operator_group ORDER BY price_uzs) AS rn,
           COUNT(*)     OVER (PARTITION BY category, operator_group)                    AS n
    FROM product
),
competitor AS (
    SELECT category, operator_group,
           CAST(AVG(price_uzs) AS INTEGER) AS median_price_uzs,
           MAX(n)                          AS n_products
    FROM product_ranked
    WHERE rn IN ((n + 1) / 2, (n + 2) / 2)
    GROUP BY category, operator_group
),
-- Secret's side: one row per distinct offer, reposts already collapsed by the view.
secret_ranked AS (
    SELECT category, price_uzs,
           ROW_NUMBER() OVER (PARTITION BY category ORDER BY price_uzs) AS rn,
           COUNT(*)     OVER (PARTITION BY category)                    AS n
    FROM v_reference_distinct_offers
    WHERE category IS NOT NULL
),
secret AS (
    SELECT category,
           CAST(AVG(price_uzs) AS INTEGER) AS median_price_uzs,
           MAX(n)                          AS n_offers
    FROM secret_ranked
    WHERE rn IN ((n + 1) / 2, (n + 2) / 2)
    GROUP BY category
)
SELECT c.category,
       c.operator_group,
       s.n_offers                              AS secret_offers,
       c.n_products                            AS competitor_products,
       s.median_price_uzs                      AS secret_median_uzs,
       c.median_price_uzs                      AS competitor_median_uzs,
       s.median_price_uzs - c.median_price_uzs AS difference_uzs,
       ROUND(100.0 * (s.median_price_uzs * 1.0 / c.median_price_uzs - 1), 1) AS difference_pct,
       CASE WHEN s.n_offers >= :min_items AND c.n_products >= :min_items
            THEN 'displayed' ELSE 'insufficient_evidence' END AS evidence
FROM competitor c
JOIN secret     s ON s.category = c.category
ORDER BY c.category, c.operator_group;
