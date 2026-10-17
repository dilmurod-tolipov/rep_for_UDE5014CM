"""robots.txt compliance: the real rules of our sources must be applied correctly."""
from priceintel.collect.http import AGENT_TOKEN
from priceintel.collect.robots import RobotsRules, parse_robots

# Excerpt of pro-buket.uz/robots.txt as read on 2026-10-17.
PRO_BUKET = """User-agent: *
Disallow: /cgi-bin
Disallow: /*?*
Disallow: /search/
Disallow: /all/
Disallow: /c/nedorogie-cvety/
Crawl-delay: 5
Sitemap: https://pro-buket.uz/sitemap.xml
"""


def test_wildcard_query_rule_blocks_query_urls_but_not_catalogue():
    rules = parse_robots(PRO_BUKET, AGENT_TOKEN)
    assert not rules.allowed("/en/catalog/?orderby=price")   # Disallow: /*?*
    assert not rules.allowed("/all/")
    assert not rules.allowed("/c/nedorogie-cvety/page/2/")
    assert rules.allowed("/en/catalog/")
    assert rules.allowed("/en/c/rozy/")
    assert rules.crawl_delay == 5


def test_longest_match_wins_and_allow_wins_ties():
    rules = parse_robots("User-agent: *\nDisallow: /shop/\nAllow: /shop/page/\nAllow: /x\nDisallow: /x\n",
                         AGENT_TOKEN)
    assert rules.allowed("/shop/page/3/")
    assert not rules.allowed("/shop/secret/")
    assert rules.allowed("/x")  # same length: allow wins


def test_end_anchor_and_specific_agent_group():
    text = ("User-agent: SecretPriceResearchBot\nDisallow: /*.pdf$\n\n"
            "User-agent: *\nDisallow: /\n")
    rules = parse_robots(text, AGENT_TOKEN)   # our own group applies, not the '*' group
    assert not rules.allowed("/files/price.pdf")
    assert rules.allowed("/files/price.pdf?v=2")
    assert rules.allowed("/shop/")


def test_empty_disallow_allows_everything_and_fallbacks():
    assert parse_robots("User-agent: *\nDisallow:\n", AGENT_TOKEN).allowed("/anything")
    assert RobotsRules.allow_everything().allowed("/x")        # robots.txt missing (404)
    assert not RobotsRules.deny_everything().allowed("/x")     # robots.txt unreadable (5xx)
