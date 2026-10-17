-- market_intel migration 002: keep the shop's own category labels on each listing.
-- Needed by the category-level comparison (analytical question 1) and the coverage rule
-- (>= 20 listings from >= 3 sources per category). Comma-separated WooCommerce category slugs,
-- exactly as the shop publishes them; mapping to our own categories happens in the pipeline.
ALTER TABLE listings ADD COLUMN site_category TEXT;
