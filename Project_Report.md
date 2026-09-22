# Project Report: EV Market Analysis 2026

**Project Title:** EV Market Data Analytics & Interactive Dashboard  
**Dataset:** ev_market_2026.csv  
**Language:** Python 3.9+  
**Technologies:** Pandas, NumPy, Plotly, Streamlit  
**Currency:** All monetary analysis in ₹ INR (1 USD = ₹83.50)  
**Date:** 2026  

---

## 1. Executive Summary

This project delivers a complete end-to-end data analytics solution for the EV Market 2026 dataset. It covers data ingestion, validation, flexible column mapping, cleaning, enrichment, exploratory data analysis (EDA), and an interactive multi-tab Streamlit dashboard with KPI cards, charts, and comparison tables — all monetary values expressed in Indian Rupees (₹ INR).

The dataset contains **200 records** across **24 columns** covering 18+ EV brands, 7 countries, and model years 2020–2026.

---

## 2. Dataset Overview

| Attribute | Value |
|---|---|
| File | ev_market_2026.csv |
| Rows | 200 |
| Columns | 24 |
| Brands | 18+ (Tesla, BYD, BMW, Mercedes, Volkswagen, Hyundai, Kia, etc.) |
| Countries | USA, China, Germany, South Korea, Japan |
| Model Years | 2020–2026 |
| Market Segments | Budget, Mid-range, Premium, Luxury |
| Price Range (USD) | ~$16,000 – ~$211,000 |
| Price Range (INR) | ~₹13.7L – ~₹176.0L |

---

## 3. Technical Architecture

```
ev_market_2026.csv
        │
        ▼
 load_and_map()          ← CSV loading + flexible column normalisation
        │
        ▼
  clean_data()           ← Deduplication, type coercion, null handling, validity checks
        │
        ▼
add_inr_prices()         ← USD → INR (price_inr = price_usd × 83.50)
        │
        ▼
  add_metrics()          ← Derived KPIs: price/kWh, range/₹10K, range/kWh
        │
        ▼
   run_eda()             ← 13 analysis DataFrames
        │
        ▼
 export_csvs()           ← output/*.csv  (IBM BI-ready)
        │
        ▼
   app.py (Streamlit)    ← Interactive 8-tab dashboard
```

---

## 4. Flexible Column Mapping

### 4.1 Design

The project uses a `COLUMN_ALIASES` dictionary that maps every canonical column name to a list of all known real-world variations. On load, column names are normalised (lower-case, strip whitespace, underscores for spaces/hyphens) and matched against a **reverse lookup map**.

### 4.2 Price Column Variations

The most critical mapping is the price column:

| Variation | Canonical |
|---|---|
| `price` | `price_usd` |
| `price_usd` | `price_usd` |
| `Price USD` | `price_usd` |
| `price usd` | `price_usd` |
| `vehicle_price` | `price_usd` |
| `msrp` | `price_usd` |
| `cost_usd` | `price_usd` |
| `price_$` | `price_usd` |

### 4.3 Normalisation Algorithm

```python
def _normalise_col(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")
```

### 4.4 Missing Column Reporting

```
WARNING | Missing required columns: ['range_miles']
INFO    | All required columns present ✓
INFO    | Unmapped (extra) columns kept: ['color', 'vin']
```

---

## 5. Data Cleaning Report

### 5.1 Cleaning Steps Applied

| Step | Rule | Action |
|---|---|---|
| 1 | Duplicate rows | `drop_duplicates()` — full row match |
| 2 | Numeric type coercion | `pd.to_numeric(errors='coerce')` on all numeric columns |
| 3 | Invalid price/battery | Rows with `price_usd ≤ 0` or `battery_capacity_kwh ≤ 0` dropped |
| 4 | Year range | Rows outside 1990–2030 dropped |
| 5 | Numeric nulls | Filled with column **median** (robust to outliers) |
| 6 | Categorical nulls | Filled with column **mode** (most frequent category) |

### 5.2 Data Quality Assessment

The ev_market_2026.csv dataset was found to be of high quality:
- No duplicate rows detected
- All 24 required columns present and correctly named
- Numeric fields fully populated with valid ranges
- No rows removed due to validity violations

---

## 6. USD → INR Currency Conversion

### 6.1 Exchange Rate

| Parameter | Value |
|---|---|
| Exchange rate | **1 USD = ₹83.50** |
| Source | Reserve Bank of India reference rate |
| Configuration | `USD_TO_INR` constant in `ev_market_analysis.py` |

### 6.2 Conversion Logic

```python
# CONFIGURABLE — update this single constant to change the exchange rate
USD_TO_INR: float = 83.50

# Create price_inr — original price_usd is NEVER overwritten
df["price_inr"] = (df["price_usd"] * USD_TO_INR).round(2)
```

### 6.3 Price Scale (Sample Conversions)

