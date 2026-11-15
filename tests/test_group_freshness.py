"""A source that goes quiet must fail a check of its own.

On 13 November 2026 loveflowers.uz redesigned its theme. The pages still returned HTTP 200, the
parser found nothing in them, and the group contributed no observations to five assessed runs. Every
overall measure stayed green, because the other three groups were collecting normally: the newest
observation was minutes old, the page success rate was high, nothing was quarantined. The loss was
found by reading the run table by hand three days later.

`group_freshness_days` is the check that would have caught it on the first run."""
import pytest

from priceintel import config
from priceintel.analysis.categories import load_rules
from priceintel.quality import run_checks
from tests.conftest import TS, add_fetch, add_observation, add_run, shop_id

FRESH = None    # filled in per test: an observation timestamp "now"


@pytest.fixture
def rules():
    return load_rules(config.CATEGORY_RULES_FILE)


def collect_from(conn, shop, observed_at):
    run_id = add_run(conn, purpose="test")
    host = {"uzflora": "uzflora.com", "loveflowers": "loveflowers.uz",
            "probuket": "pro-buket.uz", "kamilas": "kamilas.uz"}[shop]
    fetch = add_fetch(conn, run_id, shop=shop, url=f"https://{host}/")
    listing = conn.execute(
        "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
        " last_title, site_category) VALUES (?, ?, ?, ?, ?, 'Букет «Тест»', 'bukety')"
        " RETURNING listing_id",
        (shop_id(conn, shop), f"https://{host}/product/{shop}-1/", run_id, TS,
         observed_at)).fetchone()[0]
    conn.execute(
        "INSERT INTO price_observations (listing_id, run_id, fetch_id, observed_at, source_type,"
        " title, price_uzs, currency_shown) VALUES (?, ?, ?, ?, 'scrape', 'Букет «Тест»',"
        " 300000, 'UZS')", (listing, run_id, fetch, observed_at))


def check_rows(conn, rules, name):
    return {r.scope: r for r in run_checks(conn, purpose="test", rules_version=rules.version,
                                           store=False) if r.check_name == name}


def test_every_active_group_gets_its_own_freshness_check(market_db, rules):
    now = market_db.execute("SELECT strftime('%Y-%m-%dT%H:%M:%SZ', 'now')").fetchone()[0]
    for shop in ("uzflora", "loveflowers", "probuket", "kamilas"):
        collect_from(market_db, shop, now)
    rows = check_rows(market_db, rules, "group_freshness_days")
    assert set(rows) == {"UZFLORA", "LOVEFLOWERS_NET", "PROBUKET", "KAMILAS"}
    assert all(r.status == "pass" for r in rows.values())


def test_a_group_that_stops_collecting_fails_while_the_others_pass(market_db, rules):
    """The exact shape of the 13 November failure."""
    now = market_db.execute("SELECT strftime('%Y-%m-%dT%H:%M:%SZ', 'now')").fetchone()[0]
    stale = market_db.execute(
        "SELECT strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-3 days')").fetchone()[0]
    for shop in ("uzflora", "probuket", "kamilas"):
        collect_from(market_db, shop, now)
    collect_from(market_db, "loveflowers", stale)

    rows = check_rows(market_db, rules, "group_freshness_days")
    assert rows["LOVEFLOWERS_NET"].status == "fail"
    assert rows["LOVEFLOWERS_NET"].measured >= 2.9
    assert all(rows[g].status == "pass" for g in ("UZFLORA", "PROBUKET", "KAMILAS"))

    overall = next(r for r in run_checks(market_db, purpose="test", rules_version=rules.version,
                                         store=False) if r.check_name == "freshness_days")
    assert overall.status == "pass", (
        "this is why the per-group check exists: the overall freshness stays green while one "
        "source is three days stale")


def test_a_group_that_never_collected_fails(market_db, rules):
    now = market_db.execute("SELECT strftime('%Y-%m-%dT%H:%M:%SZ', 'now')").fetchone()[0]
    collect_from(market_db, "uzflora", now)
    rows = check_rows(market_db, rules, "group_freshness_days")
    assert rows["LOVEFLOWERS_NET"].status == "fail"
    assert "none in this dataset" in rows["LOVEFLOWERS_NET"].detail


def test_the_checks_are_recorded_per_group(market_db, rules):
    now = market_db.execute("SELECT strftime('%Y-%m-%dT%H:%M:%SZ', 'now')").fetchone()[0]
    collect_from(market_db, "uzflora", now)
    run_checks(market_db, purpose="test", rules_version=rules.version)
    stored = market_db.execute(
        "SELECT scope, status FROM data_quality_checks WHERE check_name = 'group_freshness_days'"
        " ORDER BY scope").fetchall()
    assert len(stored) == 4
    assert {r["scope"] for r in stored} == {"UZFLORA", "LOVEFLOWERS_NET", "PROBUKET", "KAMILAS"}
