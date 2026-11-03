"""Features engineered from the text of a listing: what one price actually buys.

Module Leader, 2026-11-03, clarification 3: product variant must be preserved, and the UZS comparison
must use an explicit, reproducible rule. The development crawl showed why this matters concretely: in
`roses_mono`, loveflowers sells a single gerbera stem for 18,000 UZS while the same category holds a
101-stem bundle at 2,500,000 UZS. A median over both describes nothing.

So every listing gets a ``price_unit``:

* ``per_bundle`` - the text states how many stems the price buys ("101 шт", "розы — 15 шт").
  ``stem_count`` is filled in and the evidence is ``stated``.
* ``per_stem`` - either the listing says so ("(за шт)", evidence ``stated``), or no quantity is
  stated and the listing is a single flower: the shop files it in a by-the-stem section, or the title
  is a bare flower name with no arrangement word (evidence ``inferred``). A robustness check re-runs
  the comparison without the inferred ones.
* ``per_item`` - everything else: one bouquet, box, basket or plant sold as one thing.

Only ``per_item`` and ``per_bundle`` listings enter the category comparison (view
``v_comparable_listings``); per-stem listings are reported separately, because a stem price is not an
assortment price.

As with the categories, the rules live in the versioned rules file and the inputs are text only - the
title, the shop's own composition line and the section slug. A price is never an input, and a stem
count is never estimated from a photograph or from a price.
"""
import re
from collections import Counter
from dataclasses import dataclass

from priceintel.analysis.categories import Rules, flower_types_in, normalise, site_category_slugs
from priceintel.db import transaction

MAX_STEMS = 1001          # the schema's upper bound; anything larger is a parsing error
MAX_SIZE_CM = 300


@dataclass(frozen=True)
class Features:
    price_unit: str
    stem_count: int | None
    size_cm: int | None
    flower_types: tuple[str, ...]
    evidence: str
    rule_id: str
    source_text: str


def _first_number(patterns: list[str], text: str, upper: int) -> int | None:
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            value = int(match.group(1))
            if 1 <= value <= upper:
                return value
    return None


def extract(title: str | None, composition: str | None, site_category: str | None,
            rules: Rules, category: str | None = None) -> Features:
    """Read the features of one listing from its text.

    ``category`` is the analysis category already assigned to the listing. It is used for one
    decision only: a potted plant, a box, a basket or a berry set is always one item, never a stem.
    When it is not given it is derived from the same rules, so the function can be used on its own."""
    spec = rules.price_unit
    source = " ".join(part for part in (title, composition) if part)
    text = normalise(source)
    slugs = site_category_slugs(site_category)
    types = flower_types_in(source, rules.flower_lexicon)

    said_per_stem = any(f" {phrase} " in text for phrase in spec.get("per_stem_phrases", []))
    if category is None:
        from priceintel.analysis.categories import classify
        category = classify(title, None, site_category, rules).category
    stems = _first_number(spec["quantity_patterns"], text, MAX_STEMS)
    size = _first_number(spec["size_patterns"], text, MAX_SIZE_CM)
    has_arrangement_word = any(f" {w} " in text for w in spec["arrangement_words"])

    sold_whole = category in spec.get("per_item_categories", [])
    if said_per_stem:
        # "(за шт)" - the shop says the price is for one flower, whatever else the title counts.
        return Features("per_stem", 1, size, types, "stated", "U00", source)
    if stems is not None:
        return Features("per_bundle", stems, size, types, "stated", "U01", source)
    if sold_whole:
        # A plant in a pot, a box, a basket or a berry set is one thing by definition.
        return Features("per_item", None, size, types, "stated", "U05", source)
    if any(slug in slugs for slug in spec["single_flower_sections"]) and not has_arrangement_word:
        return Features("per_stem", 1, size, types, "inferred", "U02", source)
    if types and not has_arrangement_word and len(text.split()) <= 4:
        # "Гербера розовая", "Роза Эквадор 60 см": a flower and its variety, nothing else.
        return Features("per_stem", 1, size, types, "inferred", "U03", source)
    return Features("per_item", None, size, types, "stated" if has_arrangement_word else "inferred",
                    "U04", source)


def build_features(conn, rules: Rules, *, shop_codes: list[str] | None = None) -> Counter:
    """Compute and store the features of every listing. Idempotent per rules version, like the
    categories: re-running overwrites the same rows, a new rules version adds a new set."""
    sql = """
        SELECT l.listing_id, l.last_title, l.site_category,
               (SELECT o.composition_text FROM price_observations o
                WHERE o.listing_id = l.listing_id AND o.composition_text IS NOT NULL
                ORDER BY o.observed_at DESC LIMIT 1) AS composition
               ,(SELECT c.category FROM listing_categories c
                 WHERE c.listing_id = l.listing_id AND c.rules_version = :rules_version)
                AS category
        FROM listings l JOIN shops s ON s.shop_id = l.shop_id"""
    params: dict = {"rules_version": rules.version}
    if shop_codes:
        placeholders = ", ".join(f":shop{i}" for i in range(len(shop_codes)))
        sql += f" WHERE s.code IN ({placeholders})"
        params |= {f"shop{i}": code for i, code in enumerate(shop_codes)}
    rows = conn.execute(sql + " ORDER BY l.listing_id", params).fetchall()

    counts: Counter = Counter()
    with transaction(conn):
        for r in rows:
            f = extract(r["last_title"], r["composition"], r["site_category"], rules,
                        category=r["category"])
            conn.execute(
                "INSERT INTO listing_features (listing_id, rules_version, price_unit, stem_count,"
                " size_cm, flower_types, evidence, rule_id, source_text)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT (listing_id, rules_version) DO UPDATE SET"
                " price_unit = excluded.price_unit, stem_count = excluded.stem_count,"
                " size_cm = excluded.size_cm, flower_types = excluded.flower_types,"
                " evidence = excluded.evidence, rule_id = excluded.rule_id,"
                " source_text = excluded.source_text,"
                " computed_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')",
                (r["listing_id"], rules.version, f.price_unit, f.stem_count, f.size_cm,
                 ",".join(f.flower_types) or None, f.evidence, f.rule_id, f.source_text[:500]))
            counts[f.price_unit] += 1
    return counts


def feature_summary(conn, rules_version: str) -> list[dict]:
    """Price unit by operator group: how much of each catalogue is sold by the stem."""
    return [dict(r) for r in conn.execute("""
        SELECT s.operator_group, f.price_unit, f.evidence,
               COUNT(*)                     AS n_listings,
               SUM(f.stem_count IS NOT NULL) AS with_stem_count
        FROM listing_features f
        JOIN listings l ON l.listing_id = f.listing_id
        JOIN shops    s ON s.shop_id    = l.shop_id
        WHERE f.rules_version = ?
        GROUP BY s.operator_group, f.price_unit, f.evidence
        ORDER BY s.operator_group, f.price_unit""", (rules_version,))]
