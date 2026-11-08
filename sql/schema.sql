-- P12 — Real-Estate Listings Scraper: star-lite schema
-- One fact table (one row per listing) + one area dimension.
-- SQLite. Rebuild any time: python3 src/build_sqlite.py
-- The .db file is NOT uploaded to GitHub (rebuildable from the CSV).

DROP TABLE IF EXISTS fact_listings;
DROP TABLE IF EXISTS dim_area;
DROP VIEW IF EXISTS vw_area_price_summary;

CREATE TABLE dim_area (
    zip TEXT PRIMARY KEY,
    city TEXT NOT NULL,
    listings_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE fact_listings (
    home_id TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('for_sale', 'for_rent', 'pending')),
    price_usd INTEGER NOT NULL CHECK (price_usd > 0),
    price_per_sqft_usd REAL,              -- sale listings only, computed
    beds INTEGER,
    baths REAL,
    sqft INTEGER CHECK (sqft IS NULL OR sqft > 0),
    property_type TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    zip TEXT NOT NULL REFERENCES dim_area (zip),
    lat REAL,
    lng REAL,
    days_on_market INTEGER CHECK (days_on_market >= 0),
    hoa_monthly_usd INTEGER,
    broker TEXT,
    agent TEXT,
    description TEXT,
    features TEXT,                        -- '; '-separated
    schools TEXT,                         -- '; '-separated
    year_built INTEGER,
    lot_sqft INTEGER,
    parking TEXT,
    annual_tax_usd INTEGER,
    zestimate_usd INTEGER,
    scrape_date TEXT NOT NULL,
    source TEXT NOT NULL
);

CREATE INDEX idx_fact_zip ON fact_listings (zip);
CREATE INDEX idx_fact_type ON fact_listings (property_type);
CREATE INDEX idx_fact_status ON fact_listings (status);

-- Area price summary: sale listings only (rent is $/month, never mixed in).
CREATE VIEW vw_area_price_summary AS
SELECT
    zip,
    COUNT(*) AS sale_listings,
    ROUND(AVG(price_usd), 0) AS avg_price_usd,
    ROUND(AVG(price_per_sqft_usd), 2) AS avg_price_per_sqft_usd,
    MIN(price_usd) AS min_price_usd,
    MAX(price_usd) AS max_price_usd,
    ROUND(AVG(days_on_market), 1) AS avg_days_on_market
FROM fact_listings
WHERE status = 'for_sale'
GROUP BY zip;
