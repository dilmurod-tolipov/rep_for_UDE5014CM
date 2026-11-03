-- market_intel migration 010: offer identity across the whole window (ADR-008)
--
-- Module Leader, 2026-11-03, clarification 4: "An identifiable offer should not become a new
-- independent item solely because its price changes or 14 days pass. Check reposts across the full
-- window and document uncertain matches."
--
-- The 14-day rule in migration 005 did both of the things that sentence forbids: a repost 15 days
-- later became a second offer, and a repost at a changed price became a second offer. Identity is
-- now the normalised title across the whole import, and a price change is recorded as a second post
-- of the same offer. `match_confidence` says how the grouping was decided, so an uncertain match can
-- be excluded in a robustness check rather than quietly trusted.
ALTER TABLE reference_offers ADD COLUMN match_confidence TEXT NOT NULL DEFAULT 'exact'
    CHECK (match_confidence IN ('exact', 'uncertain', 'unique'));

DROP VIEW v_reference_distinct_offers;

-- One row per distinct offer: posts collapsed, dated by first publication, and summarised by the
-- MEDIAN of the prices the offer was posted at (an offer reposted at 1.2M, 1.2M and 1.4M counts once,
-- at 1.2M). SQLite has no median(), so the middle row is taken by position.
CREATE VIEW v_reference_distinct_offers AS
WITH ranked AS (
    SELECT offer_group_id, price_uzs,
           ROW_NUMBER() OVER (PARTITION BY offer_group_id ORDER BY price_uzs) AS rn,
           COUNT(*)     OVER (PARTITION BY offer_group_id)                    AS n
    FROM reference_offers
)
SELECT o.offer_group_id                       AS offer_id,
       MIN(o.published_at)                    AS first_published_at,
       MAX(o.published_at)                    AS last_seen_at,
       COUNT(*)                               AS posts,
       CAST((SELECT AVG(price_uzs) FROM ranked r
             WHERE r.offer_group_id = o.offer_group_id
               AND r.rn IN ((r.n + 1) / 2, (r.n + 2) / 2)) AS INTEGER) AS price_uzs,
       MIN(o.price_uzs)                       AS lowest_price_uzs,
       MAX(o.price_uzs)                       AS highest_price_uzs,
       MIN(o.title)                           AS title,
       MIN(o.category)                        AS category,
       MIN(o.rules_version)                   AS rules_version,
       MAX(o.match_confidence)                AS match_confidence
FROM reference_offers o
GROUP BY o.offer_group_id;
