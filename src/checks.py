#!/usr/bin/env python3
"""Data-quality checks as code for P12 (run: python3 src/checks.py).

Every check recomputes from the CSV / DB independently — nothing trusts
a number typed in the README. Exit code 0 = all pass.
"""
import csv
import json
import sqlite3
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "raw" / "listings_SAMPLE.csv"
JSON = ROOT / "data" / "raw" / "listings.json"
DB = ROOT / "data" / "processed" / "listings.db"
AREA = ROOT / "outputs" / "area_price_summary.csv"
TYPES = ROOT / "outputs" / "type_price_summary.csv"
XLSX = ROOT / "outputs" / "real_estate_price_analysis_SAMPLE.xlsx"

passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  {detail}")


def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    meta = json.loads(JSON.read_text(encoding="utf-8"))
    sale = [r for r in rows if r["status"] == "for_sale"]
    pending = [r for r in rows if r["status"] == "pending"]
    rent = [r for r in rows if r["status"] == "for_rent"]

    print("== scrape completeness ==")
    check("16 listings scraped", len(rows) == 16, f"got {len(rows)}")
    check("scrape count matches playground JSON feed",
          meta["json_feed_count"] == len(rows) == 16,
          f"feed={meta['json_feed_count']}")
    check("home_id unique", len({r["home_id"] for r in rows}) == 16)
    check("home_ids are nl-1001..nl-1016",
          {r["home_id"] for r in rows} == {f"nl-{i}" for i in range(1001, 1017)})

    print("== status split ==")
    check("12 for sale", len(sale) == 12, f"got {len(sale)}")
    check("2 pending", len(pending) == 2, f"got {len(pending)}")
    check("2 for rent", len(rent) == 2, f"got {len(rent)}")

    print("== field sanity ==")
    check("every price > 0", all(int(r["price_usd"]) > 0 for r in rows))
    check("every sqft > 0", all(int(r["sqft"]) > 0 for r in rows))
    check("beds in 1..6", all(1 <= int(r["beds"]) <= 6 for r in rows))
    check("baths in 1..5.5", all(1 <= float(r["baths"]) <= 5.5 for r in rows))
    check("all ZIPs are Austin 787xx",
          all(r["zip"].startswith("787") for r in rows))
    check("12 distinct ZIPs", len({r["zip"] for r in rows}) == 12)
    check("lat in Austin range (30.1..30.5)",
          all(30.1 <= float(r["lat"]) <= 30.5 for r in rows))
    check("lng in Austin range (-97.9..-97.6)",
          all(-97.9 <= float(r["lng"]) <= -97.6 for r in rows))
    check("days on market 0..60",
          all(0 <= int(r["days_on_market"]) <= 60 for r in rows))
    check("every listing has address + detail URL",
          all(r["address"] and r["detail_url"].startswith("https://") for r in rows))
    check("every detail page enriched (year built present for all 16)",
          all(r["year_built"] for r in rows))
    check("rentals have no tax / no estimate (NULL, not zero)",
          all(not r["annual_tax_usd"] and not r["zestimate_usd"] for r in rent))
    check("rent prices are monthly ($2,450 + $3,200)",
          sorted(int(r["price_usd"]) for r in rent) == [2450, 3200])
    check("condos have no lot size (NULL, not zero)",
          all(not r["lot_sqft"] for r in rows if r["property_type"] == "Condo"))

    print("== HOA cross-check (card vs detail page) ==")
    mism = [r["home_id"] for r in rows
            if r["hoa_detail_usd"] and int(r["hoa_detail_usd"]) != int(r["hoa_monthly_usd"])]
    check("HOA agrees between card and detail page where both present", not mism, str(mism))
    check("HOA $0 means 'no HOA' on 9 listings",
          sum(1 for r in rows if int(r["hoa_monthly_usd"]) == 0) == 9)

    print("== headline numbers (recomputed from the CSV) ==")
    prices = sorted(int(r["price_usd"]) for r in sale)
    check("sale total asking value $8,410,000", sum(prices) == 8_410_000, f"${sum(prices):,}")
    check("sale median price $550,500", statistics.median(prices) == 550_500)
    ppsf = sorted(round(int(r["price_usd"]) / int(r["sqft"]), 2) for r in sale)
    check("sale median $/sqft $323.50", statistics.median(ppsf) == 323.50,
          f"${statistics.median(ppsf)}")
    check("sale median days on market 13",
          statistics.median([int(r["days_on_market"]) for r in sale]) == 13)
    gaps = [(int(r["price_usd"]) - int(r["zestimate_usd"])) / int(r["zestimate_usd"]) * 100
            for r in sale + pending if r["zestimate_usd"]]
    check("all 14 priced listings sit BELOW their Nestly estimate",
          len(gaps) == 14 and all(g < 0 for g in gaps),
          f"{sum(1 for g in gaps if g < 0)}/14 below")
    check("avg list-vs-estimate gap is negative (about -1.9%)",
          -2.5 < statistics.mean(gaps) < -1.0, f"{statistics.mean(gaps):.2f}%")
    lots = [(r["home_id"], int(r["lot_sqft"])) for r in rows if r["lot_sqft"]]
    check("lot outlier nl-1015 kept as scraped (4,278,744 sqft)",
          dict(lots).get("nl-1015") == 4_278_744)

    print("== SQLite load ==")
    con = sqlite3.connect(DB)
    check("DB holds 16 listings",
          con.execute("SELECT COUNT(*) FROM fact_listings").fetchone()[0] == 16)
    check("DB sale total reconciles to CSV",
          con.execute("SELECT SUM(price_usd) FROM fact_listings WHERE status='for_sale'"
                      ).fetchone()[0] == 8_410_000)
    check("area view has 10 ZIPs (sale only)",
          con.execute("SELECT COUNT(*) FROM vw_area_price_summary").fetchone()[0] == 10)
    check("DB median price per sqft reconciles ($323.50)",
          abs(con.execute(
              "SELECT AVG(price_per_sqft_usd) FROM (SELECT price_per_sqft_usd FROM "
              "fact_listings WHERE status='for_sale' ORDER BY price_per_sqft_usd "
              "LIMIT 2 OFFSET 5)").fetchone()[0] - 323.50) < 0.01)
    con.close()

    print("== analysis outputs ==")
    area = list(csv.DictReader(open(AREA, encoding="utf-8")))
    types = list(csv.DictReader(open(TYPES, encoding="utf-8")))
    check("area summary has 10 ZIP rows", len(area) == 10, f"got {len(area)}")
    check("ZIP 78704 is the only multi-listing ZIP (n=3)",
          [a for a in area if a["zip"] == "78704"][0]["sale_listings"] == "3" and
          all(a["sale_listings"] == "1" for a in area if a["zip"] != "78704"))
    check("type summary has 5 types", len(types) == 5, f"got {len(types)}")
    check("Single Family dominates (7 of 12 sales)",
          [t for t in types if t["property_type"] == "Single Family"][0]["sale_listings"] == "7")

    print("== workbook ==")
    check("workbook file exists", XLSX.exists())
    if XLSX.exists():
        from openpyxl import load_workbook
        wb = load_workbook(XLSX)
        check("workbook has 4 sheets",
              wb.sheetnames == ["Listings", "Dashboard", "Area Analysis", "Type Analysis"],
              str(wb.sheetnames))
        ws = wb["Listings"]
        check("Listings sheet holds 16 rows", ws.max_row == 17, f"max_row={ws.max_row}")
        check("$/sqft column is a formula, not a typed value",
              str(ws["R2"].value).startswith("=IF("))
        check("list-vs-estimate column is a formula, not a typed value",
              str(ws["S2"].value).startswith("=IF("))
        d = wb["Dashboard"]
        formulas = [c.value for row in d.iter_rows() for c in row
                    if isinstance(c.value, str) and c.value.startswith("=")]
        check("Dashboard KPIs are live formulas (>=10)", len(formulas) >= 10,
              f"found {len(formulas)}")
        check("Dashboard has a native chart", len(d._charts) == 1)

    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
