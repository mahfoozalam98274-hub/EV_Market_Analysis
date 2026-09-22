# ⚡ EV Market Analysis 2026

> Comprehensive Python data analytics project for the **EV Market 2026** dataset — featuring automated data cleaning, INR currency conversion, EDA, dashboard-ready CSV exports, and an interactive **Streamlit** dashboard.

---

## 📁 Project Structure

```
EV_Market_2026/
├── ev_market_2026.csv          # Raw dataset (source of truth)
├── ev_market_analysis.py       # Core analytics pipeline
├── app.py                      # Streamlit interactive dashboard
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── Project_Report.md           # Full project report
├── ev_analysis.log             # Runtime log (auto-created)
└── output/                     # Dashboard-ready CSVs (auto-created)
    ├── full_dataset.csv
    ├── kpis.csv
    ├── brand_analysis.csv
    ├── year_analysis.csv
    ├── country_analysis.csv
    ├── segment_analysis.csv
    ├── top_models.csv
    ├── performance_data.csv
    ├── safety_analysis.csv
    ├── technology_analysis.csv
    ├── body_type_analysis.csv
    ├── drive_type_analysis.csv
    └── price_distribution.csv
```

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.9 or later
- pip

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run the analytics pipeline (generates all output CSVs)

```powershell
python ev_market_analysis.py
```

### 4. Launch the interactive Streamlit dashboard

```powershell
streamlit run app.py
```

The dashboard will open at **http://localhost:8501** in your browser.

---

## 💱 USD → INR Conversion

| Parameter | Value |
|---|---|
| Exchange rate used | **1 USD = ₹83.50** |
| Configurable variable | `USD_TO_INR` in `ev_market_analysis.py` line 31 |
| Source | Reserve Bank of India reference rate |

**Key rule:** The original `price_usd` column is **never overwritten**. A new column `price_inr` is derived as:

```python
price_inr = price_usd × USD_TO_INR
```

> To update the exchange rate, edit the single constant at the top of `ev_market_analysis.py`:
> ```python
> USD_TO_INR: float = 83.50  # ← update this value
> ```

All monetary values shown in the dashboard, KPI cards, charts, and exported CSVs use **₹ INR only**.

---

## 🗺️ Flexible Column Mapping

The loader (`load_and_map()`) normalises all incoming column headers (lower-case, strip, underscores) and maps them to a canonical set using `COLUMN_ALIASES` in `ev_market_analysis.py`.

### Example mappings

| Canonical column | Accepted variations |
|---|---|
| `price_usd` | `price`, `price_usd`, `Price USD`, `vehicle_price`, `msrp`, `cost_usd`, `price_$` |
| `brand` | `brand`, `make`, `manufacturer` |
| `battery_capacity_kwh` | `battery_kwh`, `battery`, `battery_capacity`, `kwh` |
| `range_miles` | `range`, `range_mi`, `driving_range` |
| `annual_sales_units` | `sales`, `annual_sales`, `units_sold`, `sales_volume` |
| `country_of_origin` | `country`, `origin`, `made_in` |

### How it works

```python
# 1. Normalise all headers
df.columns = [col.strip().lower().replace(" ", "_").replace("-", "_") for col in df.columns]

# 2. Build reverse lookup:  alias → canonical
reverse_map = {alias: canonical for canonical, aliases in COLUMN_ALIASES.items() for alias in aliases}

# 3. Rename matched columns
df.rename(columns={c: reverse_map[c] for c in df.columns if c in reverse_map})
```

Missing required columns are **reported as warnings** in the log; unmapped extra columns are **kept as-is**.

---

## 🧹 Data Cleaning Steps

| Step | Action |
|---|---|
| Duplicate rows | Removed with `drop_duplicates()` |
| Type coercion | All numeric columns forced with `pd.to_numeric(errors='coerce')` |
| Invalid prices | Rows with `price_usd ≤ 0` or `battery_capacity_kwh ≤ 0` removed |
| Year sanity | Rows outside 1990–2030 removed |
| Numeric nulls | Filled with **column median** |
| Categorical nulls | Filled with **column mode** |

---

## 📊 Calculated Metrics

| Metric | Formula | Unit |
|---|---|---|
| Average EV Price | `mean(price_inr)` | ₹ INR |
| Price per kWh | `price_inr / battery_capacity_kwh` | ₹/kWh |
| Range per ₹10,000 | `range_miles / (price_inr / 10000)` | miles/₹10K |
| Range per kWh | `range_miles / battery_capacity_kwh` | miles/kWh |
| Value Score | `(range_miles / price_inr) × 1,000,000` | composite |

