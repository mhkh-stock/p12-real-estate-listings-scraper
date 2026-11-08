# P12 — Real-Estate Listings Scraper + Price Analysis: 16 listings in, a priced market out

**Source:** Scrapify Playground — Nestly home search, Austin, TX ·
**Scraped:** 8 Nov 2026 · **Status: SAMPLE delivery on DEMO listings**
**Tools:** Python (requests + BeautifulSoup) · SQLite · Excel (live formulas + native chart)
**Deliverable:** `outputs/real_estate_price_analysis_SAMPLE.xlsx`
(Dashboard + Listings + Area Analysis + Type Analysis, 16 listings, 12 ZIPs)

> ⚠️ **What this is and is not.** The listings come from a live scrape
> of Scrapify Playground's Nestly search — a practice site **built to be
> scraped** ("You are invited to scrape every page here"), so these are
> the playground's own demo homes, not a live market feed and no real
> buyer or seller is involved. What is real is the pipeline: the scraper
> fetched the search page + all 16 detail pages, cross-checked the count
> against the playground's own JSON feed (16 = 16), loaded the rows into
> SQLite, and the workbook's Dashboard KPIs are live formulas over the
> Listings sheet — change a price and the medians, totals and chart
> re-run. A real client points the same scraper at their own market's
> listings and the same analysis runs on real rows.

## Business question it answers

> "What are homes actually asking in this area — by ZIP, by type, per
> square foot — and which ones have been sitting long enough to negotiate on?"

A buyer or small investor comparing listings by hand copies prices into
a spreadsheet one by one and does it again next week. This delivery
does the copying (scraper), the maths (SQLite + analysis) and the
one-page answer (workbook) in one re-runnable pipeline.

## What is inside

| File | What it does |
|---|---|
| `outputs/real_estate_price_analysis_SAMPLE.xlsx` | The deliverable: Dashboard (12 KPIs + by-type table + chart, all formulas) + Listings (16 rows, $/sqft and list-vs-estimate as formulas) + Area / Type Analysis sheets |
| `outputs/price-analysis.md` | Findings report: 3 findings with "so what", by-ZIP and by-type tables, data-quality notes |
| `outputs/area_price_summary.csv` | Sale listings by ZIP (10 ZIPs) |
| `outputs/type_price_summary.csv` | Sale listings by property type (5 types) |
| `data/raw/listings_SAMPLE.csv` | 16 scraped listings, 26 columns (search-card fields + detail-page enrichment) |
| `data/raw/listings.json` | Same rows + scrape metadata and feed cross-check |
| `data/README.md` | Data dictionary + known quirks |
| `src/scrape_nestly.py` | The scraper: search page + 16 detail pages, polite 0.5 s delay, named User-Agent |
| `src/build_sqlite.py` | Loads the CSV into `data/processed/listings.db` (star-lite schema, `sql/schema.sql`) |
| `src/analyze.py` | Area price analysis → the report + the two summary CSVs |
| `src/build_workbook.py` | Builds the workbook: 4 sheets, live formulas, native chart |
| `src/checks.py` | Data-quality checks as code — 45 checks, all passing |
| `requirements.txt` | Pinned: `requests==2.31.0`, `beautifulsoup4==4.15.0`, `openpyxl==3.1.2` (Python 3.12) |

## How it fits together

```
scrapifydatalabs.com/playground/nestly/ ──▶ src/scrape_nestly.py ──▶ data/raw/listings_SAMPLE.csv
        (search page + 16 detail pages, 0.5 s delay)                          │
                                              ┌──────────────────────────────┘
                                              ▼
                                   src/build_sqlite.py ──▶ data/processed/listings.db
                                              │                    (NOT uploaded: rebuildable)
                                              ▼
                                   src/analyze.py ──▶ outputs/price-analysis.md + 2 CSVs
                                              │
                                              ▼
                                   src/build_workbook.py ──▶ outputs/real_estate_price_analysis_SAMPLE.xlsx
                                              ▲ src/checks.py verifies all of it (45 checks)
```

## 3 key findings (from this snapshot)

1. **Every listing is priced below its Nestly estimate.** 14 of 14
   priced listings sit below the site's own estimate, by −1.93% on
   average (range −3.23% to −1.37%). *So what:* on this snapshot the
   estimates read like a ceiling, not a target — a buyer opening below
   asking has the estimate on their side.
2. **Price per sqft is the real spread, not price.** Cheapest per sqft:
   Lot 42 Pioneer Trails at $144.63/sqft (Manufactured, $175,000);
   priciest: 18 Westlake Dr at $446.06/sqft (Single Family, $2,150,000).
   *So what:* headline price alone misranks value — a per-sqft sort
   answers a different question than a price sort.
