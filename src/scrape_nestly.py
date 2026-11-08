#!/usr/bin/env python3
"""Scrape Nestly home-search listings from Scrapify Playground.

Source: https://scrapifydatalabs.com/playground/nestly/
Scrapify Playground is a site BUILT to be scraped ("You are invited to
scrape every page here", scrapifydatalabs.com) — no live shop, no ToS
conflict, no login. The listings are the playground's own demo homes
(Austin, TX), so the shipped dataset is SAMPLE data by nature: it proves
the scraper and the analysis, it is not a live market feed.

Polite by design: one search page + one detail page per listing,
0.5 s between requests, a named User-Agent, no retries hammering.
Writes data/raw/listings_SAMPLE.csv (one row per listing) and
data/raw/listings.json (same rows, plus scrape metadata).
"""
import csv
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://scrapifydatalabs.com"
SEARCH_URL = BASE + "/playground/nestly/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) hasho-portfolio-scraper/1.0 "
        "(learning project; polite 0.5s delay; scrapifydatalabs.com invites scraping)"
    )
}
DELAY_S = 0.5
SCRAPE_DATE = "2026-11-08"

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW_HTML = RAW / "html"


def _num(text):
    """'1,680' -> 1680, '$9,850' -> 9850, '2.5' -> 2.5, None-safe."""
    if text is None:
        return None
    t = re.sub(r"[^0-9.]", "", str(text))
    if t == "" or t == ".":
        return None
    return float(t) if "." in t else int(t)


def _int_or_none(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _float_or_none(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_search_page(html):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("article.nl-card")
    rows = []
    for card in cards:
        d = card.attrs
        price_p = card.select_one(".nl-price")
        facts = card.select_one(".nl-facts")
        addr_a = card.select_one(".nl-addr a")
        meta = card.select_one(".nl-meta")
        broker = card.select_one(".nl-broker")
        hoa = None
        if meta:
            m = re.search(r"HOA \$([\d,]+)/mo", meta.get_text(" ", strip=True))
            hoa = int(m.group(1).replace(",", "")) if m else None
        rows.append({
            "home_id": d.get("data-home-id"),
            "status": d.get("data-status"),
            "price_usd": _int_or_none(d.get("data-price")),
            "beds": _int_or_none(d.get("data-beds")),
            "baths": _float_or_none(d.get("data-baths")),
            "sqft": _int_or_none(d.get("data-sqft")),
            "property_type": d.get("data-type"),
            "address": addr_a.get_text(" ", strip=True) if addr_a else None,
            "city": d.get("data-city"),
            "zip": d.get("data-zip"),
            "lat": _float_or_none(d.get("data-lat")),
            "lng": _float_or_none(d.get("data-lng")),
            "days_on_market": _int_or_none(d.get("data-days")),
            "hoa_monthly_usd": hoa if hoa is not None else _int_or_none(d.get("data-hoa")),
            "broker": broker.get("data-broker") if broker else None,
            "agent": broker.get("data-agent") if broker else None,
            "detail_url": BASE + addr_a["href"] if addr_a else None,
        })
    return rows


def parse_detail_page(html):
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("#home-detail")
    if root is None:
        return {}
    out = {}
    desc = soup.select_one("#home-description")
    out["description"] = desc.get_text(" ", strip=True) if desc else None
    feats = [t.get("data-feature") for t in soup.select("#home-features .nl-tag")]
    out["features"] = "; ".join(feats) if feats else None
    schools = []
    for li in soup.select("#home-schools li"):
        schools.append(li.get_text(" ", strip=True))
    out["schools"] = "; ".join(schools) if schools else None
    # Facts & features panel: label/value pairs in plain text lines.
    text = root.get_text("\n", strip=True)
    for label, key, kind in [
        ("Year built", "year_built", "int"),
        ("Lot", "lot_sqft", "num"),
        ("Parking", "parking", "str"),
        ("Annual tax", "annual_tax_usd", "num"),
    ]:
        m = re.search(re.escape(label) + r"\s*\n?\s*([^\n]+)", text)
        if m:
            v = m.group(1).strip()
            out[key] = _num(v) if kind in ("int", "num") else v
    zest = soup.select_one("#home-zestimate")
    out["zestimate_usd"] = _num(zest.get_text()) if zest else None
    # HOA also appears on detail pages ("HOA $385/mo" or "HOA None")
    m = re.search(r"HOA\s+\$([\d,]+)/mo", text)
    out["hoa_detail_usd"] = int(m.group(1).replace(",", "")) if m else None
    return out


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    RAW_HTML.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(HEADERS)

    r = session.get(SEARCH_URL, timeout=30)
    r.raise_for_status()
    (RAW_HTML / f"nestly_search_{SCRAPE_DATE}.html").write_text(r.text, encoding="utf-8")
    rows = parse_search_page(r.text)
    print(f"search page: {len(rows)} listings")

    for row in rows:
        time.sleep(DELAY_S)
        d = session.get(row["detail_url"], timeout=30)
        d.raise_for_status()
        (RAW_HTML / f"nestly_{row['home_id']}_{SCRAPE_DATE}.html").write_text(
            d.text, encoding="utf-8")
        row.update(parse_detail_page(d.text))
        row["scrape_date"] = SCRAPE_DATE
        row["source"] = "scrapifydatalabs.com/playground/nestly"
    print(f"detail pages: {len(rows)} fetched")

    # Cross-check against the playground's own JSON feed (count only).
    try:
        j = session.get(BASE + "/data/nestly-homes.json", timeout=30)
        feed = j.json()
        feed_n = len(feed if isinstance(feed, list) else feed.get("homes", []))
        print(f"JSON feed cross-check: {feed_n} homes listed")
    except Exception as e:  # noqa: BLE001 - feed is a bonus check, never fatal
        feed_n = None
        print(f"JSON feed cross-check unavailable: {e}")

    fields = ["home_id", "status", "price_usd", "beds", "baths", "sqft",
              "property_type", "address", "city", "zip", "lat", "lng",
              "days_on_market", "hoa_monthly_usd", "broker", "agent",
              "description", "features", "schools", "year_built",
              "lot_sqft", "parking", "annual_tax_usd", "zestimate_usd",
              "hoa_detail_usd", "detail_url", "scrape_date", "source"]
    csv_path = RAW / "listings_SAMPLE.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k) for k in fields})
    (RAW / "listings.json").write_text(json.dumps(
        {"scrape_date": SCRAPE_DATE, "source": SEARCH_URL,
         "listings_count": len(rows), "json_feed_count": feed_n,
         "listings": rows}, indent=2), encoding="utf-8")
    print(f"wrote {csv_path} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
