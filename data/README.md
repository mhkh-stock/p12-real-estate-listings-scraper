# Data dictionary — P12 Real-Estate Listings Scraper

## Source (read this first)

**Live scrape, 8 Nov 2026, of Scrapify Playground's Nestly home search**
(`https://scrapifydatalabs.com/playground/nestly/`) — a practice site
**built to be scraped** ("You are invited to scrape every page here").
The 16 listings are the playground's own demo homes in Austin, TX, so
this dataset is SAMPLE data by nature: it proves the scraper and the
analysis, it is not a live market feed and no real buyer or seller is
involved. Re-run `python3 src/scrape_nestly.py` to re-scrape (polite:
0.5 s between requests, named User-Agent). Scrape completeness was
cross-checked against the playground's own JSON feed
(`/data/nestly-homes.json`): 16 scraped = 16 listed.

## Files

| File | What it is |
|---|---|
| `raw/listings_SAMPLE.csv` | One row per listing (16 rows): search-card fields + detail-page enrichment |
| `raw/listings.json` | Same rows + scrape metadata (date, source, feed cross-check count) |
| `raw/html/` | Raw HTML snapshots of the search page + all 16 detail pages (local only, not uploaded — provenance for the scrape) |
| `processed/listings.db` | SQLite star-lite load (`sql/schema.sql`); rebuild with `python3 src/build_sqlite.py`; NOT uploaded (rebuildable from the CSV) |

## Columns (`listings_SAMPLE.csv`)

| Column | Meaning | Notes |
|---|---|---|
| `home_id` | Playground listing id (`nl-1001` … `nl-1016`) | Primary key |
| `status` | `for_sale` (12) / `pending` (2) / `for_rent` (2) | Pending = under contract, priced |
| `price_usd` | Asking price; monthly rent for `for_rent` rows | Never mix rent $/mo into sale-price stats |
| `beds` / `baths` | Bedrooms / bathrooms | Baths can be .5 |
| `sqft` | Living area, sq ft | Always present |
| `property_type` | Single Family / Condo / Townhouse / Apartment / Multi Family / Manufactured | |
| `address` / `city` / `zip` | Full address; all Austin, TX, ZIPs 78701–78758 | |
| `lat` / `lng` | Map-pin coordinates from the search card | |
| `days_on_market` | Days on Nestly at scrape time | 2–55 |
| `hoa_monthly_usd` | Monthly HOA fee; **0 = no HOA** (site prints "HOA None") | Card value; cross-checked against detail page |
| `broker` / `agent` | Listing brokerage / named agent | Demo names from the playground |
| `description` | Detail-page overview sentence | |
| `features` | `; `-separated feature tags | |
| `schools` | `; `-separated nearby schools with ratings | |
| `year_built` | Year built | Present for all 16 |
| `lot_sqft` | Lot size, sq ft | NULL for condos (no lot); see outlier note |
| `parking` | Parking description | e.g. "2 car garage" |
| `annual_tax_usd` | Annual property tax | NULL for rentals |
| `zestimate_usd` | Nestly estimate | NULL for rentals |
| `hoa_detail_usd` | HOA from the detail page (audit column) | Agrees with the card wherever present |
| `detail_url` | Full detail-page URL | |
| `scrape_date` / `source` | 2026-11-08 / scrapifydatalabs.com/playground/nestly | |

## Known quirks (kept as scraped, flagged — never silently edited)

- **Lot outlier:** `nl-1015` reports a 4,278,744-sqft lot (median lot is
  7,622 sqft). Kept exactly as scraped; the analysis reports median lot,
  never mean lot.
- **Thin ZIPs:** only ZIP 78704 has more than one active sale listing
  (n=3). Other ZIP rows in the area summary are single-listing reference
  points, not market rates — the report says so.
- **Rentals have no tax and no estimate** (NULL, not zero) — the site
  does not publish them for rentals.
- **Every priced listing sits below its Nestly estimate** (14/14, avg
  −1.93%) — a finding of this snapshot, asserted in `src/checks.py`, not
  a universal claim.
