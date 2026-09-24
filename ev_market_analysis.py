"""
EV Market Analysis 2026
========================
Comprehensive data analytics pipeline for the EV Market 2026 dataset.
- Loads and validates CSV with flexible column mapping
- Cleans and normalises data
- Converts prices from USD → INR
- Calculates key metrics
- Performs EDA
- Exports dashboard-ready CSVs for IBM BI

Author : Mahfooz Alam
Python : 3.9+
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# ── Exchange rate ──────────────────────────────────────────────────────────
# Source: Reserve Bank of India reference rate (configurable).
# Update this single variable whenever the rate changes.
USD_TO_INR: float = 83.50  # 1 USD = ₹83.50

# ── File paths ──────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent
INPUT_CSV = DATA_DIR / "ev_market_2026.csv"
OUTPUT_DIR = DATA_DIR / "output"

# ── Flexible column-name mapping ────────────────────────────────────────────
# Maps each *canonical* column name to every known variation in real datasets.
# The loader normalises headers and looks them up here.
COLUMN_ALIASES: dict[str, list[str]] = {
    "brand":                  ["brand", "make", "manufacturer"],
    "model":                  ["model", "model_name", "vehicle_model"],
    "year":                   ["year", "model_year", "year_of_manufacture"],
    "variant":                ["variant", "trim", "trim_level", "edition"],
    "price_usd":              ["price_usd", "price", "price_usd_$", "price usd",
                               "vehicle_price", "msrp", "price_$", "cost_usd"],
    "battery_capacity_kwh":   ["battery_capacity_kwh", "battery_kwh", "battery",
                               "battery_capacity", "kwh"],
    "range_miles":            ["range_miles", "range", "range_mi", "driving_range"],
    "charging_speed_kw":      ["charging_speed_kw", "charging_kw", "charging_speed",
                               "max_charging_kw"],
    "acceleration_0_60_mph":  ["acceleration_0_60_mph", "acceleration", "0_60",
                               "0_to_60", "accel_0_60"],
    "top_speed_mph":          ["top_speed_mph", "top_speed", "max_speed_mph"],
    "horsepower":             ["horsepower", "hp", "power_hp"],
    "torque_nm":              ["torque_nm", "torque", "max_torque_nm"],
    "drive_type":             ["drive_type", "drivetrain", "drive"],
    "seating_capacity":       ["seating_capacity", "seats", "passenger_capacity"],
    "body_type":              ["body_type", "body", "vehicle_type", "car_type"],
    "cargo_volume_cubic_ft":  ["cargo_volume_cubic_ft", "cargo_volume", "trunk_space"],
    "weight_kg":              ["weight_kg", "weight", "curb_weight_kg"],
    "safety_rating":          ["safety_rating", "safety", "safety_score", "ncap_rating"],
    "autopilot_level":        ["autopilot_level", "autonomy_level", "autopilot",
                               "self_driving_level"],
    "country_of_origin":      ["country_of_origin", "country", "origin", "made_in"],
    "market_segment":         ["market_segment", "segment", "category", "class"],
    "annual_sales_units":     ["annual_sales_units", "sales", "annual_sales",
                               "units_sold", "sales_volume"],
    "customer_rating":        ["customer_rating", "rating", "user_rating",
                               "customer_score"],
    "warranty_years":         ["warranty_years", "warranty", "warranty_period"],
}

REQUIRED_COLUMNS = [
    "brand", "model", "year", "price_usd",
    "battery_capacity_kwh", "range_miles", "annual_sales_units",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

# Force UTF-8 on Windows so INR/Unicode symbols don't crash the console handler
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(DATA_DIR / "ev_analysis.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _normalise_col(name: str) -> str:
    """Lower-case, strip, replace spaces/hyphens with underscores."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def _build_reverse_map() -> dict[str, str]:
    """Reverse COLUMN_ALIASES so every alias → canonical name."""
    rev: dict[str, str] = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            rev[_normalise_col(alias)] = canonical
    return rev


REVERSE_MAP = _build_reverse_map()


def fmt_inr(value: float) -> str:
    """Format a number as ₹ Indian Rupee with comma grouping."""
    if pd.isna(value):
        return "N/A"
    return f"₹{value:,.0f}"


