"""Draw the one-page entity-relationship diagram for the report appendix.

    python tools/er_diagram.py          # writes docs/analysis/figures/er_diagram.svg

The Module Leader asked (26 November 2026) for a one-page ER diagram that lets a marker tell the
competitor, reference and synthetic tables apart. That is the organising idea here: the diagram is
laid out in four zones by **what the data is**, not by which module touches it, because the whole
compliance story of this project is which rows are collected evidence and which are not.

The diagram is generated rather than drawn by hand so it cannot drift from the schema: the table
list below is checked against the live databases by `tests/test_er_diagram.py`, which fails if a
table exists in SQL and is missing here.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "analysis" / "figures" / "er_diagram.svg"

W, H = 1180, 820

ZONES = [
    ("A", 16, 54, 560, 430, "#1f6feb",
     "market_intel — collected competitor data (PRIMARY)",
     "Every row produced by this project's own collector. This is the assessed data."),
    ("B", 592, 54, 572, 250, "#8250df",
     "market_intel — derived analysis tables",
     "Computed from the collected rows; rebuilt by the pipeline, never hand-edited."),
    ("C", 592, 318, 572, 166, "#bf8700",
     "market_intel — reference data (NOT primary)",
     "Secret's own published prices, imported once. Excluded from every model by test."),
    ("D", 16, 516, 1148, 288, "#cf222e",
     "secret_shop — operational core (SYNTHETIC fixtures only)",
     "Secret keeps no digital order record. Every row is is_synthetic = 1, enforced by triggers."),
]

# name: (zone, x, y, w, lines)
TABLES = {
    "shops": ("A", 32, 112, 150, ["shop_id PK", "code UQ, operator_group", "is_mirror, is_own_shop"]),
    "scrape_runs": ("A", 205, 112, 164, ["run_id PK", "purpose, status", "git_commit, git_dirty"]),
    "fetch_log": ("A", 392, 112, 152, ["fetch_id PK", "run_id FK, shop_id FK", "content_sha256"]),
    "listings": ("A", 32, 212, 150, ["listing_id PK", "shop_id FK", "url UQ"]),
    "price_observations": ("A", 205, 212, 164, ["observation_id PK", "listing_id FK, run_id FK",
                                                "fetch_id FK", "UQ (listing_id, run_id)"]),
    "rejected_records": ("A", 392, 212, 152, ["reject_id PK", "run_id FK, shop_id FK", "rule"]),
    "shop_delivery_terms": ("A", 32, 330, 170, ["term_id PK", "shop_id FK", "UQ (shop, observed_on)"]),
    "data_quality_checks": ("A", 225, 330, 160, ["check_run_id PK", "check_name, measured",
                                                 "threshold, status"]),
    "category_rule_sets": ("A", 400, 330, 144, ["rules_version PK", "sha256"]),

    "listing_categories": ("B", 608, 112, 166, ["listing_id, rules_version PK", "category FK"]),
    "listing_features": ("B", 788, 112, 166, ["listing_id, rules_version PK", "price_unit, stem_count"]),
    "analysis_categories": ("B", 968, 112, 180, ["code PK", "the shared vocabulary"]),
    "pipeline_runs": ("B", 608, 200, 166, ["pipeline_run_id PK", "window, rules_version"]),
    "analysis_products": ("B", 788, 200, 166, ["pipeline_run_id, listing_id PK", "category, price_unit"]),
    "results tables": ("B", 968, 200, 180, ["hypothesis_tests, comparison_results,",
                                            "model_runs → model_metrics,", "dataset_splits"]),

    "reference_imports": ("C", 608, 376, 180, ["import_id PK", "file_sha256, exported_at",
                                               "consent_note"]),
    "reference_offers": ("C", 812, 376, 180, ["offer_id PK", "import_id FK", "offer_group_id FK self"]),

    "admin_users": ("D", 32, 574, 150, ["admin_user_id PK", "role, is_synthetic"]),
    "clients": ("D", 200, 574, 150, ["client_id PK", "phone_last4, is_synthetic",
                                     "CK consent if real"]),
    "addresses": ("D", 368, 574, 150, ["address_id PK", "client_id FK", "is_synthetic"]),
    "orders": ("D", 536, 574, 164, ["order_id PK", "client_id FK, address_id FK",
                                    "created_by FK, is_synthetic", "total_uzs GENERATED"]),
    "order_items": ("D", 718, 574, 164, ["order_id, line_no PK", "product_id FK",
                                         "line_total_uzs GENERATED"]),
    "payments": ("D", 900, 574, 150, ["payment_id PK", "order_id FK", "is_synthetic"]),
    "categories": ("D", 1068, 574, 96, ["category_id PK", "code"]),
    "products": ("D", 718, 700, 164, ["product_id PK", "category_id FK", "origin, is_synthetic"]),
    "product_price_history": ("D", 900, 700, 184, ["price_id PK", "product_id FK",
                                                   "effective_from, append-only"]),
    "product_attributes": ("D", 536, 700, 164, ["product_id, attribute, value PK"]),
}

EDGES = [
    ("shops", "listings"), ("scrape_runs", "fetch_log"), ("shops", "fetch_log"),
    ("fetch_log", "price_observations"), ("listings", "price_observations"),
    ("scrape_runs", "price_observations"), ("scrape_runs", "rejected_records"),
    ("shops", "shop_delivery_terms"),
    ("listings", "listing_categories"), ("listings", "listing_features"),
    ("analysis_categories", "listing_categories"),
    ("pipeline_runs", "analysis_products"), ("listings", "analysis_products"),
    ("pipeline_runs", "results tables"),
    ("reference_imports", "reference_offers"),
    ("clients", "addresses"), ("clients", "orders"), ("addresses", "orders"),
    ("admin_users", "orders"), ("orders", "order_items"), ("orders", "payments"),
    ("products", "order_items"), ("categories", "products"),
    ("products", "product_price_history"), ("products", "product_attributes"),
]

ROW_H = 15


def box_height(lines):
    return 26 + ROW_H * len(lines)


def anchors(name):
    _, x, y, w, lines = TABLES[name]
    h = box_height(lines)
    return {"cx": x + w / 2, "cy": y + h / 2, "x": x, "y": y, "w": w, "h": h}


def edge_path(a, b):
    """Straight line between the two box centres, clipped to the box edges."""
    pa, pb = anchors(a), anchors(b)
    x1, y1, x2, y2 = pa["cx"], pa["cy"], pb["cx"], pb["cy"]
    downwards, rightwards = y2 > y1, x2 > x1            # decided before anything moves
    if abs(y2 - y1) > abs(x2 - x1):                     # mostly vertical
        y1 = pa["y"] + pa["h"] if downwards else pa["y"]
        y2 = pb["y"] if downwards else pb["y"] + pb["h"]
    else:                                               # mostly horizontal
        x1 = pa["x"] + pa["w"] if rightwards else pa["x"]
        x2 = pb["x"] if rightwards else pb["x"] + pb["w"]
    return f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" class="edge"/>'


def svg():
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="Entity-relationship diagram of both databases">',
        '<style>'
        'text { font-family: "Segoe UI", system-ui, sans-serif; fill: #1f2328; }'
        '.title { font-size: 19px; font-weight: 700; }'
        '.subtitle { font-size: 12.5px; fill: #57606a; }'
        '.zone-title { font-size: 13px; font-weight: 700; }'
        '.zone-note { font-size: 11.5px; fill: #57606a; }'
        '.tname { font-size: 12.5px; font-weight: 700; }'
        '.col { font-size: 11px; fill: #424a53; }'
        '.edge { stroke: #8c959f; stroke-width: 1.1; }'
        '.link { stroke: #cf222e; stroke-width: 1.6; stroke-dasharray: 6 4; }'
        '.linklabel { font-size: 11.5px; fill: #cf222e; }'
        '</style>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="16" y="24" class="title">Competitive Price Intelligence for a Tashkent Flower '
        f'Shop — database design</text>',
        '<text x="16" y="42" class="subtitle">Two SQLite databases, every table STRICT. Zones are '
        'what the data IS: collected evidence, derived, reference, or synthetic.</text>',
    ]
    for _, x, y, w, h, colour, title, note in ZONES:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{colour}0d" '
                     f'stroke="{colour}" stroke-width="1.4"/>')
        parts.append(f'<text x="{x + 14}" y="{y + 22}" class="zone-title" fill="{colour}">'
                     f'{title}</text>')
        parts.append(f'<text x="{x + 14}" y="{y + 38}" class="zone-note">{note}</text>')

    for a, b in EDGES:
        parts.append(edge_path(a, b))

    for name, (zone, x, y, w, lines) in TABLES.items():
        colour = next(z[5] for z in ZONES if z[0] == zone)
        h = box_height(lines)
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#ffffff" '
                     f'stroke="{colour}" stroke-width="1.2"/>')
        parts.append(f'<text x="{x + 8}" y="{y + 16}" class="tname">{name}</text>')
        for i, line in enumerate(lines):
            parts.append(f'<text x="{x + 8}" y="{y + 31 + i * ROW_H}" class="col">{line}</text>')

    # The one connection between the files, which SQLite cannot enforce.
    parts.append('<line x1="1116" y1="160" x2="1116" y2="574" class="link"/>')
    parts.append('<text x="20" y="505" class="linklabel">analysis_categories ↔ categories is '
                 'the only link between the two files. SQLite cannot enforce a foreign key across '
                 'files, so it is checked in code: on every dashboard page load, by '
                 'check-integrity, and by the tests.</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg(), encoding="utf-8")
    shown = OUT.relative_to(ROOT) if OUT.is_relative_to(ROOT) else OUT
    print(f"wrote {shown} ({len(TABLES)} tables, {len(EDGES)} relationships)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
