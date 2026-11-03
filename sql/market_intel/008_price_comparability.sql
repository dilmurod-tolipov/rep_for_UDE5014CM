-- market_intel migration 008: keep what makes two prices comparable (ADR-008)
--
-- Module Leader, 2026-11-03, clarification 3: "Preserve currency, product variant, discount status
-- and availability. Uzflora displays USD prices, while PROBUKET displays multiple currencies and
-- bouquet sizes, so your UZS comparisons must use an explicit, reproducible price-selection and
-- conversion rule."
--
-- Discount status and availability were already stored (old_price_uzs and availability). These three
-- columns add what was missing, on every observation rather than once per listing, because a shop can
-- change any of them between runs:
--
--   currency_shown    the currency label the shop itself printed beside the number that was read.
--                     The project NEVER converts: a price enters the database only when the shop
--                     publishes it in UZS (uzflora is requested with ?currency=UZS; pro-buket
--                     publishes UZS, USD and RUB on one card and the UZS span is the one read).
--                     Anything else is quarantined as currency_not_uzs, so no exchange rate, and no
--                     date of an exchange rate, can ever enter a comparison.
--   variant_label     which option the price belongs to when a card offers several (a size, a stem
--                     count, a packaging choice). NULL means the shop showed one price for one item.
--   composition_text  what the shop says is in the product, verbatim ("Состав: розы — 15 шт,
--                     фисташка"). It is the source of the stem-count feature and of the
--                     flower-type-restricted secondary comparison; it is stored raw so the feature
--                     can be recomputed without re-collecting.
--
-- Existing rows keep NULL: they were collected before the columns existed, which is itself honest
-- provenance - all of them are purpose = dev.

ALTER TABLE price_observations ADD COLUMN currency_shown   TEXT;
ALTER TABLE price_observations ADD COLUMN variant_label    TEXT;
ALTER TABLE price_observations ADD COLUMN composition_text TEXT;

-- A scraped assessed price must say which currency the shop displayed, and it must be UZS.
-- (SQLite cannot add a CHECK to an existing table, so the rule is a trigger.)
CREATE TRIGGER trg_price_obs_currency_is_uzs
BEFORE INSERT ON price_observations
WHEN NEW.source_type = 'scrape'
 AND NEW.currency_shown IS NOT NULL
 AND lower(NEW.currency_shown) NOT IN ('uzs', 'сум', 'сўм', 'so''m', 'som', 'sum')
BEGIN
    SELECT RAISE(ABORT, 'price must be published in UZS; the project never converts currencies');
END;