# ---------------------------------------------------------------------------
# Step 1 – Load & column-map
# ---------------------------------------------------------------------------


def load_and_map(path: Path) -> pd.DataFrame:
    """Load CSV, normalise headers, and apply flexible column mapping."""
    log.info("Loading dataset from %s", path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path, encoding="utf-8")
    log.info("Raw shape: %d rows × %d columns", *df.shape)

    # Normalise all column names
    df.columns = [_normalise_col(c) for c in df.columns]

    # Rename via reverse map
    rename_map = {c: REVERSE_MAP[c] for c in df.columns if c in REVERSE_MAP}
    df.rename(columns=rename_map, inplace=True)
    log.info("Columns mapped: %s", list(rename_map.keys()))

    # Report missing required columns
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        log.warning("Missing required columns: %s", missing)
    else:
        log.info("All required columns present [OK]")

    # Report unmapped columns (extra columns kept as-is)
    all_canonical = set(COLUMN_ALIASES.keys())
    unmapped = [c for c in df.columns if c not in all_canonical]
    if unmapped:
        log.info("Unmapped (extra) columns kept: %s", unmapped)

    return df


# ---------------------------------------------------------------------------
# Step 2 – Clean data
# ---------------------------------------------------------------------------


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates, fix types, clip outliers, impute nulls."""
    log.info("=== Data Cleaning ===")
    original_rows = len(df)

    # ── Duplicates ──────────────────────────────────────────────────────────
    dupes = df.duplicated().sum()
    if dupes:
        df.drop_duplicates(inplace=True)
        log.info("Dropped %d duplicate rows", dupes)

    # ── Numeric coercion ────────────────────────────────────────────────────
    numeric_cols = [
        "year", "price_usd", "battery_capacity_kwh", "range_miles",
        "charging_speed_kw", "acceleration_0_60_mph", "top_speed_mph",
        "horsepower", "torque_nm", "seating_capacity", "cargo_volume_cubic_ft",
        "weight_kg", "safety_rating", "autopilot_level", "annual_sales_units",
        "customer_rating", "warranty_years",
    ]
    for col in numeric_cols:
        if col in df.columns:
            before = df[col].isna().sum()
            df[col] = pd.to_numeric(df[col], errors="coerce")
            after = df[col].isna().sum()
            if after > before:
                log.warning("Column '%s': %d values coerced to NaN", col, after - before)

    # ── Validity filters ────────────────────────────────────────────────────
    # Remove rows with non-positive prices or battery
    invalid_price = df["price_usd"] <= 0 if "price_usd" in df.columns else pd.Series(False, index=df.index)
    invalid_battery = df["battery_capacity_kwh"] <= 0 if "battery_capacity_kwh" in df.columns else pd.Series(False, index=df.index)
    invalid_mask = invalid_price | invalid_battery
    n_invalid = invalid_mask.sum()
    if n_invalid:
        df = df[~invalid_mask].copy()
        log.info("Removed %d rows with invalid price/battery values", n_invalid)

    # Year sanity check (1990–2030)
    if "year" in df.columns:
        bad_year = ~df["year"].between(1990, 2030)
        if bad_year.sum():
            df = df[~bad_year].copy()
            log.info("Removed %d rows with out-of-range year", bad_year.sum())

    # Customer rating clamp (0–5 typical; allow up to 10 if dataset uses that scale)
    if "customer_rating" in df.columns:
        max_rating = df["customer_rating"].max()
        if max_rating > 5:
            log.info("customer_rating max=%s — keeping original scale (0–10)", max_rating)

    # ── Missing-value imputation ─────────────────────────────────────────────
    # Numeric → median; categorical → mode
    cat_cols = ["brand", "model", "variant", "drive_type", "body_type",
                "country_of_origin", "market_segment"]
    num_fill_cols = [
        "charging_speed_kw", "acceleration_0_60_mph", "top_speed_mph",
        "horsepower", "torque_nm", "cargo_volume_cubic_ft", "weight_kg",
        "safety_rating", "warranty_years",
    ]
    for col in num_fill_cols:
        if col in df.columns and df[col].isna().any():
            med = df[col].median()
            df[col].fillna(med, inplace=True)
            log.info("Imputed '%s' NaNs with median=%.2f", col, med)

    for col in cat_cols:
        if col in df.columns and df[col].isna().any():
            mode_val = df[col].mode().iloc[0]
            df[col].fillna(mode_val, inplace=True)
            log.info("Imputed '%s' NaNs with mode='%s'", col, mode_val)

    log.info(
        "Cleaning complete: %d -> %d rows (removed %d)",
        original_rows, len(df), original_rows - len(df),
    )
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Step 3 – Currency conversion
# ---------------------------------------------------------------------------


def add_inr_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Add price_inr column; never overwrite price_usd."""
    log.info("Converting USD -> INR at rate 1 USD = INR %.2f", USD_TO_INR)
    df["price_inr"] = (df["price_usd"] * USD_TO_INR).round(2)
    log.info("'price_inr' column created. Sample: INR %.0f", df["price_inr"].iloc[0])
    return df