3. **Days on market splits the set in two.** Median 13 days, but the
   $2.15M Westlake home has sat 55 days and the $895,000 six-bedroom
   40 days — the #1 and #3 asking prices are the longest-sitting.
   *So what:* time-on-market is a negotiation signal a buyer can read
   straight off this sheet.

## Verified numbers

| KPI | Value |
|---|---|
| Listings scraped | 16 (search page + 16 detail pages; JSON-feed cross-check 16 = 16) |
| For sale (active) / pending / for rent | 12 / 2 / 2 |
| Total asking value (for sale) | $8,410,000 |
| Median / mean asking price | $550,500 / $700,833 |
| Cheapest / priciest (for sale) | $175,000 / $2,150,000 |
| Median / mean price per sqft | $323.50 / $331.28 |
| Median / mean days on market | 13 / 18.6 days |
| Listings with an HOA fee | 6 of 12 for sale (7 of 16 overall; median HOA $165/mo) |
| Avg list vs Nestly estimate | −1.93% (14/14 below estimate) |
| ZIPs covered | 12 (only 78704 has n>1 — see the thin-ZIP note in the report) |
| Property types | Single Family 7 · Condo 2 · Townhouse 1 · Multi Family 1 · Manufactured 1 (for sale) |
| Rentals | $2,450/mo and $3,200/mo (kept out of sale-price stats) |
| Checks | 45 passing (`python3 src/checks.py`) |

Verification: `python3 src/checks.py` (45 checks pass — scrape
completeness, field sanity, HOA card-vs-detail agreement, every
headline number recomputed from the CSV, SQLite reconciliation, and
workbook structure/formula assertions) **and** the workbook was opened
in LibreOffice, which calculated every formula: Dashboard shows 16
listings, $8,410,000 total asking value, $550,500 median price,
$323.50 median $/sqft, 13 median days — identical to the Python
recompute. (Formula note: medians use `_xlfn.AGGREGATE` / `_xlfn.MINIFS`
— the OOXML form of those functions — because plain `AGGREGATE` /
`MINIFS` do not calculate in LibreOffice; Excel reads the `_xlfn.`
form identically.)

## Limits — what this delivery does not do

- **Demo listings, one city, one day.** 16 Austin demo homes scraped
  8 Nov 2026. A real market has hundreds of listings across many ZIPs
  and moves daily — the scraper is built to re-run (pagination support
  is the obvious next step for a multi-page market; this search page
  holds all 16 on one page).
- **ZIP medians are thin.** Only ZIP 78704 has more than one active
  sale listing (n=3); every other ZIP row is a single-listing reference
  point, not a market rate. The report says so on the page, not in a
  footnote.
- **Estimates are the site's, not a valuation.** The "Nestly estimate"
  is the playground's demo figure; the −1.93% gap is a finding about
  this snapshot, not a pricing rule.
- **One lot-size outlier is kept as scraped** (nl-1015, 4,278,744 sqft
  vs a 7,622-sqft median lot) — flagged in the report and the data
  dictionary, never silently edited.
- **Open it in Excel or Google Sheets to see the numbers.** The
  workbook carries live formulas (openpyxl writes formulas, not cached
  values), so they calculate when the file is opened — a raw file reader
  that does not calculate formulas will show blanks instead of KPI values.

## How to run it (under 5 steps)

First time only: `pip install -r requirements.txt`.

1. `python3 src/scrape_nestly.py` — re-scrapes the search + detail pages.
2. `python3 src/build_sqlite.py` — rebuilds `data/processed/listings.db`.
3. `python3 src/analyze.py` — regenerates the report + summary CSVs.
4. `python3 src/build_workbook.py` — rebuilds the workbook.
5. `python3 src/checks.py` — 45 checks, all must pass.
6. Open `outputs/real_estate_price_analysis_SAMPLE.xlsx` — that is the deliverable.
7. To reuse it for a real client: point `src/scrape_nestly.py` at the
   client's market listings (same card/detail shape) and re-run steps
   1–5 — the analysis and workbook rebuild themselves from the new rows.

## Tools

- Python 3.12 · requests 2.31.0 · BeautifulSoup 4.15.0 · openpyxl 3.1.2
- SQLite (star-lite schema) · Excel / Google Sheets (the client's tool)

## Data source note

**SAMPLE data, scraped 8 Nov 2026 from Scrapify Playground**
(`scrapifydatalabs.com/playground/nestly/`), a site built and offered
for scraping practice. No real home, buyer, seller or agent is involved.
The scraper, the SQLite load, the analysis and the workbook are the
product; the numbers exist to prove them.

## Repo standard note

This paid project follows the portfolio repo standard (Master Plan
§3.2): README + data dictionary (`data/README.md`) + the deliverable
workbook + reproducible scripts + a Fiverr-ready package note
(`PACKAGE-NOTE.md`). The workbook is the deliverable a buyer opens;
the scripts are the proof it was built, not typed.
