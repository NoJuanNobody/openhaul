#!/usr/bin/env python3
"""
OpenHaul Financial Model Generator
Generates: OpenHaul_Financial_Model.xlsx

Reflects baseline metrics from the 82-turn chat:
- Seed Capital: $2,450,000
- Average Order Value (AOV): $28.00
- Take Rate: 22.0% ($6.16 Gross Take)
- Net Contribution Margin: $4.19 per order (Take rate $6.16 - variable gateway/insurance/cloud cost $1.97)
- Y1 Operating Expenses: $1,860,000
- Expansion: 1 Market (Y1) -> 5 Markets (Y2) -> 15 Markets (Y3)
- Year 3 Target: ~$23.5M EBITDA (36%+ EBITDA margin)
- Surge & FEMA Emergency Logistics Sensitivity:
  - Regional Storm Surge (14-day localized surge)
  - Superstorm / Hurricane Relief Scenario ($26B Katrina-scale federal emergency logistics pool sensitivity)
"""

import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def build_financial_model(output_path: str):
    wb = Workbook()
    
    # Styles
    navy_header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
    dark_slate_fill = PatternFill(start_color="2D3748", end_color="2D3748", fill_type="solid")
    accent_blue_fill = PatternFill(start_color="2B6CB0", end_color="2B6CB0", fill_type="solid")
    light_blue_fill = PatternFill(start_color="EBF8FF", end_color="EBF8FF", fill_type="solid")
    light_gray_fill = PatternFill(start_color="F7FAFC", end_color="F7FAFC", fill_type="solid")
    highlight_green_fill = PatternFill(start_color="C6F6D5", end_color="C6F6D5", fill_type="solid")
    highlight_gold_fill = PatternFill(start_color="FEFCBF", end_color="FEFCBF", fill_type="solid")

    font_title = Font(name="Calibri", size=16, bold=True, color="1A365D")
    font_subtitle = Font(name="Calibri", size=11, italic=True, color="4A5568")
    font_section = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
    font_col_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=11, bold=True)
    font_regular = Font(name="Calibri", size=11)
    font_metric_label = Font(name="Calibri", size=11, bold=True, color="2D3748")
    font_alert = Font(name="Calibri", size=11, bold=True, color="C53030")

    thin_border_side = Side(border_style="thin", color="CBD5E0")
    double_bottom_side = Side(border_style="double", color="1A365D")
    top_thin_bottom_double = Border(top=thin_border_side, bottom=double_bottom_side, left=thin_border_side, right=thin_border_side)
    cell_border = Border(top=thin_border_side, bottom=thin_border_side, left=thin_border_side, right=thin_border_side)

    # -------------------------------------------------------------
    # 1. Executive Summary & Core Projections Sheet
    # -------------------------------------------------------------
    ws1 = wb.active
    ws1.title = "Executive Summary & P&L"
    ws1.views.sheetView[0].showGridLines = True

    # Title Block
    ws1["A1"] = "OPENHAUL LOGISTICS CONSORTIUM"
    ws1["A1"].font = font_title
    ws1["A2"] = "3-Year Pro Forma Financial Model & Unit Economics (Series Seed $2.45M)"
    ws1["A2"].font = font_subtitle

    headers_ws1 = ["Line Item / Operational Metric", "Y1 (1 Market)", "Y2 (5 Markets)", "Y3 (15 Markets)", "CAGR / Benchmark"]
    for col_idx, h in enumerate(headers_ws1, 1):
        cell = ws1.cell(row=4, column=col_idx, value=h)
        cell.font = font_col_header
        cell.fill = navy_header_fill
        cell.alignment = Alignment(horizontal="center" if col_idx > 1 else "left", vertical="center")

    rows_ws1 = [
        # Operational Scale
        ("Active Operating Markets", 1, 5, 15, "15.0x expansion"),
        ("Monthly Active Drivers (Fleet)", 750, 3100, 8800, "11.7x expansion"),
        ("Annual Completed Dispatches (Orders)", 800000, 3150000, 8500000, "10.6x expansion"),
        ("Average Order Value (AOV)", 28.00, 28.00, 28.00, "$28.00 benchmark"),
        ("Gross Merchandise Value (GMV)", "=B7*B8", "=C7*C8", "=D7*D8", "Total System Volume"),
        
        # Unit Economics & Revenue
        ("OpenHaul Protocol Take Rate (%)", 0.22, 0.22, 0.22, "22.0% Take Rate"),
        ("Gross Protocol Revenue (Take)", "=B9*B10", "=C9*C10", "=D9*D10", "$6.16 / order"),
        ("Variable Driver Payment Processing & Gateway ($0.75)", "=B7*0.75", "=C7*0.75", "=D7*0.75", "$0.75 / order"),
        ("Dynamic HNOA Insurance Reserve ($0.95)", "=B7*0.95", "=C7*0.95", "=D7*0.95", "$0.95 / order"),
        ("ZK Telemetry, Verification & Cloud Infra ($0.27)", "=B7*0.27", "=C7*0.27", "=D7*0.27", "$0.27 / order"),
        ("Total Direct Variable Cost per Order ($1.97)", "=SUM(B12:B14)", "=SUM(C12:C14)", "=SUM(D12:D14)", "$1.97 / order"),
        ("Net Protocol Contribution Margin ($4.19 / order)", "=B11-B15", "=C11-C15", "=D11-D15", "68.0% Take Margin"),
        
        # Operating Expenses (OpEx)
        ("Core Engineering & ZK Rust Development", 920000, 2100000, 3800000, "Protocol maintainers"),
        ("Regional Operations, Market Launches & FEMA Desk", 450000, 1850000, 4200000, "Local field hubs"),
        ("Legal, Regulatory Compliance & HNOA Defense Counsel", 260000, 650000, 1500000, "1099 IC Defense & Fed"),
        ("Marketing, Driver Community & Ecosystem Grants", 150000, 800000, 1900000, "Driver viral growth"),
        ("General, Administrative & Security Auditing", 80000, 320000, 700000, "Formal verification"),
        ("Total Operating Expenses (OpEx)", "=SUM(B17:B21)", "=SUM(C17:C21)", "=SUM(D17:D21)", "Y1 OpEx = $1.86M"),
        
        # Profitability & Margins
        ("EBITDA ($)", "=B16-B22", "=C16-C22", "=D16-D22", "Target: ~$23.5M Y3"),
        ("EBITDA Margin (% of Gross Protocol Revenue)", "=B23/B11", "=C23/C11", "=D23/D11", "Target: 36%+ Y3 (44.9%)"),
        ("Depreciation, Amortization & Taxes", 35000, 850000, 4800000, "Effective Tax ~21%"),
        ("Net Operating Income / (Loss)", "=B23-B25", "=C23-C25", "=D23-D25", "Net Cash Generation")
    ]

    for r_idx, row_data in enumerate(rows_ws1, 5):
        is_highlight_row = r_idx in [9, 11, 16, 22, 23, 24, 26]
        
        for c_idx, val in enumerate(row_data, 1):
            cell = ws1.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_bold if is_highlight_row else font_regular
            cell.border = top_thin_bottom_double if r_idx in [22, 23, 26] else cell_border
            
            if is_highlight_row:
                cell.fill = highlight_green_fill if r_idx in [23, 24] else (highlight_gold_fill if r_idx in [11, 16] else light_blue_fill)
            
            # Format numbers
            if c_idx in [2, 3, 4]:
                if r_idx in [5, 6, 7]:
                    cell.number_format = "#,##0"
                elif r_idx in [8]:
                    cell.number_format = "$#,##0.00"
                elif r_idx in [10]:
                    cell.number_format = "0.0%"
                elif r_idx in [24]:
                    cell.number_format = "0.0%"
                else:
                    cell.number_format = "$#,##0"
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # -------------------------------------------------------------
    # 2. Capitalization & Seed Runway Sheet
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="Cap Table & Runway")
    ws2.views.sheetView[0].showGridLines = True

    ws2["A1"] = "OPENHAUL SEED ROUND & RUNWAY ANALYSIS"
    ws2["A1"].font = font_title
    ws2["A2"] = "Initial Seed Capital Deployment ($2.45M) & Runway Milestones"
    ws2["A2"].font = font_subtitle

    headers_ws2 = ["Category / Expenditure Bucket", "Allocated ($)", "Percentage of Round", "Runway Duration (Months)", "Target Deliverables & Milestones"]
    for col_idx, h in enumerate(headers_ws2, 1):
        cell = ws2.cell(row=4, column=col_idx, value=h)
        cell.font = font_col_header
        cell.fill = navy_header_fill
        cell.alignment = Alignment(horizontal="center" if col_idx > 1 else "left", vertical="center")

    cap_rows = [
        ("Core Engineering & STMP Protocol Rust Development", 950000, "=B5/2450000", 18, "STMP v1, ZK Custody proofs, Mobile App"),
        ("Commercial HNOA Insurance Master Facility Deposit", 400000, "=B6/2450000", 18, "Surplus lines deposit, broker letters of credit"),
        ("Federal / SAM.gov Bid & FEMA Desk Operations", 300000, "=B7/2450000", 18, "CAGE/UEI validation, SAM-gov-mcp integration"),
        ("Independent Contractor (1099) Legal & Regulatory Defense", 250000, "=B8/2450000", 18, "Primacy agreements, state ABC test compliance"),
        ("Pilot Market Launch (Pacific Coast Corridor - SF to Seattle)", 350000, "=B9/2450000", 12, "2,000 driver onboarding, 800k dispatches"),
        ("Working Capital Reserve & Contingency", 200000, "=B10/2450000", 18, "Disaster buffer & liquidity maintenance"),
        ("Total Series Seed Capitalization", "=SUM(B5:B10)", "=SUM(C5:C10)", 18, "Full 18-month path to profitability")
    ]

    for r_idx, row_data in enumerate(cap_rows, 5):
        is_total = (r_idx == 11)
        for c_idx, val in enumerate(row_data, 1):
            cell = ws2.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_bold if is_total else font_regular
            cell.border = top_thin_bottom_double if is_total else cell_border
            if is_total:
                cell.fill = highlight_gold_fill
            if c_idx == 2:
                cell.number_format = "$#,##0"
                cell.alignment = Alignment(horizontal="right")
            elif c_idx == 3:
                cell.number_format = "0.0%"
                cell.alignment = Alignment(horizontal="right")
            elif c_idx == 4:
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.alignment = Alignment(horizontal="left")

    # -------------------------------------------------------------
    # 3. FEMA Emergency Logistics & Catastrophe Surge Sensitivity
    # -------------------------------------------------------------
    ws3 = wb.create_sheet(title="FEMA & Disaster Surge Model")
    ws3.views.sheetView[0].showGridLines = True

    ws3["A1"] = "FEMA DISASTER LOGISTICS & SURGE SENSITIVITY"
    ws3["A1"].font = font_title
    ws3["A2"] = "Comparative Analysis: Regional Storm Relief vs. Katrina-Scale ($26B Federal Pool)"
    ws3["A2"].font = font_subtitle

    headers_ws3 = ["Metric / Simulation Parameter", "Baseline Municipal Operations", "Scenario A: Regional Storm (14-Day Surge)", "Scenario B: Major Hurricane (Katrina Scale $26B Pool)", "Sensitivity Notes / Assumptions"]
    for col_idx, h in enumerate(headers_ws3, 1):
        cell = ws3.cell(row=4, column=col_idx, value=h)
        cell.font = font_col_header
        cell.fill = dark_slate_fill
        cell.alignment = Alignment(horizontal="center" if col_idx > 1 else "left", vertical="center")

    surge_rows = [
        ("Surge Duration / Window", "Continuous (365 days)", "14 Days", "90 Days (Active Recovery)", "FEMA Rapid Response Directive"),
        ("Active High-Capacity Vans / Sprinters", 750, 3200, 14500, "Surge driver network activation"),
        ("Emergency Deliveries / Pallet Dispatches", 5000, 168000, 1250000, "Critical food, water, cold-chain pharma"),
        ("Surge Emergency Order Value (AOV)", 28.00, 75.00, 110.00, "FEMA expedited mission rates per haul"),
        ("Gross Emergency Freight Volume (GMV)", "=B7*B8", "=C7*C8", "=D7*D8", "Total relief capital deployed through network"),
        ("OpenHaul Emergency Take Rate (%)", 0.22, 0.18, 0.15, "Reduced public service rate for federal bids"),
        ("Gross Protocol Surge Revenue", "=B9*B10", "=C9*C10", "=D9*D10", "OpenHaul platform fee realization"),
        ("Direct Driver Pay (Expedited Emergency Scale)", "=B9*(1-B10)", "=C9*(1-C10)", "=D9*(1-D10)", "Driver net earnings ($1,200-$1,800/day)"),
        ("Platform Telemetry & Cold-Chain Insurance Reserve", "=B7*1.97", "=C7*4.50", "=D7*6.20", "Enhanced catastrophe cargo & RFID tracking"),
        ("Net Protocol Disaster Margin", "=B11-B13", "=C11-C13", "=D11-D13", "Surplus generated for consortium reserve"),
        ("Federal Emergency Pool Share Capture ($26B Baseline)", 0.0, 0.00048, 0.00529, "Share of $26B federal disaster appropriation")
    ]

    for r_idx, row_data in enumerate(surge_rows, 5):
        is_highlight = r_idx in [9, 11, 12, 14, 15]
        for c_idx, val in enumerate(row_data, 1):
            cell = ws3.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_bold if is_highlight else font_regular
            cell.border = top_thin_bottom_double if r_idx in [11, 14] else cell_border
            if is_highlight:
                cell.fill = highlight_gold_fill if r_idx == 11 else (highlight_green_fill if r_idx == 14 else light_blue_fill)
            
            if c_idx in [2, 3, 4]:
                if r_idx in [5]:
                    cell.alignment = Alignment(horizontal="center")
                elif r_idx in [6, 7]:
                    cell.number_format = "#,##0"
                    cell.alignment = Alignment(horizontal="right")
                elif r_idx in [8]:
                    cell.number_format = "$#,##0.00"
                    cell.alignment = Alignment(horizontal="right")
                elif r_idx in [10]:
                    cell.number_format = "0.0%"
                    cell.alignment = Alignment(horizontal="right")
                elif r_idx in [15]:
                    cell.number_format = "0.000%"
                    cell.alignment = Alignment(horizontal="right")
                else:
                    cell.number_format = "$#,##0"
                    cell.alignment = Alignment(horizontal="right")
            else:
                cell.alignment = Alignment(horizontal="left")

    # -------------------------------------------------------------
    # 4. Unit Economics Deep Dive & State-Machine Cost Matrix
    # -------------------------------------------------------------
    ws4 = wb.create_sheet(title="Unit Economics & State Matrix")
    ws4.views.sheetView[0].showGridLines = True

    ws4["A1"] = "OPENHAUL DYNAMIC UNIT ECONOMICS & STATE MATRIX"
    ws4["A1"].font = font_title
    ws4["A2"] = "Dynamic Insurance & Telemetry Overhead by App State"
    ws4["A2"].font = font_subtitle

    headers_ws4 = ["App State / Operational Phase", "Driver Primacy / Auto State", "HNOA Insurance Premium / Hour", "Telemetry & ZK Proof Compute", "OpenHaul Marginal Cost / Order", "Legal Liability Protection"]
    for col_idx, h in enumerate(headers_ws4, 1):
        cell = ws4.cell(row=4, column=col_idx, value=h)
        cell.font = font_col_header
        cell.fill = navy_header_fill
        cell.alignment = Alignment(horizontal="center" if col_idx > 1 else "left", vertical="center")

    matrix_rows = [
        ("STATE 1: IDLE (App Active, No Order Assigned)", "Driver Personal Auto Policy (PAP) Primary", "$0.08 / hr standby", "$0.01 / hr heartbeat", "$0.04 allocation", "Zero company tort liability; driver personal coverage"),
        ("STATE 2: EN_ROUTE (Dispatch Accepted, Traveling to Pickup)", "OpenHaul Contingent HNOA Liability Primary ($1M)", "$0.42 / hr active", "$0.04 / route proof", "$0.48 allocation", "Primary liability umbrella active for third-party injury/property"),
        ("STATE 3: IN_CUSTODY_RFID_VERIFIED (Cargo Loaded, ZK Custody Active)", "OpenHaul Full Commercial HNOA + $250k Cargo Transit Primary", "$0.78 / hr loaded", "$0.12 / zk-SNARK proof", "$1.45 allocation", "Complete cargo, physical damage, cold-chain temperature telemetry warranty"),
        ("BLENDED AVERAGE PER ORDER", "Composite Multi-Tier Autonomous Protection", "$0.95 blended", "$0.27 blended", "$1.97 total direct cost", "Maximum protection; ironclad 1099 IC independent status")
    ]

    for r_idx, row_data in enumerate(matrix_rows, 5):
        is_blended = (r_idx == 8)
        for c_idx, val in enumerate(row_data, 1):
            cell = ws4.cell(row=r_idx, column=c_idx, value=val)
            cell.font = font_bold if is_blended else font_regular
            cell.border = top_thin_bottom_double if is_blended else cell_border
            if is_blended:
                cell.fill = highlight_gold_fill
            cell.alignment = Alignment(horizontal="center" if c_idx in [3, 4, 5] else "left")

    # Adjust column widths for all sheets
    for ws in [ws1, ws2, ws3, ws4]:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or "")
                if len(val) > max_len and "\n" not in val:
                    max_len = len(val)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

    # Save workbook
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb.save(output_path)
    print(f"Financial Model successfully generated at: {output_path}")

if __name__ == "__main__":
    out_file = "/Users/alejandrolondono/dev/openhaul/biz/OpenHaul_Financial_Model.xlsx"
    build_financial_model(out_file)
