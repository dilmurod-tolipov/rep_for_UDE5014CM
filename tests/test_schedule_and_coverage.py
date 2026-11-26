"""The two measures the Module Leader asked for on 26 November 2026.

1. O1 measured against **every scheduled run, including any that never started**, rather than only
   against the runs that did start. A scheduler that fires nothing looks perfect to a rate computed
   over started runs, which is exactly the blind spot he closed.
2. Whether the category comparisons change when restricted to **days with coverage from all four
   groups** - his "most useful check for your conclusions".
"""
import pytest

from priceintel import config
from priceintel.analysis import comparison
from priceintel.analysis.categories import classify_listings, load_rules
from priceintel.analysis.features import build_features
from priceintel.analysis.pipeline import build_dataset
from priceintel.quality import SCHEDULE_UTC_HOURS, run_checks, scheduled_slots
from tests.conftest import add_fetch, add_run, shop_id

WINDOW = {"window_start": "2026-11-09", "window_end": "2026-12-06"}


def test_the_window_holds_two_slots_a_day():
    slots = scheduled_slots(config.APPROVED_WINDOW_START, config.APPROVED_WINDOW_END)
    assert len(slots) == 56, "28 approved days, two scheduled runs a day"
    assert {s.hour for s in slots} == set(SCHEDULE_UTC_HOURS)
    assert slots == sorted(slots)


def check(results, name):
    return next(r for r in results if r.check_name == name)


def complete_run(conn, started_at, *, groups_reached=4):
    run = conn.execute(
        "INSERT INTO scrape_runs (kind, purpose, triggered_by, started_at, finished_at, status,"
        " git_commit, git_dirty, scraper_version, runner_host, shops_expected, shops_collected)"
        " VALUES ('competitor_scrape', 'test', 'scheduled', ?, ?, ?, ?, 0, 'test', 'pytest', 4, ?)"
        " RETURNING run_id",
        (started_at, started_at, "success" if groups_reached == 4 else "partial", "0" * 40,
         groups_reached)).fetchone()[0]
    return run


def test_a_slot_that_never_started_counts_as_a_failure(market_db):
    """Two slots elapse; one run starts and is perfect. A rate over started runs says 100%, which
    is the number that would have hidden the gap."""
    complete_run(market_db, "2026-11-09T03:17:00Z")
    complete_run(market_db, "2026-11-10T03:17:00Z")        # the 15:17 slot of the 9th never ran
    results = run_checks(market_db, purpose="test", store=False)
    started = check(results, "run_success_rate")
    scheduled = check(results, "scheduled_slot_completion")
    assert started.measured == 100.0, "every run that started was complete"
    assert scheduled.measured < 100.0, "but a scheduled slot produced nothing"
    assert "never started" in scheduled.detail


def test_the_streak_counts_back_from_the_newest_run(market_db):
    complete_run(market_db, "2026-11-09T03:17:00Z", groups_reached=2)
    complete_run(market_db, "2026-11-09T15:17:00Z")
    complete_run(market_db, "2026-11-10T03:17:00Z")
    streak = check(run_checks(market_db, purpose="test", store=False), "consecutive_complete_runs")
    assert streak.measured == 2, "the incomplete run ends the streak behind it"


def test_a_broken_streak_resets(market_db):
    complete_run(market_db, "2026-11-09T03:17:00Z")
    complete_run(market_db, "2026-11-09T15:17:00Z", groups_reached=3)
    streak = check(run_checks(market_db, purpose="test", store=False), "consecutive_complete_runs")
    assert streak.measured == 0


# ---------------------------------------------------------------------------
# Full-coverage days
# ---------------------------------------------------------------------------

