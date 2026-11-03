"""Secret's reference offers: minimal fields, provenance, repost grouping, idempotent re-import.

Everything here runs on the SYNTHETIC export in tests/fixtures: no real channel content is used in
the test suite, and the real export never enters the public repository."""
import json
from pathlib import Path

import pytest

from priceintel import config
from priceintel.analysis.categories import load_rules
from priceintel.reference.offers import (
    ImportError_,
    distinct_offers_by_category,
    import_offers,
)

EXPORT = Path(__file__).parent / "fixtures" / "telegram_export_synthetic.json"
CSV = Path(__file__).parent / "fixtures" / "reference_offers_synthetic.csv"
CONSENT = "Synthetic test data; no consent needed (tests/fixtures)."


@pytest.fixture
def rules():
    return load_rules(config.CATEGORY_RULES_FILE)


def do_import(conn, path=EXPORT, rules=None, exported_at="2026-11-21"):
    return import_offers(conn, path, exported_at=exported_at, consent_note=CONSENT,
                         purpose="test", rules=rules)


def test_import_keeps_only_offers_with_a_labelled_price(market_db):
    s = do_import(market_db)
    # 102, 103, 104, 107, 108 have one labelled price; 105 has none, 106 has two, 101 is a service
    # message
    assert s.rows_stored == 5
    assert any("no_price" in r for r in s.skipped)
    assert any("multiple_prices" in r for r in s.skipped)


def test_contact_lines_are_never_stored(market_db):
    do_import(market_db)
    stored = " ".join(r[0] for r in market_db.execute("SELECT title FROM reference_offers"))
    assert "998" not in stored and "@" not in stored and "t.me/" not in stored.replace(
        "https://t.me/", "")
    columns = {r[1] for r in market_db.execute("PRAGMA table_info(reference_offers)")}
    assert "caption" not in columns and "phone" not in columns  # only what the comparison needs


def test_reposts_are_one_offer_however_long_the_gap(market_db):
    """Approval clarification 4: neither the passing of 14 days nor a price change makes a repost a
    new independent item."""
    do_import(market_db)
    rows = market_db.execute(
        "SELECT post_id, offer_group_id, match_confidence FROM reference_offers"
        " ORDER BY post_id").fetchall()
    groups = {r["post_id"]: r["offer_group_id"] for r in rows}
    assert groups[102] == groups[104], "a repost two days later is the same offer"
    assert groups[107] == groups[102], "the same caption 18 days later is still the same offer"
    assert groups[108] == groups[102], "a price change does not create a new offer"
    distinct = market_db.execute("SELECT COUNT(*) FROM v_reference_distinct_offers").fetchone()[0]
    assert (len(rows), distinct) == (5, 2)      # the bouquet (4 posts) and the box (1 post)


def test_a_price_change_is_recorded_as_an_uncertain_match(market_db):
    s = do_import(market_db)
    confidence = {r["post_id"]: r["match_confidence"] for r in market_db.execute(
        "SELECT post_id, match_confidence FROM reference_offers")}
    assert confidence[102] == "unique"          # the first post of its group
    assert confidence[104] == "exact"           # same caption, same price
    assert confidence[108] == "uncertain"       # same caption, different price
    assert any("uncertain" in line for line in s.skipped), "the flag must be reported, not silent"


def test_a_distinct_offer_is_summarised_by_the_median_of_its_posted_prices(market_db):
    do_import(market_db)
    row = market_db.execute(
        "SELECT price_uzs, lowest_price_uzs, highest_price_uzs, posts"
        " FROM v_reference_distinct_offers WHERE posts > 1").fetchone()
    # posted at 1.25M three times and 1.45M once -> median 1.25M, range kept for the report
    assert (row["posts"], row["price_uzs"]) == (4, 1_250_000)
    assert (row["lowest_price_uzs"], row["highest_price_uzs"]) == (1_250_000, 1_450_000)


def test_distinct_offer_is_dated_by_its_first_publication(market_db):
    do_import(market_db)
    row = market_db.execute(
        "SELECT first_published_at, last_seen_at, posts FROM v_reference_distinct_offers"
        " WHERE posts > 1").fetchone()
    assert row["first_published_at"].startswith("2026-11-02")
    assert row["last_seen_at"].startswith("2026-11-22")   # a later repost never re-dates the offer
    assert row["posts"] == 4


def test_provenance_is_recorded_and_the_same_file_cannot_be_imported_twice(market_db):
    s = do_import(market_db)
    row = market_db.execute("SELECT * FROM reference_imports WHERE import_id = ?",
                            (s.import_id,)).fetchone()
    assert (row["source_kind"], row["file_name"]) == ("telegram_export", EXPORT.name)
    assert len(row["file_sha256"]) == 64 and row["exported_at"] == "2026-11-21"
    assert row["consent_note"] and row["rows_stored"] == 5
    with pytest.raises(ImportError_, match="already been imported"):
        do_import(market_db)


def test_reimporting_a_longer_export_adds_only_new_posts(market_db, tmp_path):
    """The owner exports once after the window closes; if a second export is needed it overlaps the
    first, and only the posts that are new may be added."""
    do_import(market_db)
    data = json.loads(EXPORT.read_text(encoding="utf-8"))
    data["messages"].append({"id": 109, "type": "message", "date": "2026-11-23T10:00:00",
                             "text": "Корзина с розами\nСтоимость: 3 100 000"})
    longer = tmp_path / "result.json"
    longer.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    s = do_import(market_db, longer, exported_at="2026-11-24")
    assert s.rows_stored == 1
    assert market_db.execute("SELECT COUNT(*) FROM reference_offers").fetchone()[0] == 6


def test_categories_come_from_the_committed_rules(market_db, rules):
    do_import(market_db, rules=rules)
    rows = {r["post_id"]: r["category"] for r in market_db.execute(
        "SELECT post_id, category FROM reference_offers")}
    assert rows[102] == "mixed_bouquets"        # "из роз и эустомы" = two flower types
    assert rows[103] == "boxes_baskets"         # "в коробке"
    assert all(r["rules_version"] == rules.version for r in market_db.execute(
        "SELECT rules_version FROM reference_offers"))
    counts = {r["category"]: r["n_offers"] for r in distinct_offers_by_category(market_db)}
    assert counts["boxes_baskets"] == 1 and counts["mixed_bouquets"] == 1


def test_csv_fallback_uses_the_same_path(market_db, rules):
    s = do_import(market_db, CSV, rules=rules)
    assert s.rows_stored == 2
    assert market_db.execute(
        "SELECT source_kind FROM reference_imports WHERE import_id = ?",
        (s.import_id,)).fetchone()[0] == "csv"


def test_reference_rows_are_not_price_observations(market_db, rules):
    """The point of the separate table: nothing from the reference import reaches the primary data."""
    do_import(market_db, rules=rules)
    assert market_db.execute("SELECT COUNT(*) FROM price_observations").fetchone()[0] == 0
    assert market_db.execute("SELECT COUNT(*) FROM listings").fetchone()[0] == 0
    assert market_db.execute(
        "SELECT COUNT(*) FROM scrape_runs WHERE kind = 'own_snapshot'").fetchone()[0] == 0
