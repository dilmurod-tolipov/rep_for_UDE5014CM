"""Assign every listing to one analysis category from text only.

The rules live in a versioned JSON file (``config/category_rules.v1.json``), not in this module, so
that the rules can be committed and tagged before any analysis run and cited by version in the report.
This module only *applies* them.

Three guarantees that the design depends on:

* **Price independence.** The only inputs are the title, the URL path and the shop's own section
  slugs. ``load_rules`` rejects any matcher key it does not know, so a rule that tried to look at a
  price could not be loaded at all (``test_categories.py::test_rules_cannot_match_on_price``).
* **Determinism and auditability.** Rules are tried in file order, first match wins, and the
  classification records which rule fired and on what evidence. The same rules file always gives the
  same category for the same text.
* **No guessing.** A bouquet whose composition is not stated becomes ``bouquets_unspecified`` rather
  than being assumed to be mixed, and anything no rule matches becomes ``unclassified`` and is
  counted, never silently dropped.

Matching is whole-word: text is lower-cased, every character that is not a letter or digit becomes a
space, and a keyword must sit between spaces. That is why "Розовое сердце" (pink heart) does not match
the rose keyword "розы", while "Белые розы" does.
"""
import hashlib
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from priceintel.db import transaction

# A rule may only look at these. Anything else (a price, a currency, a sale flag) is a load error.
MATCHERS = ("site_category_any", "url_any", "title_any", "title_names_flower_type")
RULE_KEYS = ("id", "category", "reason", *MATCHERS)
SPLIT_CATEGORY = "bouquets_split"   # resolved by the flower types named in the title
UNCLASSIFIED = "unclassified"

_NOT_WORD = re.compile(r"[^0-9a-zа-я]+")


class RulesError(ValueError):
    """The rules file is malformed or uses a matcher that is not allowed."""


@dataclass(frozen=True)
class Rules:
    version: str
    effective_from: str
    categories: dict[str, str]
    exclusions: list[dict]
    sections: list[dict]
    split: dict[str, str]
    flower_lexicon: dict[str, list[str]]
    source_file: str = ""
    sha256: str = ""

    @property
    def ordered_rules(self) -> list[dict]:
        """Exclusions first, then sections: a balloon is never classified as a bouquet."""
        return [*self.exclusions, *self.sections]


@dataclass(frozen=True)
class Classification:
    category: str
    rule_id: str
    evidence: str
    flower_types: tuple[str, ...]


def load_rules(path: Path | str) -> Rules:
    """Read and check a rules file. Raises ``RulesError`` rather than classifying with bad rules."""
    text = Path(path).read_text(encoding="utf-8")
    data = json.loads(text)
    for key in ("rules_version", "categories", "exclusions", "sections", "bouquets_split",
                "flower_lexicon"):
        if key not in data:
            raise RulesError(f"rules file is missing {key!r}")
    categories: dict[str, str] = data["categories"]
    split = {k: v for k, v in data["bouquets_split"].items() if not k.startswith("_")}
    rules = [*data["exclusions"], *data["sections"]]
    seen: set[str] = set()
    for rule in rules:
        unknown = set(rule) - set(RULE_KEYS)
        if unknown:
            raise RulesError(f"rule {rule.get('id')!r} uses matcher(s) {sorted(unknown)}; "
                             f"only {list(MATCHERS)} may be matched on (categories must not use price)")
        if "id" not in rule or "category" not in rule:
            raise RulesError(f"rule {rule!r} needs an id and a category")
        if rule["id"] in seen:
            raise RulesError(f"duplicate rule id {rule['id']!r}")
        seen.add(rule["id"])
        if rule["category"] not in categories and rule["category"] != SPLIT_CATEGORY:
            raise RulesError(f"rule {rule['id']!r} uses unknown category {rule['category']!r}")
        if not any(m in rule for m in MATCHERS):
            raise RulesError(f"rule {rule['id']!r} matches nothing")
    for target in split.values():
        if target not in categories:
            raise RulesError(f"bouquets_split target {target!r} is not a declared category")
    if UNCLASSIFIED not in categories:
        raise RulesError(f"categories must declare {UNCLASSIFIED!r} for listings no rule matched")
    return Rules(data["rules_version"], data.get("effective_from", ""), categories,
                 data["exclusions"], data["sections"], split, data["flower_lexicon"],
                 source_file=Path(path).name,
                 sha256=hashlib.sha256(text.encode("utf-8")).hexdigest())


