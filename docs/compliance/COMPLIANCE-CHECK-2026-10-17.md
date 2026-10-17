# Source compliance check — 2026-10-17 (Teaching Week 6)

Done before any assessed collection, as promised in the v2 proposal.
Each site's robots.txt and published terms (user agreement / privacy policy /
public offer) were read. Requests used the user agent
`SecretPriceResearchBot/0.1 (student project UDE5014CM)`, were spaced at least
5 seconds apart, and are **dev** reconnaissance only: none of the records seen
here are part of the assessed dataset.

## Results

| Site | robots.txt (summary) | Terms read | Automated access | Decision |
|---|---|---|---|---|
| pro-buket.uz | Catalogue allowed. Disallows `/*?*` (any query string), `/all/`, `/search/`, `/c/nedorogie-cvety/`, `/c/voshititelnye-bukety/`. `Crawl-delay: 5` | `/dostavka-i-oplata/` (no user agreement published) | Not prohibited | **Use**, ≥5 s between requests, no query-string URLs, skip disallowed categories |
| uzflora.com | Disallows only `add-to-cart` URLs, WooCommerce logs/uploads, `/wp-admin/` | `/oferta/` (public offer), `/dostavka/` | Not prohibited | **Use** (prices are in the page HTML) |
| uzflowers.com | Disallows `/tilda/*`, some pages, `/catalog/2` | — | — | **Do not scrape separately**: same operator as uzflora.com (shared phone +998 90 808 34 37); Tilda store prices are not in the page HTML |
| loveflowers.uz | Disallows `/*?`, `/wp-json/`, admin paths | `/politika-konfidentsialnosti/` (user agreement), `/dostavka-i-oplata/` | Not prohibited; quoting site material requires a link to the site | **Use** as the single representative of the operator network below |
| dostavka-cvetov365.uz, dostavka-cvetov24.uz, ultraflowers.uz, loveflowers24.uz | Identical template to loveflowers.uz | Identical user-agreement text | Not prohibited | **Do not count as separate sources** (see ADR-001) |
| kamilas.uz | `Allow: /` | No terms page found | Not prohibited | **Use** (new backup replacing the network backups) |
| fiori.uz | `Disallow: /` | — | **Disallowed** | **Excluded** |
| tashkent.my-present.com | Disallows `*-flowers-*.html` product pages; blocks `Claude-SearchBot` | — | Product pages disallowed | **Excluded** (also an international relay priced in USD) |
| uz-flowers.com | Disallows `/en`, `/ru`, currency pages | — | Mostly disallowed | **Excluded** (international, priced in USD) |

## Controls applied to every assessed scrape

- robots.txt is re-read at the start of each run and any disallowed URL is skipped and logged.
- At least 5 seconds between requests to the same host; one host at a time.
- An identifying user agent with a project contact.
- Only public product data is stored: title, price, old price, availability, URL, timestamps.
  No personal data, no product images, no descriptions beyond extracted attributes.
- Source URL kept on every record, which satisfies the "link to the site when quoting" clause.
