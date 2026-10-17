# ADR-003: Collect Secret's prices automatically from its public Telegram channel

- **Date:** 2026-10-17 (Week 6)
- **Status:** Accepted. Supersedes the *manual entry* part of ADR-002 (its honesty rules still apply).
- **Related:** ADR-002; approval feedback point 2; issue #7

## Context

ADR-002 planned to read Secret's prices from its public pages and type them into an admin form.
The student then identified where Secret publishes them: the public Telegram channel
**https://t.me/secret_flowersuz** ("Secret Flowers"). Reconnaissance on 2026-10-17 showed:

- Every product post has a labelled price, e.g. `Стоимость: 2.890.000`, a permanent post link and a timestamp.
- About 10 posts a day; 14 days of posts = 135 posts, 123 with a price.
- The web preview `https://t.me/s/<channel>` is public, needs no login, and `t.me/robots.txt` returns 404 (no restrictions).
  Older posts are reached through the page's `<link rel="prev" href="?before=<id>">`.

## Decision

Secret's prices are collected **automatically by our own collector** (`priceintel/secret/`), with the same
controls as the competitor scraper (robots check, >= 5 s between requests, identified user agent, retries,
every request logged with HTTP status and SHA-256):

1. `collect-secret` reads the channel preview newest-first until posts are older than `--days` (default 14).
2. Each post becomes a `secret_shop.products` row (post URL = natural key); every run that still sees the
   post adds a dated `product_price_history` row. Bouquets on sale for days are observed again in every run.
3. Only a **labelled** price is accepted (`Стоимость:`, `Цена:`, `Все по:`, `Narxi:`). Posts with no price
   or with several different prices go to `rejected_posts` with the rule; nothing is guessed.
4. Contact lines (phone numbers, @handles, links) are removed before the caption is stored.
5. `snapshot-secret` copies current prices into `market_intel` as `own_system` rows on the own shop, only from
   runs with the same purpose (dev prices can never enter an assessed snapshot). `check-integrity` verifies
   every own-shop listing in market_intel has a matching secret_shop product (no cross-database orphans).

The manual admin form from ADR-002 is kept as a later fallback for corrections (`method = 'manual_form'`).

## Why this is better than manual entry

| | Manual entry (ADR-002) | Channel collector (ADR-003) |
|---|---|---|
| Collected by our own system | form only | fully automated, scheduled |
| Provenance | source URL typed by hand | HTTP request, content hash, post link, post time |
| Volume | limited by typing time | every post, every run |
| Error risk | typing mistakes | rule-based extraction, tested; ambiguous posts quarantined |

## Consequences and open issue

- **Matching attributes are thin.** In 123 captions a flower type is named in about 30 and a stem count in none,
  and photos are not analysed. The v2 matching rule (type + packaging + stem-count band) therefore cannot be
  applied to most Secret posts. This affects the hypothesis design and is raised with the student and the
  Module Leader before Checkpoint 3 (see the reply to the v2 proposal).
- Secret's prices are premium (685,000 to 6,350,000 UZS, mean about 2.48M in the first dev run), so like-for-like
  matching matters more, not less.
- Owner's consent to read the channel is to be recorded in `config/secret_sources.json` (`consent_note`).