def normalise(text: str | None) -> str:
    """Lower-case, fold 'ё' to 'е', turn punctuation into spaces and pad with spaces, so that a
    keyword surrounded by spaces matches whole words and whole phrases only."""
    if not text:
        return " "
    folded = unicodedata.normalize("NFKC", text).lower().replace("ё", "е")
    return f" {' '.join(_NOT_WORD.sub(' ', folded).split())} "


def url_section_path(url: str | None) -> str:
    """The section part of a URL: the path without its last segment and without the query string.

    Only sections are evidence of a category. The last segment is the product's own slug, which
    repeats the title ('/product/belye-rozy/'), and treating it as a section made a mixed bouquet
    named 'Розы и лилии' look like a rose section. The query string is dropped so that a currency or
    sort parameter can never influence a category."""
    segments = urlsplit(url or "").path.strip("/").split("/")
    return normalise("/".join(segments[:-1]))


def site_category_slugs(site_category: str | None) -> list[str]:
    """'8-marta,bukety' -> ['8-marta', 'bukety'] (the shop's own section slugs, as published)."""
    return [s.strip().lower() for s in (site_category or "").split(",") if s.strip()]


def flower_types_in(title: str, lexicon: dict[str, list[str]]) -> tuple[str, ...]:
    """Distinct canonical flower types named in a title, e.g. ('lily', 'rose'). Used both for the
    mono/mixed split and later for the flower-type-restricted secondary comparison."""
    text = normalise(title)
    return tuple(sorted(t for t, words in lexicon.items() if any(f" {w} " in text for w in words)))


def _first_hit(rule: dict, title: str, url_path: str, slugs: list[str],
               flower_types: tuple[str, ...]) -> str | None:
    """Evidence string for the first matcher of this rule that fires, or None. Matchers are
    alternatives (OR): a box is a box whether the shop's section or the title says so."""
    for slug in rule.get("site_category_any", []):
        if slug.lower() in slugs:
            return f"site_category={slug}"
    for word in rule.get("url_any", []):
        if f" {normalise(word).strip()} " in url_path:
            return f"url~{word}"
    for word in rule.get("title_any", []):
        if f" {normalise(word).strip()} " in title:
            return f"title~{word}"
    if rule.get("title_names_flower_type") and flower_types:
        return f"title names flower type(s): {', '.join(flower_types)}"
    return None


def classify(title: str | None, url: str | None, site_category: str | None,
             rules: Rules) -> Classification:
    """Apply the rules to one listing (a competitor product page or a Secret offer)."""
    title_n = normalise(title)
    url_n = url_section_path(url)
    slugs = site_category_slugs(site_category)
    types = flower_types_in(title or "", rules.flower_lexicon)
    for rule in rules.ordered_rules:
        evidence = _first_hit(rule, title_n, url_n, slugs, types)
        if evidence is None:
            continue
        category = rule["category"]
        if category == SPLIT_CATEGORY:
            category = (rules.split["no_type"] if not types else
                        rules.split["one_type"] if len(types) == 1 else
                        rules.split["many_types"])
        return Classification(category, rule["id"], evidence, types)
    return Classification(UNCLASSIFIED, "none", "no rule matched", types)


# ---------------------------------------------------------------------------
# Database side: store one assignment per listing per rules version
# ---------------------------------------------------------------------------

