# Real-Estate Price Analysis — Nestly (Austin, TX), 8 Nov 2026

**Source:** live scrape of Scrapify Playground's Nestly home search
(`scrapifydatalabs.com/playground/nestly/`, 8 Nov 2026) — a practice site
built to be scraped, so these are the playground's own demo listings:
SAMPLE data, not a live market feed. 16 listings scraped, 16 listed on the
playground's own JSON feed — full census, nothing missed.

## Headline (active for-sale listings only, n=12)

| KPI | Value |
|---|---|
| Active for-sale listings | 12 of 16 scraped (2 pending, 2 for rent) |
| Total asking value (for sale) | $8,410,000 |
| Median asking price | $550,500 |
| Mean asking price | $700,833 |
| Cheapest / priciest | $175,000 / $2,150,000 |
| Median price per sqft | $323.50 |
| Mean price per sqft | $331.28 |
| Median days on market | 13 days (mean 18.6) |
| Listings with an HOA fee | 6 of 12 (median HOA $165/mo) |

## 3 findings

1. **Every listing is priced below its Nestly estimate.** 14 of 14
   priced listings (sale + pending) sit below the site's own estimate, by
   -1.93% on average (range -3.23% to -1.37%).
   *So what:* on this snapshot the estimates read like a ceiling, not a
   target — a buyer opening below asking has the estimate on their side,
   and a seller pricing at the estimate is pricing above every comparable.
2. **Price per sqft is the real spread, not price.** The cheapest home per
   sqft is Lot 42 Pioneer Trails, Austin, TX 78744 at $144.63/sqft
   (Manufactured, $175,000); the priciest is
   18 Westlake Dr, Austin, TX 78746 at $446.06/sqft
   (Single Family, $2,150,000). *So what:* headline price
   alone misranks value — the $2.15M Westlake home is also the most
   expensive per sqft, while the $175k manufactured home is the cheapest
   per sqft by a wide margin, so a per-sqft sort answers a different
   question than a price sort.
3. **Days on market splits the set in two.** Median is 13 days,
   but 18 Westlake Dr, Austin, TX 78746 has sat 55 days while
   128 Mueller Blvd, Austin, TX 78723 moved in 4 days. The two
   longest-sitting homes are the $2,150,000 Westlake listing
   (55 days) and the $895,000
   6-bedroom on 2201 E Cesar Chavez St
   (40 days) — the #1 and #3 asking prices in the
   set. *So what:* time-on-market is a negotiation
   signal a buyer can read straight off this sheet — expensive homes wait.

## By ZIP (sale only — thin counts, read as reference points)

Only ZIP 78704 has more than one active sale listing (n=3, median
$589,000);
every other ZIP is a single listing, so no ZIP median here is a market
rate — the table is a per-listing reference, and the honest area story
is the type table below. Full table: `area_price_summary.csv`.

## By property type (sale only)

| Type | n | Median price | Median $/sqft | Avg days |
|---|---|---|---|---|
| Condo | 2 | $359,000 | $410.45 | 10.5 |
| Manufactured | 1 | $175,000 | $144.63 | 8 |
| Multi Family | 1 | $895,000 | $319.64 | 40 |
| Single Family | 7 | $625,000 | $327.36 | 21.4 |
| Townhouse | 1 | $512,000 | $297.67 | 4 |

Single Family dominates the set (7 of 12 active sales) — the
type medians for Townhouse, Multi Family and Manufactured are single
listings, shown for completeness, not as type rates.

## Pending + rentals (kept out of the sale stats)

- Pending (under contract, priced): 4110 Lakewood Cove, Austin, TX 78731 ($875,000), 4702 Duval St, Austin, TX 78751 ($535,000)
- For rent: 2100 Domain Dr #221, Austin, TX 78758 ($2,450/mo), 1204 E 12th St, Austin, TX 78702 ($3,200/mo)

## Data-quality notes

- Lot-size outlier: nl-1015 reports a 4,278,744-sqft lot
  (median lot 7,622 sqft) — kept exactly as scraped, flagged
  here, never silently edited. Median lot is reported instead of the mean.
- Condos report no lot size (2 listings) — `lot_sqft` is NULL, not zero.
- Rentals report no annual tax and no Nestly estimate — NULL, not zero.
- HOA $0 means "no HOA" (the site prints "HOA None"); 7 of 16 listings
  carry a monthly HOA fee.
- All 16 scraped listings match the playground's own JSON feed count (16).

## How to re-run it

1. `python3 src/scrape_nestly.py` — re-scrapes the search + detail pages.
2. `python3 src/build_sqlite.py` — rebuilds `data/processed/listings.db`.
3. `python3 src/analyze.py` — regenerates this report + the two CSVs.
4. `python3 src/checks.py` — data-quality checks as code.
