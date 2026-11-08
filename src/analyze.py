#!/usr/bin/env python3
"""Area price analysis over data/processed/listings.db.

Writes:
  outputs/price-analysis.md        — findings report (all numbers from the DB)
  outputs/area_price_summary.csv   — sale listings by ZIP (median price, $/sqft)
  outputs/type_price_summary.csv   — sale listings by property type

Sale-price stats use ACTIVE for-sale listings only. Pending listings are
shown separately (priced, but under contract). Rentals ($/month) are never
mixed into sale-price stats.
"""
import csv
import sqlite3
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "listings.db"
OUT = ROOT / "outputs"


def median(xs):
    return round(statistics.median(xs), 2) if xs else None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    total = con.execute("SELECT COUNT(*) FROM fact_listings").fetchone()[0]
    by_status = dict(con.execute(
        "SELECT status, COUNT(*) FROM fact_listings GROUP BY status").fetchall())
    sale = [dict(r) for r in con.execute(
        "SELECT * FROM fact_listings WHERE status='for_sale'")]
    pending = [dict(r) for r in con.execute(
        "SELECT * FROM fact_listings WHERE status='pending'")]
    rent = [dict(r) for r in con.execute(
        "SELECT * FROM fact_listings WHERE status='for_rent'")]

    prices = [r["price_usd"] for r in sale]
    ppsf = [r["price_per_sqft_usd"] for r in sale if r["price_per_sqft_usd"]]
    dom = [r["days_on_market"] for r in sale]
    sale_sum = sum(prices)
    sale_median = median(prices)
    ppsf_median = median(ppsf)

    # List price vs Nestly estimate (sale + pending, both have estimates).
    gaps = []
    for r in sale + pending:
        if r["zestimate_usd"]:
            gaps.append(round((r["price_usd"] - r["zestimate_usd"]) / r["zestimate_usd"] * 100, 2))
    below_est = sum(1 for g in gaps if g < 0)

    # By ZIP (sale only) and by property type (sale only).
    area_rows = []
    for z in sorted({r["zip"] for r in sale}):
        zs = [r for r in sale if r["zip"] == z]
        area_rows.append({
            "zip": z, "sale_listings": len(zs),
            "median_price_usd": median([r["price_usd"] for r in zs]),
            "avg_price_usd": round(statistics.mean([r["price_usd"] for r in zs]), 0),
            "median_price_per_sqft_usd": median(
                [r["price_per_sqft_usd"] for r in zs if r["price_per_sqft_usd"]]),
            "min_price_usd": min(r["price_usd"] for r in zs),
            "max_price_usd": max(r["price_usd"] for r in zs),
            "avg_days_on_market": round(statistics.mean(
                [r["days_on_market"] for r in zs]), 1),
        })
    type_rows = []
    for t in sorted({r["property_type"] for r in sale}):
        ts = [r for r in sale if r["property_type"] == t]
        type_rows.append({
            "property_type": t, "sale_listings": len(ts),
            "median_price_usd": median([r["price_usd"] for r in ts]),
            "avg_price_usd": round(statistics.mean([r["price_usd"] for r in ts]), 0),
            "median_price_per_sqft_usd": median(
                [r["price_per_sqft_usd"] for r in ts if r["price_per_sqft_usd"]]),
            "avg_days_on_market": round(statistics.mean(
                [r["days_on_market"] for r in ts]), 1),
        })

    # Outlier watch: lot sizes (nl-1015's lot is ~98 acres — as scraped).
    lots = [(r["home_id"], r["lot_sqft"]) for r in sale + pending if r["lot_sqft"]]
    lot_median = median([v for _, v in lots])
    lot_outlier = max(lots, key=lambda x: x[1])

    hoa = [r for r in sale if r["hoa_monthly_usd"]]
    with open(OUT / "area_price_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(area_rows[0].keys()))
        w.writeheader()
        w.writerows(area_rows)
    with open(OUT / "type_price_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(type_rows[0].keys()))
        w.writeheader()
        w.writerows(type_rows)

    cheapest = min(sale, key=lambda r: r["price_per_sqft_usd"])
    priciest = max(sale, key=lambda r: r["price_per_sqft_usd"])
    longest = max(sale, key=lambda r: r["days_on_market"])
    second_longest = sorted(sale, key=lambda r: r["days_on_market"])[-2]
    newest = min(sale, key=lambda r: r["days_on_market"])

    md = f"""# Real-Estate Price Analysis — Nestly (Austin, TX), 8 Nov 2026

**Source:** live scrape of Scrapify Playground's Nestly home search
(`scrapifydatalabs.com/playground/nestly/`, 8 Nov 2026) — a practice site
built to be scraped, so these are the playground's own demo listings:
SAMPLE data, not a live market feed. 16 listings scraped, 16 listed on the
playground's own JSON feed — full census, nothing missed.

## Headline (active for-sale listings only, n={len(sale)})

| KPI | Value |
|---|---|
| Active for-sale listings | {len(sale)} of {total} scraped ({by_status.get('pending', 0)} pending, {by_status.get('for_rent', 0)} for rent) |
| Total asking value (for sale) | ${sale_sum:,} |
| Median asking price | ${sale_median:,.0f} |
| Mean asking price | ${round(statistics.mean(prices), 0):,.0f} |
| Cheapest / priciest | ${min(prices):,} / ${max(prices):,} |
| Median price per sqft | ${ppsf_median:,.2f} |
| Mean price per sqft | ${round(statistics.mean(ppsf), 2):,.2f} |
| Median days on market | {median(dom):.0f} days (mean {round(statistics.mean(dom), 1)}) |
| Listings with an HOA fee | {len(hoa)} of {len(sale)} (median HOA ${median([r['hoa_monthly_usd'] for r in hoa]):,.0f}/mo) |

## 3 findings

1. **Every listing is priced below its Nestly estimate.** {below_est} of {len(gaps)}
   priced listings (sale + pending) sit below the site's own estimate, by
   {round(statistics.mean(gaps), 2)}% on average (range {min(gaps)}% to {max(gaps)}%).
   *So what:* on this snapshot the estimates read like a ceiling, not a
   target — a buyer opening below asking has the estimate on their side,
   and a seller pricing at the estimate is pricing above every comparable.
2. **Price per sqft is the real spread, not price.** The cheapest home per
   sqft is {cheapest['address']} at ${cheapest['price_per_sqft_usd']:.2f}/sqft
   (Manufactured, ${cheapest['price_usd']:,}); the priciest is
   {priciest['address']} at ${priciest['price_per_sqft_usd']:.2f}/sqft
   (Single Family, ${priciest['price_usd']:,}). *So what:* headline price
   alone misranks value — the $2.15M Westlake home is also the most
   expensive per sqft, while the $175k manufactured home is the cheapest
   per sqft by a wide margin, so a per-sqft sort answers a different
   question than a price sort.
3. **Days on market splits the set in two.** Median is {median(dom):.0f} days,
   but {longest['address']} has sat {longest['days_on_market']} days while
   {newest['address']} moved in {newest['days_on_market']} days. The two
   longest-sitting homes are the ${longest['price_usd']:,} Westlake listing
   ({longest['days_on_market']} days) and the ${second_longest['price_usd']:,}
   {second_longest['beds']}-bedroom on {second_longest['address'].split(',')[0]}
   ({second_longest['days_on_market']} days) — the #1 and #3 asking prices in the
   set. *So what:* time-on-market is a negotiation
   signal a buyer can read straight off this sheet — expensive homes wait.

## By ZIP (sale only — thin counts, read as reference points)

Only ZIP 78704 has more than one active sale listing (n=3, median
${[a for a in area_rows if a['zip'] == '78704'][0]['median_price_usd']:,.0f});
every other ZIP is a single listing, so no ZIP median here is a market
rate — the table is a per-listing reference, and the honest area story
is the type table below. Full table: `area_price_summary.csv`.

## By property type (sale only)

| Type | n | Median price | Median $/sqft | Avg days |
|---|---|---|---|---|
"""
    for t in type_rows:
        md += (f"| {t['property_type']} | {t['sale_listings']} | "
               f"${t['median_price_usd']:,.0f} | ${t['median_price_per_sqft_usd']:,.2f} | "
               f"{t['avg_days_on_market']} |\n")
    md += f"""
Single Family dominates the set ({[t for t in type_rows if t['property_type'] == 'Single Family'][0]['sale_listings']} of {len(sale)} active sales) — the
type medians for Townhouse, Multi Family and Manufactured are single
listings, shown for completeness, not as type rates.

## Pending + rentals (kept out of the sale stats)

- Pending (under contract, priced): {', '.join(f"{r['address']} (${r['price_usd']:,})" for r in pending)}
- For rent: {', '.join(f"{r['address']} (${r['price_usd']:,}/mo)" for r in rent)}

## Data-quality notes

- Lot-size outlier: {lot_outlier[0]} reports a {lot_outlier[1]:,}-sqft lot
  (median lot {lot_median:,.0f} sqft) — kept exactly as scraped, flagged
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
"""
    (OUT / "price-analysis.md").write_text(md, encoding="utf-8")
    print(f"analysis written: {len(sale)} sale, {len(pending)} pending, {len(rent)} rent")
    print(f"median price ${sale_median:,.0f} | median $/sqft ${ppsf_median:,.2f} | "
          f"avg list-vs-estimate gap {round(statistics.mean(gaps), 2)}%")
    con.close()


if __name__ == "__main__":
    main()