---

## 📈 Dashboard Tabs

| Tab | Contents |
|---|---|
| **KPI Overview** | 10 KPI cards, segment pie, country bar, price & range histograms |
| **Sales Analysis** | Brand sales bar, year trend, segment share, top 15 models, body/country breakdown |
| **Price Analysis** | Brand price bar, segment box-plot, price-vs-range scatter, price/kWh, heatmap |
| **Technology** | Battery & charging histograms, autopilot pie, drive-type pie, range-vs-battery scatter |
| **Performance** | Top-HP bar, fastest-accel bar, HP-vs-price scatter, speed & torque charts |
| **Customer & Safety** | Rating by brand, safety distribution, rating-vs-price scatter, warranty bar, top-rated table |
| **Country Analysis** | Sales & price by country, stacked-segment chart, summary table |
| **EV Comparison** | Full searchable & filterable table, CSV download |

---

## 📤 Output Files (IBM BI-ready)

All CSVs in `output/` are UTF-8 encoded and ready for import into **IBM Cognos**, **IBM Planning Analytics**, or any BI tool.

- `full_dataset.csv` — enriched master dataset with `price_inr` and all derived columns
- `kpis.csv` — flat KPI summary (metric name + value)
- `brand_analysis.csv` — aggregated stats per brand
- `year_analysis.csv` — aggregated stats per model year
- `country_analysis.csv` — aggregated stats per country
- `segment_analysis.csv` — aggregated stats per market segment
- `top_models.csv` — top 20 models by annual sales
- `technology_analysis.csv` — stats by autopilot level
- `performance_data.csv` — full performance columns with power-to-price ratio
- `safety_analysis.csv` — stats by safety rating
- `price_distribution.csv` — count per ₹-bucket

---

## 🔧 Configuration

All configurable constants are at the top of `ev_market_analysis.py`:

```python
USD_TO_INR: float = 83.50          # Exchange rate
INPUT_CSV  = DATA_DIR / "ev_market_2026.csv"   # Input path
OUTPUT_DIR = DATA_DIR / "output"               # Output directory
COLUMN_ALIASES = { ... }            # Column name mappings
REQUIRED_COLUMNS = [ ... ]         # Columns validated on load
```

---

## 🐛 Logging

All pipeline steps are logged to both the console and `ev_analysis.log`:

```
2025-01-15 10:23:01 | INFO     | Loading dataset from ev_market_2026.csv
2025-01-15 10:23:01 | INFO     | Raw shape: 200 rows × 24 columns
2025-01-15 10:23:01 | INFO     | All required columns present ✓
2025-01-15 10:23:01 | INFO     | Cleaning complete: 200 → 200 rows
2025-01-15 10:23:01 | INFO     | Converting USD → INR at rate 1 USD = ₹83.50
...
```

---

## 📝 Dataset Columns

| Column | Type | Description |
|---|---|---|
| `brand` | str | Vehicle manufacturer |
| `model` | str | Model name |
| `year` | int | Model year |
| `variant` | str | Trim/variant level |
| `price_usd` | float | Price in US dollars |
| `battery_capacity_kwh` | float | Battery capacity (kWh) |
| `range_miles` | float | Driving range (miles) |
| `charging_speed_kw` | float | Max charging speed (kW) |
| `acceleration_0_60_mph` | float | 0–60 mph time (seconds) |
| `top_speed_mph` | float | Top speed (mph) |
| `horsepower` | float | Motor power (HP) |
| `torque_nm` | float | Peak torque (Nm) |
| `drive_type` | str | AWD / FWD / RWD |
| `seating_capacity` | int | Number of seats |
| `body_type` | str | SUV / Sedan / Hatchback etc. |
| `cargo_volume_cubic_ft` | float | Cargo space (ft³) |
| `weight_kg` | float | Curb weight (kg) |
| `safety_rating` | int | Safety score |
| `autopilot_level` | int | SAE automation level (0–3) |
| `country_of_origin` | str | Manufacturing country |
| `market_segment` | str | Budget / Mid-range / Premium / Luxury |
| `annual_sales_units` | int | Estimated annual sales |
| `customer_rating` | float | Customer satisfaction score |
| `warranty_years` | int | Warranty period (years) |

---

## 🤝 Contributing

Pull requests welcome. Please follow the existing code style and add docstrings to all functions.

---

*© 2026 EV Market Analytics Team — Data sourced from ev_market_2026.csv*
