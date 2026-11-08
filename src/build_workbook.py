#!/usr/bin/env python3
"""Build outputs/real_estate_price_analysis_SAMPLE.xlsx.

Sheets:
  Dashboard      — KPIs (live formulas over Listings) + by-type table + chart
  Listings       — the 16 scraped listings (Excel Table; $/sqft and
                   list-vs-estimate are formulas, not typed values)
  Area Analysis  — sale listings by ZIP (values from src/analyze.py)
  Type Analysis  — sale listings by property type (values from src/analyze.py)

Medians use AGGREGATE(16,6,range/(condition),0.5) — a normal formula,
no array entry needed; verified to calculate in LibreOffice.
openpyxl writes formulas, not cached values: open in Excel / Sheets /
LibreOffice to see the numbers.
"""
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "raw" / "listings_SAMPLE.csv"
AREA = ROOT / "outputs" / "area_price_summary.csv"
TYPES = ROOT / "outputs" / "type_price_summary.csv"
OUT = ROOT / "outputs" / "real_estate_price_analysis_SAMPLE.xlsx"

TITLE_FONT = Font(name="Calibri", size=14, bold=True)
HDR_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
HDR_FILL = PatternFill("solid", fgColor="1F4E79")
KPI_FONT = Font(name="Calibri", size=11, bold=True)
MONEY = '#,##0'
MONEY2 = '#,##0.00'
PCT = '0.00%'
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = HDR_FONT
        cell.fill = HDR_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    area = list(csv.DictReader(open(AREA, encoding="utf-8")))
    types = list(csv.DictReader(open(TYPES, encoding="utf-8")))
    n = len(rows)
    last = n + 1  # last data row on Listings (header row 1)

    wb = Workbook()
    # ---------------------------------------------------------------- Listings
    ws = wb.active
    ws.title = "Listings"
    cols = ["home_id", "status", "price_usd", "beds", "baths", "sqft",
            "property_type", "address", "zip", "days_on_market",
            "hoa_monthly_usd", "broker", "agent", "year_built", "lot_sqft",
            "annual_tax_usd", "zestimate_usd", "price_per_sqft_usd",
            "list_vs_estimate_pct", "detail_url"]
    headers = ["Home ID", "Status", "Price (USD)", "Beds", "Baths", "Sqft",
               "Type", "Address", "ZIP", "Days on market", "HOA $/mo",
               "Broker", "Agent", "Year built", "Lot sqft", "Annual tax (USD)",
               "Nestly estimate (USD)", "$ / sqft", "List vs estimate",
               "Detail URL"]
    for j, h in enumerate(headers, 1):
        ws.cell(row=1, column=j, value=h)
    style_header(ws, 1, len(cols))
    for i, r in enumerate(rows, 2):
        for j, k in enumerate(cols, 1):
            if k == "price_per_sqft_usd":
                ws.cell(row=i, column=j).value = (
                    f'=IF(AND(B{i}="for_sale",F{i}<>""),C{i}/F{i},"")')
            elif k == "list_vs_estimate_pct":
                ws.cell(row=i, column=j).value = (
                    f'=IF(AND(B{i}<>"for_rent",Q{i}<>""),(C{i}-Q{i})/Q{i},"")')
            else:
                v = r.get(k)
                if k in ("price_usd", "beds", "sqft", "days_on_market",
                         "hoa_monthly_usd", "year_built", "lot_sqft",
                         "annual_tax_usd", "zestimate_usd"):
                    v = int(v) if v not in (None, "") else None
                elif k == "baths":
                    v = float(v) if v not in (None, "") else None
                ws.cell(row=i, column=j, value=v)
        for j in range(1, len(cols) + 1):
            ws.cell(row=i, column=j).border = BORDER
    for j, fmt in [(3, MONEY), (6, MONEY), (11, MONEY), (15, MONEY),
                   (16, MONEY), (17, MONEY), (18, MONEY2), (19, PCT)]:
        for i in range(2, last + 1):
            ws.cell(row=i, column=j).number_format = fmt
    tab = Table(displayName="Listings", ref=f"A1:{get_column_letter(len(cols))}{last}")
    tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium9", showRowStripes=True)
    ws.add_table(tab)
    widths = [10, 10, 13, 6, 7, 8, 15, 34, 8, 10, 10, 20, 14, 10, 11, 13, 15, 10, 12, 52]
    for j, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = "A2"
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    # --------------------------------------------------------------- Dashboard
    d = wb.create_sheet("Dashboard")
    d["A1"] = "Real-Estate Price Analysis — Nestly, Austin TX"
    d["A1"].font = TITLE_FONT
    d["A2"] = ("SAMPLE — demo listings scraped 8 Nov 2026 from Scrapify Playground's "
               "Nestly home search (a practice site built to be scraped). "
               "Sale-price KPIs cover ACTIVE for-sale listings only; "
               "pending and rentals are counted separately, never mixed in.")
    d["A2"].font = Font(name="Calibri", size=10, italic=True, color="595959")
    d["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    d.merge_cells("A2:F2")
    d.row_dimensions[2].height = 30

    kpis = [
        ("Total listings scraped", f"=COUNTA(Listings!A2:A{last})", "0"),
        ("For sale (active)", f'=COUNTIF(Listings!B2:B{last},"for_sale")', "0"),
        ("Pending (under contract)", f'=COUNTIF(Listings!B2:B{last},"pending")', "0"),
        ("For rent", f'=COUNTIF(Listings!B2:B{last},"for_rent")', "0"),
        ("Total asking value (for sale)", f'=SUMIF(Listings!B2:B{last},"for_sale",Listings!C2:C{last})', '"$"#,##0'),
        ("Median asking price", f'=_xlfn.AGGREGATE(16,6,Listings!C2:C{last}/(Listings!B2:B{last}="for_sale"),0.5)', '"$"#,##0'),
        ("Mean asking price", f'=AVERAGEIF(Listings!B2:B{last},"for_sale",Listings!C2:C{last})', '"$"#,##0'),
        ("Cheapest / priciest (for sale)", None, None),  # two formulas, one row
        ("Median $ / sqft", f'=_xlfn.AGGREGATE(16,6,Listings!R2:R{last}/(Listings!B2:B{last}="for_sale"),0.5)', '"$"#,##0.00'),
        ("Median days on market", f'=_xlfn.AGGREGATE(16,6,Listings!J2:J{last}/(Listings!B2:B{last}="for_sale"),0.5)', "0"),
        ("Avg list vs Nestly estimate", f'=AVERAGE(Listings!S2:S{last})', PCT),
        ("Listings with an HOA fee", f'=COUNTIFS(Listings!B2:B{last},"for_sale",Listings!K2:K{last},">0")', "0"),
    ]
    d["A4"] = "KPI"
    d["B4"] = "Value"
    style_header(d, 4, 2)
    r = 5
    for label, formula, fmt in kpis:
        d.cell(row=r, column=1, value=label).font = KPI_FONT
        if label.startswith("Cheapest"):
            d.cell(row=r, column=2).value = (
                f'=_xlfn.MINIFS(Listings!C2:C{last},Listings!B2:B{last},"for_sale")')
            d.cell(row=r, column=2).number_format = '"$"#,##0'
            d.cell(row=r, column=3).value = (
                f'=_xlfn.MAXIFS(Listings!C2:C{last},Listings!B2:B{last},"for_sale")')
            d.cell(row=r, column=3).number_format = '"$"#,##0'
            d.cell(row=r, column=1, value="Cheapest / priciest (for sale)").font = KPI_FONT
            d["C4"] = "…to"
            d["C4"].font = HDR_FONT
            d["C4"].fill = HDR_FILL
        elif formula:
            d.cell(row=r, column=2).value = formula
            d.cell(row=r, column=2).number_format = fmt
        r += 1
    d.column_dimensions["A"].width = 34
    d.column_dimensions["B"].width = 18
    d.column_dimensions["C"].width = 18

    tr = r + 1
    d.cell(row=tr, column=1, value="By property type (for sale only — live formulas)").font = TITLE_FONT
    tr += 1
    for j, h in enumerate(["Type", "n", "Mean price", "Median $ / sqft", "Avg days"], 1):
        d.cell(row=tr, column=j, value=h)
    style_header(d, tr, 5)
    tr += 1
    type_start = tr
    for t in sorted({x["property_type"] for x in rows if x["status"] == "for_sale"}):
        d.cell(row=tr, column=1, value=t)
        d.cell(row=tr, column=2).value = f'=COUNTIFS(Listings!B2:B{last},"for_sale",Listings!G2:G{last},A{tr})'
        d.cell(row=tr, column=3).value = f'=AVERAGEIFS(Listings!C2:C{last},Listings!B2:B{last},"for_sale",Listings!G2:G{last},A{tr})'
        d.cell(row=tr, column=3).number_format = '"$"#,##0'
        d.cell(row=tr, column=4).value = (
            f'=_xlfn.AGGREGATE(16,6,Listings!R2:R{last}/((Listings!B2:B{last}="for_sale")*(Listings!G2:G{last}=A{tr})),0.5)')
        d.cell(row=tr, column=4).number_format = '"$"#,##0.00'
        d.cell(row=tr, column=5).value = f'=AVERAGEIFS(Listings!J2:J{last},Listings!B2:B{last},"for_sale",Listings!G2:G{last},A{tr})'
        d.cell(row=tr, column=5).number_format = '0.0'
        tr += 1
    type_end = tr - 1
    d.column_dimensions["D"].width = 16
    d.column_dimensions["E"].width = 12

    chart = BarChart()
    chart.type = "col"
    chart.title = "Mean asking price by property type (for sale)"
    chart.y_axis.title = "USD"
    chart.x_axis.title = "Property type"
    chart.height = 7.5
    chart.width = 15
    chart.shape = 4
    data = Reference(d, min_col=3, min_row=type_start - 1, max_row=type_end)
    cats = Reference(d, min_col=1, min_row=type_start, max_row=type_end)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.dataLabels = None
    d.add_chart(chart, f"A{tr + 1}")
    d.cell(row=tr + 1, column=1).value = ""  # anchor row for the chart

    # --------------------------------------------------------- Analysis sheets
    for sheet, path, note in [
        ("Area Analysis", AREA,
         "Sale listings by ZIP — values computed by src/analyze.py from the SQLite DB. "
         "Only ZIP 78704 has n>1; other rows are single-listing reference points, not market rates."),
        ("Type Analysis", TYPES,
         "Sale listings by property type — values computed by src/analyze.py from the SQLite DB. "
         "Single-listing types are shown for completeness, not as type rates."),
    ]:
        w = wb.create_sheet(sheet)
        rows2 = list(csv.DictReader(open(path, encoding="utf-8")))
        w["A1"] = note
        w["A1"].font = Font(name="Calibri", size=10, italic=True, color="595959")
        w["A1"].alignment = Alignment(wrap_text=True, vertical="top")
        w.merge_cells(f"A1:{get_column_letter(len(rows2[0]))}1")
        w.row_dimensions[1].height = 30
        for j, h in enumerate(rows2[0].keys(), 1):
            w.cell(row=2, column=j, value=h.replace("_", " ").title())
        style_header(w, 2, len(rows2[0]))
        for i, r in enumerate(rows2, 3):
            for j, k in enumerate(r.keys(), 1):
                v = r[k]
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    pass
                w.cell(row=i, column=j, value=v)
        for j, key in enumerate(rows2[0].keys(), 1):
            if "price" in key:
                for i in range(3, 3 + len(rows2)):
                    w.cell(row=i, column=j).number_format = '"$"#,##0.00' if "sqft" in key else '"$"#,##0'
            w.column_dimensions[get_column_letter(j)].width = 22

    wb.active = wb["Dashboard"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