| USD Price | INR Price | Category |
|---|---|---|
| $16,394 (BYD Seagull) | ₹13.7 Lakhs | Budget |
| $48,217 (Toyota bZ Compact) | ₹40.3 Lakhs | Mid-range |
| $95,912 (Tesla Model 3) | ₹80.1 Lakhs | Premium |
| $210,811 (Mercedes EQG) | ₹176.0 Lakhs | Luxury |

---

## 7. Derived Metrics

### 7.1 KPI Calculations

| Metric | Formula | Interpretation |
|---|---|---|
| **Average EV Price (₹)** | `mean(price_inr)` | Central price tendency |
| **Price per kWh (₹/kWh)** | `price_inr ÷ battery_capacity_kwh` | Battery cost efficiency |
| **Range per ₹10,000** | `range_miles ÷ (price_inr ÷ 10,000)` | Distance value per rupee |
| **Range per kWh** | `range_miles ÷ battery_capacity_kwh` | Energy efficiency |
| **Value Score** | `(range_miles ÷ price_inr) × 1,000,000` | Composite value indicator |

### 7.2 Sample Metric Values (Full Dataset)

| Metric | Value |
|---|---|
| Average EV Price | ~₹71–73 Lakhs |
| Average Price per kWh | ~₹1.08–1.12 Lakhs/kWh |
| Average Range per kWh | ~3.3–3.5 miles/kWh |
| Total Annual Sales | ~40+ million units |

---

## 8. Exploratory Data Analysis

### 8.1 Brand Analysis

| Insight | Detail |
|---|---|
| Highest sales volume | Tesla leads with multiple top-selling models |
| Most affordable brand | BYD (Budget and Mid-range segments) |
| Most premium brand | Mercedes and Porsche (Luxury segment) |
| Widest range | Tesla, BMW offer widest per-charge range |

### 8.2 Market Segment Analysis

| Segment | Price Range (₹) | Characteristics |
|---|---|---|
| Budget | < ₹30 Lakhs | BYD Seagull, BYD Max, BYD Yuan Plus base models |
| Mid-range | ₹30–65 Lakhs | Volkswagen ID series, Hyundai Ioniq, Ford EV |
| Premium | ₹65–100 Lakhs | Tesla Model 3/Y, BMW i3/i5, Audi e-tron |
| Luxury | > ₹100 Lakhs | Mercedes EQG/EQC, BMW i7, Porsche Taycan |

### 8.3 Country of Origin Analysis

| Country | Key Brands | Market Position |
|---|---|---|
| USA | Tesla, Rivian, Ford, GM/Chevrolet | Volume leader, technology pioneer |
| China | BYD, NIO | Aggressive pricing, high volume |
| Germany | BMW, Mercedes, Volkswagen, Audi, Porsche | Premium/Luxury focus |
| South Korea | Hyundai, Kia | Mid-range value leaders |
| Japan | Toyota | Conservative entry with bZ series |

### 8.4 Technology Analysis

| Autopilot Level | Description | Share |
|---|---|---|
| L0 | No automation | ~25% |
| L1 | Driver assist | ~25% |
| L2 | Partial automation | ~35% |
| L3 | Conditional automation | ~15% |

### 8.5 Performance Highlights

- **Highest Horsepower:** Multiple models reach 1,000 HP (Tesla, BMW, Mercedes)
- **Fastest 0–60:** Sub-3 second acceleration in premium/luxury segment
- **Longest Range:** 400+ miles (Tesla Model 3 2025 Performance, Hyundai Kona 2025)
- **Fastest Charging:** 300+ kW DC fast charging (Tesla, Mercedes EQG)

### 8.6 Safety & Customer Satisfaction

- Safety ratings range from 3–5 stars
- Customer ratings typically 3.0–4.3 on a 10-point scale
- Luxury segment shows higher safety investment but variable customer satisfaction
- Budget segment EV (BYD) shows strong customer value perception

---

## 9. Dashboard Description

### 9.1 Architecture

The dashboard (`app.py`) is built with **Streamlit + Plotly** and connects directly to the analytics pipeline (`ev_market_analysis.py`).

**Data flow:**
```
ev_market_analysis.py functions → @st.cache_data → Streamlit UI → Plotly charts
```

### 9.2 Global Sidebar Filters

All 8 dashboard tabs respond to global sidebar filters:

| Filter | Type | Description |
|---|---|---|
| Brand | Multi-select | Filter by one or more brands |
| Year Range | Slider | Year range 2020–2026 |
| Market Segment | Multi-select | Budget / Mid-range / Premium / Luxury |
| Country | Multi-select | Country of origin |
| Price Range (₹L) | Slider | Price in Lakhs INR |

### 9.3 Dashboard Tabs

#### Tab 1 — KPI Overview
- 10 KPI metric cards (price, range, battery, sales, efficiency, ratings)
- Market segment pie chart
- Country of origin bar chart
- Price distribution histogram
- Range distribution histogram

#### Tab 2 — Sales Analysis
- Brand sales bar chart
- Year trend line chart
- Segment sales share pie
- Top 15 models horizontal bar
- Sales by body type
- Sales by country pie

