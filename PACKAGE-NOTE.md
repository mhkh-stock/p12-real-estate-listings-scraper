# PACKAGE NOTE — P12: Real-Estate Listings Scraper + Price Analysis

**Fiverr-ready gig title:** "I will scrape real-estate listings and build
your area price analysis dashboard"

## What the buyer gets

A re-runnable pipeline, not a one-off spreadsheet: a scraper that pulls
listings (price, beds, baths, sqft, type, address, days on market, HOA,
agent + detail-page enrichment: year built, lot, tax, estimate, features,
schools), a SQLite database, an area price analysis (median price and
$/sqft by ZIP and by property type), and an Excel dashboard whose KPIs
are live formulas — change a price and the whole dashboard re-runs.
Delivered on this sample: 16 listings, 12 ZIPs, 45 data-quality checks.

## Tiers

| Tier | Price | Delivery | Includes |
|---|---|---|---|
| **Basic — $20** | $20 | 2 days | Scrape of one listings search (up to 50 listings) → clean CSV dataset + data dictionary. |
| **Standard — $65** | $65 | 4 days | Everything in Basic + SQLite database + area price analysis report (median price / $/sqft by ZIP and type, days-on-market signals, list-vs-estimate gaps) + Excel dashboard with live-formula KPIs and a native chart. |
| **Premium — $140** | $140 | 7 days | Everything in Standard + scraper set up to re-run on the buyer's schedule (weekly snapshot + price-change report, like a P4 tracker) + a second market/area in the same run + a 30-min walkthrough call on the findings. |

## What the buyer must provide

- The listings site(s) or search URL(s) for their market, and
  confirmation they have the right to scrape them (we scrape only sites
  that allow it, or the buyer's own listings — never a portal that
  forbids scraping).
- The areas / property types they care about, and whether they want
  sale, rent, or both (rent $/month is never mixed into sale-price stats).

## Notes for the seller (Hashir)

- Sample built on Scrapify Playground's Nestly search — a practice site
  built to be scraped. Never present the demo Austin listings as a real
  market report; the deliverable is the pipeline, the sample proves it.
- For a real order, confirm the source site's scraping permission in
  writing before the first fetch, and keep the 0.5 s polite delay.
- Price-change tracking (Premium) reuses the P4 snapshot-diff pattern:
  same scraper, dated snapshots, diff report.
