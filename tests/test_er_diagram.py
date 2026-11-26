"""The appendix ER diagram: it must parse, fit on its page, and match the real schema.

A diagram that has drifted from the schema is worse than none, because a marker checks the report
against the database. So the generator's table list is compared with the tables the migrations
actually create, and the geometry is checked so the one-page figure cannot silently overlap itself
after an edit."""
import xml.etree.ElementTree as ET

import pytest

from priceintel import config
from priceintel.db import init_market_db, init_secret_db
from tools import er_diagram

# Tables that exist in SQL but are deliberately not drawn, each with its reason.
NOT_DRAWN = {
    "schema_migrations": "infrastructure, not project data",
    "dataset_splits": "drawn inside the 'results tables' box",
    "hypothesis_tests": "drawn inside the 'results tables' box",
    "comparison_results": "drawn inside the 'results tables' box",
    "model_runs": "drawn inside the 'results tables' box",
    "model_metrics": "drawn inside the 'results tables' box",
    "source_channels": "withdrawn Telegram collector, kept empty for provenance (ADR-007)",
    "collection_runs": "withdrawn Telegram collector, kept empty for provenance (ADR-007)",
    "source_fetches": "withdrawn Telegram collector, kept empty for provenance (ADR-007)",
    "rejected_posts": "withdrawn Telegram collector, kept empty for provenance (ADR-007)",
}


@pytest.fixture(scope="module")
def schema_tables(tmp_path_factory):
    """Every table the migrations create, from both databases."""
    tmp = tmp_path_factory.mktemp("er")
    from priceintel.db import connect
    names = set()
    init_market_db(tmp / "m.db", config.MARKET_MIGRATIONS, config.SHOPS_FILE,
                   config.CATEGORY_RULES_FILE)
    init_secret_db(tmp / "s.db", config.SECRET_MIGRATIONS, config.SECRET_SOURCES_FILE)
    for name in ("m.db", "s.db"):
        conn = connect(tmp / name)
        names |= {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")}
        conn.close()
    return names


def test_every_table_is_drawn_or_explained(schema_tables):
    drawn = set(er_diagram.TABLES)
    missing = schema_tables - drawn - set(NOT_DRAWN)
    assert not missing, (
        f"these tables exist in SQL but are neither drawn nor listed as deliberately omitted: "
        f"{sorted(missing)}")


def test_nothing_is_drawn_that_does_not_exist(schema_tables):
    invented = {t for t in er_diagram.TABLES if t not in schema_tables and " " not in t}
    assert not invented, f"the diagram shows tables that do not exist: {sorted(invented)}"


def test_every_relationship_connects_two_drawn_tables():
    for a, b in er_diagram.EDGES:
        assert a in er_diagram.TABLES and b in er_diagram.TABLES, f"dangling edge {a} -> {b}"


def test_the_svg_parses_and_fits_its_page(tmp_path):
    svg = er_diagram.svg()
    root = ET.fromstring(svg)                              # raises if it is not valid XML
    assert root.get("viewBox") == f"0 0 {er_diagram.W} {er_diagram.H}"
    for name, (zone, x, y, w, lines) in er_diagram.TABLES.items():
        h = er_diagram.box_height(lines)
        assert 0 <= x and x + w <= er_diagram.W, f"{name} runs off the page horizontally"
        assert 0 <= y and y + h <= er_diagram.H, f"{name} runs off the page vertically"
        zx, zy, zw, zh = next((z[1], z[2], z[3], z[4]) for z in er_diagram.ZONES if z[0] == zone)
        assert zx <= x and x + w <= zx + zw, f"{name} escapes zone {zone} horizontally"
        assert zy <= y and y + h <= zy + zh, f"{name} escapes zone {zone} vertically"


def test_no_two_boxes_overlap():
    boxes = []
    for name, (_, x, y, w, lines) in er_diagram.TABLES.items():
        boxes.append((name, x, y, w, er_diagram.box_height(lines)))
    for i, (n1, x1, y1, w1, h1) in enumerate(boxes):
        for n2, x2, y2, w2, h2 in boxes[i + 1:]:
            apart = x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1
            assert apart, f"{n1} overlaps {n2}"


def test_the_three_data_kinds_are_visibly_separate():
    """The reason the diagram exists: a marker must be able to tell collected, reference and
    synthetic rows apart at a glance."""
    zones = {t: z for t, (z, *_) in er_diagram.TABLES.items()}
    assert zones["price_observations"] == "A", "collected competitor data"
    assert zones["reference_offers"] == "C", "reference data"
    assert zones["orders"] == "D" and zones["payments"] == "D", "synthetic operational data"
    svg = er_diagram.svg()
    assert "PRIMARY" in svg and "NOT primary" in svg and "SYNTHETIC" in svg


def test_the_generator_writes_the_file(monkeypatch, tmp_path):
    out = tmp_path / "er.svg"
    monkeypatch.setattr(er_diagram, "OUT", out)
    assert er_diagram.main() == 0
    assert out.read_text(encoding="utf-8").startswith("<svg")
