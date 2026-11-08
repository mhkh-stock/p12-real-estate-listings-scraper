#!/usr/bin/env python3
"""Load data/raw/listings_SAMPLE.csv into data/processed/listings.db.

Rebuildable any time (the .db is NOT uploaded to GitHub):
    python3 src/build_sqlite.py
"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "processed" / "listings.db"
CSV = ROOT / "data" / "raw" / "listings_SAMPLE.csv"
SCHEMA = ROOT / "sql" / "schema.sql"


def _int(v):
    return int(v) if v not in (None, "") else None


def _float(v):
    return float(v) if v not in (None, "") else None


def main():
    DB.parent.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    areas = {}
    for r in rows:
        areas.setdefault(r["zip"], r["city"])
    con.executemany(
        "INSERT INTO dim_area (zip, city, listings_count) VALUES (?, ?, ?)",
        [(z, c, sum(1 for r in rows if r["zip"] == z)) for z, c in areas.items()],
    )
    for r in rows:
        price = _int(r["price_usd"])
        sqft = _int(r["sqft"])
        ppsf = round(price / sqft, 2) if (price and sqft and r["status"] == "for_sale") else None
        con.execute(
            """INSERT INTO fact_listings
            (home_id, status, price_usd, price_per_sqft_usd, beds, baths, sqft,
             property_type, address, city, zip, lat, lng, days_on_market,
             hoa_monthly_usd, broker, agent, description, features, schools,
             year_built, lot_sqft, parking, annual_tax_usd, zestimate_usd,
             scrape_date, source)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (r["home_id"], r["status"], price, ppsf, _int(r["beds"]),
             _float(r["baths"]), sqft, r["property_type"], r["address"],
             r["city"], r["zip"], _float(r["lat"]), _float(r["lng"]),
             _int(r["days_on_market"]), _int(r["hoa_monthly_usd"]),
             r["broker"] or None, r["agent"] or None,
             r["description"] or None, r["features"] or None,
             r["schools"] or None, _int(r["year_built"]), _int(r["lot_sqft"]),
             r["parking"] or None, _int(r["annual_tax_usd"]),
             _int(r["zestimate_usd"]), r["scrape_date"], r["source"]),
        )
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM fact_listings").fetchone()[0]
    print(f"loaded {n} listings into {DB}")
    con.close()


if __name__ == "__main__":
    main()