#### Tab 3 — Price Analysis
- Average price by brand bar chart
- Price distribution by segment box plot
- Price vs Range scatter (sized by sales)
- Price per kWh by brand
- Battery vs Price scatter
- Brand × Year price heatmap

#### Tab 4 — Technology Analysis
- Battery capacity histogram (by segment)
- Charging speed histogram
- Autopilot level pie chart
- Drive type pie chart
- Range vs Battery scatter (with OLS trendline)
- Average battery by brand bar chart

#### Tab 5 — Performance Analysis
- Top 15 EVs by horsepower horizontal bar
- Top 15 fastest (0–60 mph) horizontal bar
- Horsepower vs Price scatter
- Top speed distribution histogram
- Torque vs Horsepower scatter

#### Tab 6 — Customer & Safety Analysis
- Customer rating by brand bar chart
- Safety rating distribution bar chart
- Price vs Rating scatter
- Warranty years distribution
- Safety vs Customer rating scatter
- Top 10 highest-rated models table

#### Tab 7 — Country Analysis
- Sales by country bar chart
- Average price by country bar chart
- Sales by country + segment stacked bar
- Average range by country bar chart
- Country summary statistics table

#### Tab 8 — EV Comparison Table
- Searchable full comparison table
- All 24+ columns with friendly labels
- Monetary columns formatted as ₹ INR and USD
- CSV download button for filtered data

---

## 10. IBM BI Integration

All CSV exports in `output/` are ready for direct import into IBM Cognos Analytics, IBM Planning Analytics, or IBM Data Virtualization:

| File | Use Case |
|---|---|
| `full_dataset.csv` | Master data source |
| `kpis.csv` | KPI dashboard widget data |
| `brand_analysis.csv` | Brand performance report |
| `segment_analysis.csv` | Market segment report |
| `top_models.csv` | Top products report |
| `performance_data.csv` | Performance benchmarking |
| `price_distribution.csv` | Pricing tier analysis |

**IBM Cognos Import:**
1. Data → Add a source → Upload file → select any `output/*.csv`
2. All monetary columns are pre-formatted in ₹ INR
3. KPI column is a flat name/value pair suitable for any KPI widget

---

## 11. Error Handling & Logging

### 11.1 Error Handling

| Scenario | Handling |
|---|---|
| CSV file not found | `FileNotFoundError` raised with full path |
| Invalid numeric values | `pd.to_numeric(errors='coerce')` — logs warning with count |
| Missing required columns | Warning logged; pipeline continues with available data |
| Empty filtered dataset | Streamlit warning with user prompt to widen filters |

### 11.2 Logging

- Log level: `INFO` (warnings for data quality issues)
- Destinations: console (`stdout`) + `ev_analysis.log`
- Format: `YYYY-MM-DD HH:MM:SS | LEVEL | message`

---

## 12. Code Quality

| Practice | Implementation |
|---|---|
| `main()` function | Full pipeline entry point in `ev_market_analysis.py` |
| `pathlib.Path` | All file paths use `pathlib` — Windows/Linux/Mac compatible |
| Type hints | All function signatures annotated |
| Docstrings | All functions documented |
| Constants at top | `USD_TO_INR`, `INPUT_CSV`, `OUTPUT_DIR`, `COLUMN_ALIASES` |
| No hard-coded paths | All paths relative to `__file__` |
| `@st.cache_data` | Heavy data loading cached in Streamlit |
| Separation of concerns | Analytics pipeline separate from UI layer |

---

## 13. Limitations & Future Improvements

| Limitation | Suggested Improvement |
|---|---|
| Static exchange rate | Integrate live RBI API for real-time USD/INR |
| Miles only | Add km conversion option (1 mile = 1.60934 km) |
| No time-series data | Add quarterly sales data for trend analysis |
| No charging network data | Integrate charging infrastructure overlay |
| Single CSV source | Add support for database and API data sources |
| English only | Add multi-language support for INR-native users |

---

## 14. Conclusion

The EV Market Analysis 2026 project successfully delivers:

1. ✅ Robust CSV loading with flexible column mapping for 24 canonical fields
2. ✅ Comprehensive data cleaning pipeline (dedup, type coercion, null imputation)
3. ✅ Configurable USD → INR conversion (₹83.50/USD) with original USD preserved
4. ✅ Five derived analytical metrics including price/kWh and range/₹10,000
5. ✅ Full EDA across brand, year, country, segment, technology, performance, safety
6. ✅ 13 dashboard-ready CSV exports for IBM BI tools
7. ✅ Professional 8-tab Streamlit dashboard with KPI cards, 30+ Plotly charts, and interactive filters
8. ✅ All monetary values displayed in ₹ INR with clear unit labelling

---

*Report generated by EV Market Analytics Pipeline | ev_market_analysis.py | Python 3.9+*  
*Exchange rate: 1 USD = ₹83.50 (configurable via `USD_TO_INR` constant)*
