-- market_intel migration 004: operator groups and mirror domains (ADR-001)
--
-- Module Leader, 26/10/2026, point 1: "Record the evidence supporting each grouping, assign an
-- operator/catalogue identifier, and map the related domains to it. Mirrored listings must not
-- increase the number of independent competitors or products."
--
-- `operator` was free text. `operator_group` is the identifier the analysis counts
-- (PROBUKET, UZFLORA, LOVEFLOWERS_NET, KAMILAS), and `is_mirror` marks a domain that republishes
-- another domain's catalogue. The evidence for each grouping is in docs/compliance/source_groups.md.
ALTER TABLE shops ADD COLUMN operator_group TEXT;
ALTER TABLE shops ADD COLUMN is_mirror INTEGER NOT NULL DEFAULT 0 CHECK (is_mirror IN (0, 1));

UPDATE shops SET operator_group = CASE operator
    WHEN 'Pro-Buket'           THEN 'PROBUKET'
    WHEN 'Uzflora'             THEN 'UZFLORA'
    WHEN 'Love Flowers network' THEN 'LOVEFLOWERS_NET'
    WHEN 'Kamila''s'           THEN 'KAMILAS'
    WHEN 'Secret'              THEN 'SECRET'
    ELSE upper(replace(operator, ' ', '_')) END;

-- Every domain that is not the one we collect from is a mirror of its group.
UPDATE shops SET is_mirror = 1 WHERE is_active = 0 AND is_own_shop = 0
  AND operator_group IN (SELECT operator_group FROM shops WHERE is_active = 1 GROUP BY operator_group);

-- One collected domain per operator group: this is what stops mirrors inflating the counts.
CREATE UNIQUE INDEX ux_shops_one_active_domain_per_group
    ON shops (operator_group) WHERE is_active = 1 AND is_own_shop = 0;
