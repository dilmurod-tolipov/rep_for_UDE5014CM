"""No Secret reference data, and no development data, can reach a model matrix.

The promise to the Module Leader (26/10/2026, point 4) is enforced in code by
`priceintel.analysis.model_data.model_rows`, which is the only way a model gets its rows."""
from pathlib import Path

import pytest

from priceintel import config
from priceintel.analysis.categories import classify_listings, load_rules
from priceintel.analysis.model_data import model_rows
from priceintel.reference.offers import import_offers
from tests.conftest import TS, add_fetch, add_observation, add_run, shop_id

EXPORT = Path(__file__).parent / "fixtures" / "telegram_export_synthetic.json"


@pytest.fixture
def rules():
    return load_rules(config.CATEGORY_RULES_FILE)


def add_listing(conn, run_id, title, shop, slug, site_category=None):
    host = {"uzflora": "uzflora.com", "kamilas": "kamilas.uz"}[shop]
    return conn.execute(
        "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
        " last_title, site_category) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING listing_id",
        (shop_id(conn, shop), f"https://{host}/product/{slug}/", run_id, TS, TS, title,
         site_category)).fetchone()[0]


@pytest.fixture
def populated(market_db, rules):
    """Two competitor listings observed in an assessed run, one in a dev run, plus Secret's
    reference offers imported from the synthetic export."""
    assessed = add_run(market_db, purpose="test")
    dev = add_run(market_db, purpose="dev")
    for run in (assessed, dev):
        fetch = add_fetch(market_db, run)
        listing = add_listing(market_db, run, "Белые розы", "uzflora", f"roses-{run}", "bukety")
        add_observation(market_db, listing, run, fetch, price=300000)
    import_offers(market_db, EXPORT, exported_at="2026-11-21", consent_note="synthetic test data",
                  purpose="test", rules=rules)
    classify_listings(market_db, rules)
    return market_db


def test_reference_offers_exist_but_never_appear_in_the_model_matrix(populated, rules):
    reference_prices = {r[0] for r in populated.execute("SELECT price_uzs FROM reference_offers")}
    assert reference_prices, "the fixture must actually contain reference offers"
    rows = model_rows(populated, rules_version=rules.version, purpose="test")
    assert rows, "competitor rows should be there"
    assert not reference_prices & {r["price_uzs"] for r in rows}


def test_model_matrix_takes_only_scraped_competitor_rows(populated, rules):
    rows = model_rows(populated, rules_version=rules.version, purpose="test")
    sources = {r[0] for r in populated.execute(
        "SELECT DISTINCT source_type FROM price_observations"
        " WHERE observation_id IN (%s)" % ", ".join(str(r["observation_id"]) for r in rows))}
    assert sources == {"scrape"}
    assert all(r["operator_group"] != "SECRET" for r in rows)


def test_development_rows_are_not_mixed_into_assessed_results(populated, rules):
    assessed = model_rows(populated, rules_version=rules.version, purpose="test")
    dev = model_rows(populated, rules_version=rules.version, purpose="dev")
    assert assessed and dev
    assert not {r["observation_id"] for r in assessed} & {r["observation_id"] for r in dev}


def test_every_row_carries_its_grouping_keys(populated, rules):
    """Grouped cross-validation and leave-one-operator-group-out both need these."""
    for row in model_rows(populated, rules_version=rules.version, purpose="test"):
        assert row["group_key"] and row["operator_group"] and row["observed_at"]