def register_rules(conn, rules: Rules) -> None:
    """Record the rules version, its SHA-256 and its category vocabulary in the database.

    Re-registering the same version with a different file is refused, exactly as for schema
    migrations: results already stored under a version must stay reproducible from that file."""
    row = conn.execute("SELECT sha256, source_file FROM category_rule_sets WHERE rules_version = ?",
                       (rules.version,)).fetchone()
    if row is not None and row["sha256"] != rules.sha256:
        raise RulesError(
            f"rules version {rules.version} was already applied from {row['source_file']} with a "
            f"different content (sha256 {row['sha256'][:12]}...); bump rules_version instead of "
            f"editing a version that has been used")
    with transaction(conn):
        for code, name in rules.categories.items():
            conn.execute("INSERT INTO analysis_categories (code, name) VALUES (?, ?)"
                         " ON CONFLICT (code) DO UPDATE SET name = excluded.name", (code, name))
        conn.execute(
            "INSERT INTO category_rule_sets (rules_version, effective_from, source_file, sha256)"
            " VALUES (?, ?, ?, ?) ON CONFLICT (rules_version) DO NOTHING",
            (rules.version, rules.effective_from, rules.source_file, rules.sha256))


def classify_listings(conn, rules: Rules, *, shop_codes: list[str] | None = None) -> Counter:
    """Classify every listing (or only the given shops) and store the result in
    ``listing_categories``. Re-running with the same rules version overwrites the same rows, so the
    command is idempotent; a new rules version adds a new set of rows and keeps the old one for
    comparison. Returns the count per category."""
    sql = ("SELECT l.listing_id, l.last_title, l.url, l.site_category FROM listings l"
           " JOIN shops s ON s.shop_id = l.shop_id")
    params: list = []
    if shop_codes:
        sql += f" WHERE s.code IN ({', '.join('?' * len(shop_codes))})"
        params += shop_codes
    register_rules(conn, rules)
    rows = conn.execute(sql + " ORDER BY l.listing_id", params).fetchall()
    counts: Counter = Counter()
    with transaction(conn):
        for r in rows:
            c = classify(r["last_title"], r["url"], r["site_category"], rules)
            conn.execute(
                "INSERT INTO listing_categories (listing_id, rules_version, category, rule_id,"
                " evidence, flower_types) VALUES (?, ?, ?, ?, ?, ?)"
                " ON CONFLICT (listing_id, rules_version) DO UPDATE SET"
                " category = excluded.category, rule_id = excluded.rule_id,"
                " evidence = excluded.evidence, flower_types = excluded.flower_types,"
                " classified_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')",
                (r["listing_id"], rules.version, c.category, c.rule_id, c.evidence,
                 ",".join(c.flower_types) or None))
            counts[c.category] += 1
    return counts


def coverage_rows(conn, rules_version: str, *, purpose: str | None = None) -> list[dict]:
    """Distinct listings per operator group and category — the body of Table 1 (sampling plan).

    Counting is over *listings*, not observations, so repeated price snapshots of the same product
    cannot inflate the counts (feedback point 4, 26/10/2026). With ``purpose`` only listings that
    were observed in a run of that purpose are counted, which keeps dev and assessed data apart."""
    sql = ("SELECT s.operator_group AS operator, s.is_own_shop, c.category,"
           " COUNT(DISTINCT l.listing_id) AS n_listings"
           " FROM listing_categories c"
           " JOIN listings l ON l.listing_id = c.listing_id"
           " JOIN shops    s ON s.shop_id    = l.shop_id"
           " WHERE c.rules_version = ?")
    params: list = [rules_version]
    if purpose:
        sql += (" AND EXISTS (SELECT 1 FROM price_observations o JOIN scrape_runs r"
                " ON r.run_id = o.run_id WHERE o.listing_id = l.listing_id AND r.purpose = ?)")
        params.append(purpose)
    sql += (" GROUP BY s.operator_group, s.is_own_shop, c.category"
            " ORDER BY s.operator_group, c.category")
    return [dict(r) for r in conn.execute(sql, params).fetchall()]
