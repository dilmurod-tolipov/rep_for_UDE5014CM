"""Operator groups: one collected domain per group, mirrors never collected, counts per group.

This is the automated check promised to the Module Leader (26/10/2026, point 1): mirrored listings
must not increase the number of independent competitors or products."""
import json
import sqlite3
from pathlib import Path

import pytest

from priceintel import config
from priceintel.collect.runner import CollectError, collect

EXPECTED_GROUPS = {"PROBUKET", "UZFLORA", "LOVEFLOWERS_NET", "KAMILAS"}
EVIDENCE_DOC = Path("docs/compliance/source_groups.md")


def active_competitors(conn):
    return conn.execute("SELECT * FROM shops WHERE is_active = 1 AND is_own_shop = 0"
                        " ORDER BY operator_group").fetchall()


def test_each_group_is_collected_from_exactly_one_domain(market_db):
    rows = active_competitors(market_db)
    groups = [r["operator_group"] for r in rows]
    assert set(groups) == EXPECTED_GROUPS
    assert len(groups) == len(set(groups)), "two domains of one group would double-count products"
    assert all(r["is_mirror"] == 0 for r in rows)


def test_a_second_active_domain_in_a_group_is_refused_by_the_database(market_db):
    """Activating a mirror must fail, whatever the code does."""
    with pytest.raises(sqlite3.IntegrityError):
        market_db.execute("UPDATE shops SET is_active = 1 WHERE code = 'cvetov24'")


def test_mirrors_are_registered_inactive_and_flagged(market_db):
    mirrors = market_db.execute(
        "SELECT code, operator_group FROM shops WHERE is_mirror = 1 ORDER BY code").fetchall()
    assert {r["code"] for r in mirrors} == {"cvetov24", "cvetov365", "ultraflowers", "uzflowers"}
    for r in mirrors:
        assert r["operator_group"] in EXPECTED_GROUPS
    assert market_db.execute(
        "SELECT COUNT(*) FROM shops WHERE is_mirror = 1 AND is_active = 1").fetchone()[0] == 0


def test_collect_refuses_a_mirror_domain(market_db):
    with pytest.raises(CollectError, match="not an active competitor shop"):
        collect(market_db, ["cvetov365"], purpose="test")


def test_registry_and_evidence_document_agree():
    """The groups in config/shops.json are the groups documented with evidence."""
    shops = json.loads(config.SHOPS_FILE.read_text(encoding="utf-8"))["shops"]
    doc = EVIDENCE_DOC.read_text(encoding="utf-8")
    for shop in shops:
        assert shop.get("operator_group"), f"{shop['code']} has no operator_group"
    for group in EXPECTED_GROUPS:
        assert f"`{group}`" in doc, f"{group} has no recorded evidence in {EVIDENCE_DOC}"
    for shop in shops:
        if shop.get("is_mirror"):
            assert shop["base_url"].split("//")[1] in doc, f"{shop['code']} is not listed as a mirror"
