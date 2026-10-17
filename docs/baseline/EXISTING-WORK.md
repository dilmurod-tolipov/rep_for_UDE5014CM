# Existing work disclosure (pre-approval baseline)

This file records work that existed **before** Module Leader approval, as required
in the approval feedback (point 7). Nothing in `storefront/` at tag `baseline-demo`
is claimed as checkpoint development.

## What it is

A React + Vite + Tailwind demonstration storefront and admin panel for Secret
(flowers, Secret Berries, Green Mood plants). It stores everything in the
browser's `localStorage`; it has no server and no database. Product prices in
`src/data/products.ts` are placeholders, not Secret's real prices. Orders and
payments are simulated. It contains **no collected data**.

## Snapshot identity

| Item | Value |
|---|---|
| Source folder | `secret v2/site/` on the student's PC (not under version control) |
| Last file modification | 2026-09-21 18:30 (Asia/Tashkent) |
| Distributed zip | `secret-—-luxury-florals,-green-mood-&-berries.zip` |
| Zip SHA-256 | `399a19112690185cff91453fdd2e1983fdfd019ba629b94c88f0f9fb46752559` |
| Per-file hashes | [`storefront-sha256-manifest.txt`](storefront-sha256-manifest.txt) (100 files, `node_modules/` and `dist/` excluded) |
| Git tag | `baseline-demo` (first commit of this repository) |

## How it was made

The demo was scaffolded with **Google AI Studio (Gemini)** and then edited by the
student. Traces: `metadata.json` and the `.env.example` template. The code does
not call the Gemini API and needs no API key.

## Previously submitted for assessment?

<!-- CONFIRM: student must confirm this statement is true before Checkpoint 1 -->
No. The demo has not been submitted for assessment in this or any other module.

## Reused components

Everything in `storefront/` at `baseline-demo` is reused, specifically:

- Storefront UI: `App.tsx`, `Navbar`, `ParallaxHero`, `CatalogSections`, `ProductCard`,
  `ProductDetailModal`, `BouquetBuilder`, `CartDrawer`, `CheckoutModal`, `PaymentModal`,
  `Footer`, `LanguageSelector`, `Preloader`, `PetalsCanvas`, `SecretLogo`, `SafeImage`,
  `ErrorBoundary`, `DemoNotice`
- Admin UI: `admin/AdminApp`, `admin/Products`, `admin/Orders`, `admin/Dashboard`, `admin/ui`, `admin/i18n`
- Client-side data layer: `data/store.ts`, `data/useStore.ts`, `data/demoSeed.ts`, `data/products.ts`
- Translations (UZ/RU/EN), images in `public/images/`

## What counts as new work

Only changes made **after** `baseline-demo` count: the market-intelligence collector,
both SQLite databases, the pipeline, analysis, tests, dashboard/API, and any diff to
`storefront/` (for example replacing `localStorage` with calls to the `secret_shop`
API). Run `git diff baseline-demo -- storefront/` to see exactly what changed.