# ---------------------------------------------------------------------------
# Step 4 – Derived metrics
# ---------------------------------------------------------------------------


def add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute analytical KPI columns."""
    log.info("Computing derived metrics ...")

    # Price per kWh (₹/kWh)
    df["price_per_kwh_inr"] = (df["price_inr"] / df["battery_capacity_kwh"]).round(2)

    # Range per ₹10,000
    df["range_per_10k_inr"] = (df["range_miles"] / (df["price_inr"] / 10_000)).round(4)

    # Range per kWh (miles/kWh)
    df["range_per_kwh"] = (df["range_miles"] / df["battery_capacity_kwh"]).round(4)

    # Value score (arbitrary composite: range / price_inr * 1M)
    df["value_score"] = ((df["range_miles"] / df["price_inr"]) * 1_000_000).round(4)

    log.info("Derived metrics added: price_per_kwh_inr, range_per_10k_inr, range_per_kwh, value_score")
    return df


# ---------------------------------------------------------------------------
# Step 5 – EDA summary
# ---------------------------------------------------------------------------


def run_eda(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return a dict of summary DataFrames for each EDA dimension."""
    log.info("=== Exploratory Data Analysis ===")
    results: dict[str, pd.DataFrame] = {}

    # ── Overall KPIs ────────────────────────────────────────────────────────
    kpis = {
        "Total Records":            len(df),
        "Unique Brands":            df["brand"].nunique(),
        "Unique Models":            df["model"].nunique(),
        "Year Range":               f"{int(df['year'].min())}–{int(df['year'].max())}",
        "Avg EV Price (₹)":         fmt_inr(df["price_inr"].mean()),
        "Median EV Price (₹)":      fmt_inr(df["price_inr"].median()),
        "Min Price (₹)":            fmt_inr(df["price_inr"].min()),
        "Max Price (₹)":            fmt_inr(df["price_inr"].max()),
        "Avg Battery (kWh)":        f"{df['battery_capacity_kwh'].mean():.1f} kWh",
        "Avg Range (miles)":        f"{df['range_miles'].mean():.1f} mi",
        "Avg Price/kWh (₹)":        fmt_inr(df["price_per_kwh_inr"].mean()),
        "Avg Range/₹10K":           f"{df['range_per_10k_inr'].mean():.4f} mi",
        "Avg Range/kWh":            f"{df['range_per_kwh'].mean():.4f} mi/kWh",
        "Total Annual Sales":       f"{df['annual_sales_units'].sum():,.0f}",
        "Avg Customer Rating":      f"{df['customer_rating'].mean():.2f}",
        "Exchange Rate Used":       f"1 USD = ₹{USD_TO_INR:.2f}",
    }
    results["kpis"] = pd.DataFrame(list(kpis.items()), columns=["Metric", "Value"])
    log.info("KPIs computed (%d metrics)", len(kpis))

    # ── Brand analysis ──────────────────────────────────────────────────────
    brand_df = (
        df.groupby("brand")
        .agg(
            models=("model", "nunique"),
            avg_price_inr=("price_inr", "mean"),
            avg_range_miles=("range_miles", "mean"),
            avg_battery_kwh=("battery_capacity_kwh", "mean"),
            total_sales=("annual_sales_units", "sum"),
            avg_rating=("customer_rating", "mean"),
            count=("brand", "count"),
        )
        .round(2)
        .sort_values("total_sales", ascending=False)
        .reset_index()
    )
    results["brand_analysis"] = brand_df
    log.info("Brand analysis: %d brands", len(brand_df))

    # ── Year analysis ────────────────────────────────────────────────────────
    year_df = (
        df.groupby("year")
        .agg(
            models=("model", "nunique"),
            avg_price_inr=("price_inr", "mean"),
            avg_range_miles=("range_miles", "mean"),
            total_sales=("annual_sales_units", "sum"),
            avg_battery_kwh=("battery_capacity_kwh", "mean"),
            count=("year", "count"),
        )
        .round(2)
        .reset_index()
        .sort_values("year")
    )
    results["year_analysis"] = year_df
    log.info("Year analysis: %d years", len(year_df))

    # ── Country analysis ────────────────────────────────────────────────────
    country_df = (
        df.groupby("country_of_origin")
        .agg(
            brands=("brand", "nunique"),
            models=("model", "nunique"),
            avg_price_inr=("price_inr", "mean"),
            total_sales=("annual_sales_units", "sum"),
            avg_rating=("customer_rating", "mean"),
            count=("country_of_origin", "count"),
        )
        .round(2)
        .sort_values("total_sales", ascending=False)
        .reset_index()
    )
    results["country_analysis"] = country_df
    log.info("Country analysis: %d countries", len(country_df))

    # ── Market segment analysis ─────────────────────────────────────────────
    segment_df = (
        df.groupby("market_segment")
        .agg(
            avg_price_inr=("price_inr", "mean"),
            avg_range_miles=("range_miles", "mean"),
            avg_battery_kwh=("battery_capacity_kwh", "mean"),
            total_sales=("annual_sales_units", "sum"),
            avg_rating=("customer_rating", "mean"),
            count=("market_segment", "count"),
        )
        .round(2)
        .sort_values("avg_price_inr", ascending=False)
        .reset_index()
    )
    results["segment_analysis"] = segment_df
    log.info("Segment analysis: %d segments", len(segment_df))

    # ── Body type analysis ──────────────────────────────────────────────────
    body_df = (
        df.groupby("body_type")
        .agg(
            avg_price_inr=("price_inr", "mean"),
            avg_range_miles=("range_miles", "mean"),
            total_sales=("annual_sales_units", "sum"),
            count=("body_type", "count"),
        )
        .round(2)
        .sort_values("total_sales", ascending=False)
        .reset_index()
    )
    results["body_type_analysis"] = body_df

    # ── Drive type analysis ─────────────────────────────────────────────────
    drive_df = (
        df.groupby("drive_type")
        .agg(
            avg_price_inr=("price_inr", "mean"),
            avg_range_miles=("range_miles", "mean"),
            total_sales=("annual_sales_units", "sum"),
            count=("drive_type", "count"),
        )
        .round(2)
        .sort_values("total_sales", ascending=False)
        .reset_index()
    )
    results["drive_type_analysis"] = drive_df

    # ── Price distribution buckets ──────────────────────────────────────────
    bins = [0, 25e5, 50e5, 75e5, 100e5, 150e5, 200e5, np.inf]
    labels = ["<₹25L", "₹25–50L", "₹50–75L", "₹75–100L", "₹100–150L", "₹150–200L", ">₹200L"]
    df["price_bucket"] = pd.cut(df["price_inr"], bins=bins, labels=labels, right=False)
    price_dist = df["price_bucket"].value_counts().sort_index().reset_index()
    price_dist.columns = ["price_range", "count"]
    results["price_distribution"] = price_dist

    # ── Top 20 models by sales ──────────────────────────────────────────────
    top_models = (
        df.groupby(["brand", "model"])
        .agg(
            total_sales=("annual_sales_units", "sum"),
            avg_price_inr=("price_inr", "mean"),
            avg_range_miles=("range_miles", "mean"),
            avg_rating=("customer_rating", "mean"),
        )
        .round(2)
        .sort_values("total_sales", ascending=False)
        .head(20)
        .reset_index()
    )
    results["top_models"] = top_models

    # ── Technology analysis ─────────────────────────────────────────────────
    tech_df = (
        df.groupby("autopilot_level")
        .agg(
            count=("autopilot_level", "count"),
            avg_price_inr=("price_inr", "mean"),
            avg_range_miles=("range_miles", "mean"),
            total_sales=("annual_sales_units", "sum"),
        )
        .round(2)
        .reset_index()
        .sort_values("autopilot_level")
    )
    tech_df["autopilot_level_label"] = tech_df["autopilot_level"].map(
        {0: "L0-No Assist", 1: "L1-Assist", 2: "L2-Partial", 3: "L3-Conditional"}
    ).fillna("L3+")
    results["technology_analysis"] = tech_df

    # ── Performance analysis ────────────────────────────────────────────────
    perf_df = df[["brand", "model", "year", "variant",
                  "horsepower", "torque_nm", "acceleration_0_60_mph",
                  "top_speed_mph", "price_inr", "market_segment"]].copy()
    perf_df["power_to_price"] = (perf_df["horsepower"] / perf_df["price_inr"] * 1e6).round(4)
    results["performance_data"] = perf_df.sort_values("horsepower", ascending=False)

    # ── Safety analysis ─────────────────────────────────────────────────────
    safety_df = (
        df.groupby("safety_rating")
        .agg(
            count=("safety_rating", "count"),
            avg_price_inr=("price_inr", "mean"),
            avg_range_miles=("range_miles", "mean"),
            total_sales=("annual_sales_units", "sum"),
            avg_customer_rating=("customer_rating", "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("safety_rating")
    )
    results["safety_analysis"] = safety_df

    # ── Full enriched dataset ────────────────────────────────────────────────
    results["full_dataset"] = df.copy()

    return results


# ---------------------------------------------------------------------------
# Step 6 – Export CSVs
# ---------------------------------------------------------------------------


def export_csvs(results: dict[str, pd.DataFrame], output_dir: Path) -> None:
    """Write all result DataFrames as UTF-8 CSVs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, df_out in results.items():
        out_path = output_dir / f"{name}.csv"
        df_out.to_csv(out_path, index=False, encoding="utf-8")
        log.info("Exported: %s (%d rows)", out_path.name, len(df_out))
    log.info("All CSVs written to: %s", output_dir)


# ---------------------------------------------------------------------------
# Step 7 – Console summary report
# ---------------------------------------------------------------------------


def print_summary(results: dict[str, pd.DataFrame]) -> None:
    """Print a formatted summary to console (ASCII-safe for Windows cp1252)."""

    def _safe(text: str) -> str:
        """Replace non-ASCII chars with ASCII substitutes for Windows console."""
        return (
            text.encode("ascii", errors="replace")
                .decode("ascii")
                .replace("?", " ")
        )

    sep = "=" * 70
    print(f"\n{sep}")
    print("  EV MARKET ANALYSIS 2026  -  EXECUTIVE SUMMARY")
    print(f"{sep}\n")

    kpis_df = results["kpis"]
    for _, row in kpis_df.iterrows():
        val = _safe(str(row["Value"]))
        print(f"  {row['Metric']:<35} {val}")

    print(f"\n{sep}")
    print("  TOP 5 BRANDS BY SALES")
    print(f"{sep}")
    brand_df = results["brand_analysis"].head(5)
    print(brand_df[["brand", "count", "avg_price_inr", "total_sales", "avg_rating"]].to_string(index=False))

    print(f"\n{sep}")
    print("  MARKET SEGMENT SUMMARY")
    print(f"{sep}")
    seg = results["segment_analysis"]
    print(seg[["market_segment", "count", "avg_price_inr", "total_sales"]].to_string(index=False))

    print(f"\n{sep}")
    print("  TOP 10 MODELS BY SALES")
    print(f"{sep}")
    top = results["top_models"].head(10)
    print(top[["brand", "model", "total_sales", "avg_price_inr", "avg_range_miles"]].to_string(index=False))

    print(f"\n{sep}\n")


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def main() -> None:
    log.info("=== EV Market Analysis 2026 - Starting ===")

    # 1. Load
    df = load_and_map(INPUT_CSV)

    # 2. Clean
    df = clean_data(df)

    # 3. Currency conversion
    df = add_inr_prices(df)

    # 4. Derived metrics
    df = add_metrics(df)

    # 5. EDA
    results = run_eda(df)

    # 6. Export
    export_csvs(results, OUTPUT_DIR)

    # 7. Summary
    print_summary(results)

    log.info("=== Analysis complete. Outputs in: %s ===", OUTPUT_DIR)


if __name__ == "__main__":
    main()
