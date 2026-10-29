-- Q3. "Which competitor products changed price, and by how much?"
--     Asked by: the owner, who wants to know what moved rather than re-read a whole catalogue.
--
-- Compares each listing's newest observation with the one before it, within runs of :purpose, and
-- returns only listings whose price actually changed. LAG() over the observation history is the
-- reason price_observations is append-only: the history is the evidence for this answer.
--
-- Parameters: :purpose, :limit

WITH history AS (
    SELECT l.listing_id,
           s.operator_group,
           l.last_title,
           l.url,
           o.observed_at,
           o.price_uzs,
           LAG(o.price_uzs)   OVER (PARTITION BY l.listing_id
                                   ORDER BY o.observed_at, o.observation_id) AS previous_price_uzs,
           LAG(o.observed_at) OVER (PARTITION BY l.listing_id
                                   ORDER BY o.observed_at, o.observation_id) AS previous_observed_at,
           ROW_NUMBER()       OVER (PARTITION BY l.listing_id
                                   ORDER BY o.observed_at DESC, o.observation_id DESC) AS recency
    FROM price_observations o
    JOIN listings    l ON l.listing_id = o.listing_id
    JOIN shops       s ON s.shop_id    = l.shop_id
    JOIN scrape_runs r ON r.run_id     = o.run_id
    WHERE o.source_type = 'scrape' AND r.purpose = :purpose
)
SELECT operator_group,
       last_title                     AS product,
       previous_observed_at           AS was_seen_at,
       previous_price_uzs             AS was_uzs,
       observed_at                    AS now_seen_at,
       price_uzs                      AS now_uzs,
       price_uzs - previous_price_uzs AS change_uzs,
       ROUND(100.0 * (price_uzs * 1.0 / previous_price_uzs - 1), 1) AS change_pct,
       url
FROM history
WHERE recency = 1
  AND previous_price_uzs IS NOT NULL
  AND price_uzs <> previous_price_uzs
ORDER BY ABS(price_uzs - previous_price_uzs) DESC
LIMIT :limit;