@pytest.fixture
def two_days(market_db):
    """Day one: only PROBUKET reports, and it is expensive. Day two: every group reports, and
    PROBUKET has dropped its price. One product per shop, observed on both days."""
    rules = load_rules(config.CATEGORY_RULES_FILE)
    partial = complete_run(market_db, "2026-11-09T03:17:00Z", groups_reached=1)
    full = complete_run(market_db, "2026-11-10T03:17:00Z", groups_reached=4)
    listings = {}
    for shop, host in (("probuket", "pro-buket.uz"), ("uzflora", "uzflora.com")):
        for i in range(12):
            listings[(shop, i)] = market_db.execute(
                "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at,"
                " last_seen_at, last_title, site_category) VALUES (?, ?, ?, ?, ?, ?, 'bukety')"
                " RETURNING listing_id",
                (shop_id(market_db, shop), f"https://{host}/product/p{i}/", partial,
                 "2026-11-09T03:17:00Z", "2026-11-10T03:17:00Z", f"Букет {i}")).fetchone()[0]

    def observe(run, shop, price, at):
        fetch = add_fetch(market_db, run, shop=shop, url=f"https://{shop}.test/catalog/")
        for i in range(12):
            market_db.execute(
                "INSERT INTO price_observations (listing_id, run_id, fetch_id, observed_at,"
                " source_type, title, price_uzs, currency_shown) VALUES (?, ?, ?, ?, 'scrape',"
                " 'x', ?, 'UZS')", (listings[(shop, i)], run, fetch, at, price))

    observe(partial, "probuket", 3_000_000, "2026-11-09T03:17:00Z")      # the dear day
    observe(full, "probuket", 1_000_000, "2026-11-10T03:17:00Z")
    observe(full, "uzflora", 500_000, "2026-11-10T03:17:00Z")
    classify_listings(market_db, rules)
    build_features(market_db, rules)
    run_id, _ = build_dataset(market_db, purpose="test", rules_version=rules.version, **WINDOW)
    return market_db, run_id


def test_only_days_with_every_group_are_full_coverage(two_days):
    conn, _ = two_days
    assert comparison.full_coverage_days(conn, "test") == ["2026-11-10"]


def test_the_restriction_reprices_products_from_those_days_alone(two_days):
    """PROBUKET's median over both days is 2,000,000; over the full-coverage day alone it is
    1,000,000. The check must use the second, or it is not answering the question."""
    conn, run_id = two_days
    main = comparison.competitor_prices(conn, run_id)
    restricted = comparison.competitor_prices(conn, run_id, full_coverage_only=True)
    assert main[("bouquets_unspecified", "PROBUKET")][0] == 2_000_000
    assert restricted[("bouquets_unspecified", "PROBUKET")][0] == 1_000_000
    assert restricted[("bouquets_unspecified", "UZFLORA")][0] == 500_000


def test_a_product_never_seen_on_a_full_day_is_dropped(two_days):
    conn, run_id = two_days
    partial_run = conn.execute("SELECT run_id FROM scrape_runs WHERE status = 'partial'").fetchone()[0]
    fetch = add_fetch(conn, partial_run, shop="probuket", url="https://pro-buket.uz/catalog/")
    listing = conn.execute(
        "INSERT INTO listings (shop_id, url, first_seen_run_id, first_seen_at, last_seen_at,"
        " last_title, site_category) VALUES (?, 'https://pro-buket.uz/product/gone/', ?,"
        " '2026-11-09T03:17:00Z', '2026-11-09T03:17:00Z', 'Букет исчез', 'bukety')"
        " RETURNING listing_id", (shop_id(conn, "probuket"), partial_run)).fetchone()[0]
    conn.execute(
        "INSERT INTO price_observations (listing_id, run_id, fetch_id, observed_at, source_type,"
        " title, price_uzs, currency_shown) VALUES (?, ?, ?, '2026-11-09T03:17:00Z', 'scrape',"
        " 'x', 9000000, 'UZS')", (listing, partial_run, fetch))
    rules_version = load_rules(config.CATEGORY_RULES_FILE).version
    classify_listings(conn, load_rules(config.CATEGORY_RULES_FILE))
    build_features(conn, load_rules(config.CATEGORY_RULES_FILE))
    new_run, _ = build_dataset(conn, purpose="test", rules_version=rules_version, **WINDOW)

    main = comparison.competitor_prices(conn, new_run)
    restricted = comparison.competitor_prices(conn, new_run, full_coverage_only=True)
    assert 9_000_000 in main[("bouquets_unspecified", "PROBUKET")]
    assert 9_000_000 not in restricted[("bouquets_unspecified", "PROBUKET")], (
        "a product only ever seen on a day with missing coverage cannot be in the restricted set")
