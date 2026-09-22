"""
EV Market 2026 — Streamlit Dashboard
=====================================
Interactive analytics dashboard for the EV Market 2026 dataset.
Run with:  streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Add project root to path so ev_market_analysis can be imported ─────────
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from ev_market_analysis import (
    USD_TO_INR,
    INPUT_CSV,
    OUTPUT_DIR,
    add_inr_prices,
    add_metrics,
    clean_data,
    load_and_map,
    run_eda,
    export_csvs,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="EV Market Analysis 2026",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ── Global ────────────────────────────────── */
    html, body, [class*="css"] { font-family: 'Segoe UI', system-ui, sans-serif; }

    /* ── Sidebar ───────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: #0f1117;
        border-right: 1px solid #2e3347;
    }
    section[data-testid="stSidebar"] * { color: #e0e6f0 !important; }
    section[data-testid="stSidebar"] h1 { color: #4fc3f7 !important; font-size: 1.1rem; }

    /* ── KPI cards ─────────────────────────────── */
    .kpi-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #252b3b 100%);
        border: 1px solid #2e3347;
        border-radius: 12px;
        padding: 18px 20px 14px 20px;
        text-align: center;
        margin-bottom: 8px;
    }
    .kpi-label {
        font-size: 0.72rem;
        color: #8b9abf;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.55rem;
        font-weight: 700;
        color: #4fc3f7;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 0.70rem;
        color: #6b7799;
        margin-top: 4px;
    }

    /* ── Section headers ───────────────────────── */
    .section-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #4fc3f7;
        border-left: 4px solid #4fc3f7;
        padding-left: 12px;
        margin: 24px 0 14px 0;
    }

    /* ── Tab strip ─────────────────────────────── */
    .stTabs [data-baseweb="tab"] {
        font-size: 0.85rem;
        font-weight: 600;
        padding: 8px 18px;
    }

    /* ── DataFrame ─────────────────────────────── */
    .dataframe-container { border-radius: 8px; overflow: hidden; }

    /* ── Footer ────────────────────────────────── */
    .footer {
        text-align: center;
        color: #6b7799;
        font-size: 0.75rem;
        padding: 20px 0 8px 0;
        border-top: 1px solid #2e3347;
        margin-top: 40px;
    }

    /* ── Main background ───────────────────────── */
    .main .block-container { background: #0a0e17; padding-top: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Plotly theme helper
# ---------------------------------------------------------------------------
PLOTLY_TEMPLATE = "plotly_dark"
COLOR_SEQ = px.colors.qualitative.Bold
ACCENT = "#4fc3f7"

def fig_style(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, system-ui, sans-serif", size=12, color="#c8d4e8"),
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            bgcolor="rgba(255,255,255,0.04)",
            bordercolor="#2e3347",
            borderwidth=1,
            font_size=11,
        ),
    )
    return fig


# ---------------------------------------------------------------------------
# Data loading — cached
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading & processing dataset …")
def get_data() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    df = load_and_map(INPUT_CSV)
    df = clean_data(df)
    df = add_inr_prices(df)
    df = add_metrics(df)
    results = run_eda(df)
    export_csvs(results, OUTPUT_DIR)
    return df, results


df_full, eda = get_data()


# ---------------------------------------------------------------------------
# Sidebar — global filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚡ EV Market 2026")
    st.markdown("---")
    st.markdown("### 🔍 Global Filters")

    all_brands = sorted(df_full["brand"].dropna().unique())
    sel_brands = st.multiselect("Brand", all_brands, default=all_brands, key="brand_filter")

    year_min, year_max = int(df_full["year"].min()), int(df_full["year"].max())
    sel_years = st.slider("Year Range", year_min, year_max, (year_min, year_max), key="year_filter")

    all_segments = sorted(df_full["market_segment"].dropna().unique())
    sel_segments = st.multiselect("Market Segment", all_segments, default=all_segments, key="seg_filter")

    all_countries = sorted(df_full["country_of_origin"].dropna().unique())
    sel_countries = st.multiselect("Country", all_countries, default=all_countries, key="country_filter")

    price_min_inr = float(df_full["price_inr"].min())
    price_max_inr = float(df_full["price_inr"].max())
    sel_price = st.slider(
        "Price Range (₹ Lakhs)",
        min_value=round(price_min_inr / 1e5, 1),
        max_value=round(price_max_inr / 1e5, 1),
        value=(round(price_min_inr / 1e5, 1), round(price_max_inr / 1e5, 1)),
        step=1.0,
        key="price_filter",
    )

    st.markdown("---")
    st.markdown(f"**Exchange Rate:** 1 USD = ₹{USD_TO_INR:,.2f}")
    st.markdown("**All monetary values in ₹ INR**")
    st.markdown("---")
    total_records = len(df_full)
    st.markdown(f"**Dataset:** {total_records:,} records")
    st.markdown(f"**Brands:** {df_full['brand'].nunique()}")
    st.markdown(f"**Countries:** {df_full['country_of_origin'].nunique()}")


# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def apply_filters(
    brands: list[str],
    years: tuple[int, int],
    segments: list[str],
    countries: list[str],
    price_range_lakh: tuple[float, float],
) -> pd.DataFrame:
    mask = (
        df_full["brand"].isin(brands)
        & df_full["year"].between(*years)
        & df_full["market_segment"].isin(segments)
        & df_full["country_of_origin"].isin(countries)
        & df_full["price_inr"].between(price_range_lakh[0] * 1e5, price_range_lakh[1] * 1e5)
    )
    return df_full[mask].copy()


df = apply_filters(sel_brands, sel_years, sel_segments, sel_countries, sel_price)

# ---------------------------------------------------------------------------
# Title bar
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style='background:linear-gradient(90deg,#0d1117 0%,#1a2035 100%);
                padding:20px 24px 16px 24px;border-radius:12px;
                border:1px solid #2e3347;margin-bottom:18px'>
        <h1 style='color:#4fc3f7;margin:0;font-size:1.8rem;font-weight:800;letter-spacing:-0.5px'>
            ⚡ EV Market Analysis 2026
        </h1>
        <p style='color:#8b9abf;margin:4px 0 0 0;font-size:0.9rem'>
            Comprehensive EV market intelligence dashboard &nbsp;|&nbsp;
            All prices in ₹ INR &nbsp;|&nbsp; 1 USD = ₹83.50
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if len(df) == 0:
    st.warning("No records match the current filters. Please widen your selection.")
    st.stop()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tabs = st.tabs([
    "📊 KPI Overview",
    "📈 Sales Analysis",
    "💰 Price Analysis",
    "🔋 Technology",
    "🏎️ Performance",
    "⭐ Customer & Safety",
    "🌍 Country Analysis",
    "📋 EV Comparison",
])

# ===========================================================================
# TAB 0 — KPI Overview
# ===========================================================================
with tabs[0]:
    st.markdown("<div class='section-header'>Key Performance Indicators</div>", unsafe_allow_html=True)

    avg_price = df["price_inr"].mean()
    median_price = df["price_inr"].median()
    avg_range = df["range_miles"].mean()
    avg_battery = df["battery_capacity_kwh"].mean()
    avg_price_kwh = df["price_per_kwh_inr"].mean()
    avg_range_10k = df["range_per_10k_inr"].mean()
    total_sales = df["annual_sales_units"].sum()
    avg_rating = df["customer_rating"].mean()
    n_brands = df["brand"].nunique()
    n_models = df["model"].nunique()

    c1, c2, c3, c4, c5 = st.columns(5)
    kpi_data = [
        (c1, "Avg EV Price",     f"₹{avg_price/1e5:.2f}L",       "Lakhs INR"),
        (c2, "Median Price",     f"₹{median_price/1e5:.2f}L",     "Lakhs INR"),
        (c3, "Avg Range",        f"{avg_range:.0f} mi",            "miles per charge"),
        (c4, "Avg Battery",      f"{avg_battery:.1f} kWh",         "battery capacity"),
        (c5, "Total Sales",      f"{total_sales/1e6:.2f}M",        "annual units"),
    ]
    for col, label, value, sub in kpi_data:
        col.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value'>{value}</div>"
            f"<div class='kpi-sub'>{sub}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    c6, c7, c8, c9, c10 = st.columns(5)
    kpi_data2 = [
        (c6,  "Price / kWh",     f"₹{avg_price_kwh:,.0f}",        "₹ per kWh"),
        (c7,  "Range / ₹10K",    f"{avg_range_10k:.3f} mi",        "miles per ₹10,000"),
        (c8,  "Avg Rating",      f"{avg_rating:.2f} / 10",         "customer score"),
        (c9,  "Brands",          str(n_brands),                    "unique brands"),
        (c10, "Models",          str(n_models),                    "unique models"),
    ]
    for col, label, value, sub in kpi_data2:
        col.markdown(
            f"<div class='kpi-card'>"
            f"<div class='kpi-label'>{label}</div>"
            f"<div class='kpi-value'>{value}</div>"
            f"<div class='kpi-sub'>{sub}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div class='section-header'>Market Segment Distribution</div>", unsafe_allow_html=True)
    col_l, col_r = st.columns(2)

    seg_counts = df["market_segment"].value_counts().reset_index()
    seg_counts.columns = ["Segment", "Count"]
    fig_seg_pie = px.pie(
        seg_counts, names="Segment", values="Count",
        title="Records by Market Segment",
        color_discrete_sequence=COLOR_SEQ,
    )
    col_l.plotly_chart(fig_style(fig_seg_pie, 380), use_container_width=True)

    country_counts = df["country_of_origin"].value_counts().reset_index()
    country_counts.columns = ["Country", "Count"]
    fig_country_bar = px.bar(
        country_counts, x="Country", y="Count", color="Country",
        title="Records by Country of Origin",
        color_discrete_sequence=COLOR_SEQ,
    )
    col_r.plotly_chart(fig_style(fig_country_bar, 380), use_container_width=True)

    st.markdown("<div class='section-header'>Price & Range Overview</div>", unsafe_allow_html=True)
    col_l2, col_r2 = st.columns(2)

    fig_hist_price = px.histogram(
        df, x=df["price_inr"] / 1e5, nbins=30,
        title="Price Distribution (₹ Lakhs)",
        labels={"x": "Price (₹ Lakhs)"},
        color_discrete_sequence=[ACCENT],
    )
    fig_hist_price.update_xaxes(title="Price (₹ Lakhs)")
    col_l2.plotly_chart(fig_style(fig_hist_price, 360), use_container_width=True)

    fig_hist_range = px.histogram(
        df, x="range_miles", nbins=30,
        title="Range Distribution (miles)",
        labels={"range_miles": "Range (miles)"},
        color_discrete_sequence=["#a78bfa"],
    )
    col_r2.plotly_chart(fig_style(fig_hist_range, 360), use_container_width=True)


# ===========================================================================
# TAB 1 — Sales Analysis
# ===========================================================================
with tabs[1]:
    st.markdown("<div class='section-header'>Sales Analysis</div>", unsafe_allow_html=True)

    # Brand sales bar
    brand_sales = (
        df.groupby("brand")["annual_sales_units"].sum()
        .sort_values(ascending=False).reset_index()
    )
    fig_brand_sales = px.bar(
        brand_sales, x="brand", y="annual_sales_units", color="brand",
        title="Total Annual Sales by Brand",
        labels={"annual_sales_units": "Annual Sales Units", "brand": "Brand"},
        color_discrete_sequence=COLOR_SEQ,
    )
    st.plotly_chart(fig_style(fig_brand_sales, 440), use_container_width=True)

    col_l, col_r = st.columns(2)

    # Sales by year
    year_sales = df.groupby("year")["annual_sales_units"].sum().reset_index()
    fig_year = px.line(
        year_sales, x="year", y="annual_sales_units",
        title="Annual Sales Trend by Model Year",
        markers=True,
        labels={"annual_sales_units": "Sales Units", "year": "Year"},
        color_discrete_sequence=[ACCENT],
    )
    col_l.plotly_chart(fig_style(fig_year, 380), use_container_width=True)

    # Sales by segment
    seg_sales = df.groupby("market_segment")["annual_sales_units"].sum().reset_index()
    fig_seg = px.pie(
        seg_sales, names="market_segment", values="annual_sales_units",
        title="Sales Share by Market Segment",
        color_discrete_sequence=COLOR_SEQ,
    )
    col_r.plotly_chart(fig_style(fig_seg, 380), use_container_width=True)

    # Top 15 models
    st.markdown("<div class='section-header'>Top 15 Models by Annual Sales</div>", unsafe_allow_html=True)
    top15 = (
        df.groupby(["brand", "model"])["annual_sales_units"].sum()
        .sort_values(ascending=False).head(15).reset_index()
    )
    top15["label"] = top15["brand"] + " " + top15["model"]
    fig_top15 = px.bar(
        top15, x="annual_sales_units", y="label", orientation="h",
        title="Top 15 EV Models by Annual Sales",
        labels={"annual_sales_units": "Annual Sales Units", "label": ""},
        color="annual_sales_units",
        color_continuous_scale="Blues",
    )
    fig_top15.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_style(fig_top15, 520), use_container_width=True)

    # Sales by body type & country
    col_l2, col_r2 = st.columns(2)
    body_sales = df.groupby("body_type")["annual_sales_units"].sum().reset_index()
    fig_body = px.bar(
        body_sales.sort_values("annual_sales_units", ascending=False),
        x="body_type", y="annual_sales_units", color="body_type",
        title="Sales by Body Type",
        labels={"annual_sales_units": "Sales Units", "body_type": "Body Type"},
        color_discrete_sequence=COLOR_SEQ,
    )
    col_l2.plotly_chart(fig_style(fig_body, 380), use_container_width=True)

    country_sales = df.groupby("country_of_origin")["annual_sales_units"].sum().reset_index()
    fig_cs = px.pie(
        country_sales, names="country_of_origin", values="annual_sales_units",
        title="Sales Share by Country",
        color_discrete_sequence=COLOR_SEQ,
    )
    col_r2.plotly_chart(fig_style(fig_cs, 380), use_container_width=True)


# ===========================================================================
# TAB 2 — Price Analysis
# ===========================================================================
with tabs[2]:
    st.markdown("<div class='section-header'>Price Analysis (₹ INR)</div>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    # Avg price by brand
    brand_price = df.groupby("brand")["price_inr"].mean().sort_values(ascending=False).reset_index()
    brand_price["price_lakh"] = brand_price["price_inr"] / 1e5
    fig_bp = px.bar(
        brand_price, x="brand", y="price_lakh", color="brand",
        title="Average Price by Brand (₹ Lakhs)",
        labels={"price_lakh": "Avg Price (₹ Lakhs)", "brand": "Brand"},
        color_discrete_sequence=COLOR_SEQ,
    )
    col_l.plotly_chart(fig_style(fig_bp, 400), use_container_width=True)

    # Price by segment box
    df_box = df.copy()
    df_box["price_lakh"] = df_box["price_inr"] / 1e5
    fig_box = px.box(
        df_box, x="market_segment", y="price_lakh", color="market_segment",
        title="Price Distribution by Market Segment (₹ Lakhs)",
        labels={"price_lakh": "Price (₹ Lakhs)", "market_segment": "Segment"},
        color_discrete_sequence=COLOR_SEQ,
    )
    col_r.plotly_chart(fig_style(fig_box, 400), use_container_width=True)

    # Price vs Range scatter
    st.markdown("<div class='section-header'>Price vs Range Scatter</div>", unsafe_allow_html=True)
    df_scatter = df.copy()
    df_scatter["price_lakh"] = df_scatter["price_inr"] / 1e5
    fig_scatter = px.scatter(
        df_scatter,
        x="price_lakh", y="range_miles",
        color="market_segment", size="annual_sales_units",
        hover_data=["brand", "model", "year", "battery_capacity_kwh"],
        title="Price (₹ Lakhs) vs Range (miles) — sized by Annual Sales",
        labels={"price_lakh": "Price (₹ Lakhs)", "range_miles": "Range (miles)"},
        color_discrete_sequence=COLOR_SEQ,
        size_max=30,
    )
    st.plotly_chart(fig_style(fig_scatter, 480), use_container_width=True)

    col_l2, col_r2 = st.columns(2)

    # Price per kWh by brand
    ppkwh = df.groupby("brand")["price_per_kwh_inr"].mean().sort_values(ascending=False).reset_index()
    fig_ppkwh = px.bar(
        ppkwh, x="brand", y="price_per_kwh_inr", color="brand",
        title="Average Price per kWh (₹/kWh) by Brand",
        labels={"price_per_kwh_inr": "₹/kWh", "brand": "Brand"},
        color_discrete_sequence=COLOR_SEQ,
    )
    col_l2.plotly_chart(fig_style(fig_ppkwh, 400), use_container_width=True)

    # Price vs battery scatter
    fig_bat_price = px.scatter(
        df_scatter, x="battery_capacity_kwh", y="price_lakh",
        color="brand", hover_data=["model", "year"],
        title="Battery Capacity vs Price (₹ Lakhs)",
        labels={"battery_capacity_kwh": "Battery (kWh)", "price_lakh": "Price (₹ Lakhs)"},
        color_discrete_sequence=COLOR_SEQ,
    )
    col_r2.plotly_chart(fig_style(fig_bat_price, 400), use_container_width=True)

    # Price heatmap: brand x year
    st.markdown("<div class='section-header'>Avg Price Heatmap — Brand × Year (₹ Lakhs)</div>", unsafe_allow_html=True)
    pivot_price = df.pivot_table(
        values="price_inr", index="brand", columns="year", aggfunc="mean"
    )
    pivot_price = pivot_price / 1e5  # convert to Lakhs
    fig_heat = px.imshow(
        pivot_price.round(1),
        title="Avg Price (₹ Lakhs) — Brand × Year",
        color_continuous_scale="Blues",
        aspect="auto",
        text_auto=True,
    )
    fig_heat.update_layout(coloraxis_colorbar_title="₹ Lakhs")
    st.plotly_chart(fig_style(fig_heat, 560), use_container_width=True)


# ===========================================================================
# TAB 3 — Technology Analysis
# ===========================================================================
with tabs[3]:
    st.markdown("<div class='section-header'>Technology Analysis</div>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    # Battery capacity distribution
    fig_bat_hist = px.histogram(
        df, x="battery_capacity_kwh", nbins=25, color="market_segment",
        title="Battery Capacity Distribution (kWh)",
        labels={"battery_capacity_kwh": "Battery Capacity (kWh)"},
        color_discrete_sequence=COLOR_SEQ,
        barmode="overlay",
        opacity=0.8,
    )
    col_l.plotly_chart(fig_style(fig_bat_hist, 400), use_container_width=True)

    # Charging speed distribution
    fig_chg_hist = px.histogram(
        df, x="charging_speed_kw", nbins=25, color="market_segment",
        title="Charging Speed Distribution (kW)",
        labels={"charging_speed_kw": "Charging Speed (kW)"},
        color_discrete_sequence=COLOR_SEQ,
        barmode="overlay",
        opacity=0.8,
    )
    col_r.plotly_chart(fig_style(fig_chg_hist, 400), use_container_width=True)

    # Autopilot level pie
    col_l2, col_r2 = st.columns(2)
    ap_counts = df["autopilot_level"].value_counts().reset_index()
    ap_counts.columns = ["level", "count"]
    ap_label_map = {0: "L0 – No Assist", 1: "L1 – Driver Assist",
                    2: "L2 – Partial Auto", 3: "L3 – Conditional Auto"}
    ap_counts["label"] = ap_counts["level"].map(ap_label_map).fillna("L3+")
    fig_ap = px.pie(
        ap_counts, names="label", values="count",
        title="Autopilot Level Distribution",
        color_discrete_sequence=COLOR_SEQ,
    )
    col_l2.plotly_chart(fig_style(fig_ap, 380), use_container_width=True)

    # Drive type pie
    dt_counts = df["drive_type"].value_counts().reset_index()
    dt_counts.columns = ["drive_type", "count"]
    fig_dt = px.pie(
        dt_counts, names="drive_type", values="count",
        title="Drive Type Distribution",
        color_discrete_sequence=COLOR_SEQ,
    )
    col_r2.plotly_chart(fig_style(fig_dt, 380), use_container_width=True)

    # Range vs Battery scatter
    st.markdown("<div class='section-header'>Range vs Battery Capacity</div>", unsafe_allow_html=True)
    fig_rb = px.scatter(
        df, x="battery_capacity_kwh", y="range_miles",
        color="brand", size="annual_sales_units",
        hover_data=["model", "year", "drive_type"],
        title="Battery Capacity (kWh) vs Range (miles)",
        labels={"battery_capacity_kwh": "Battery (kWh)", "range_miles": "Range (miles)"},
        color_discrete_sequence=COLOR_SEQ,
        trendline="ols",
        trendline_color_override="#fbbf24",
    )
    st.plotly_chart(fig_style(fig_rb, 480), use_container_width=True)

    # Avg battery by brand
    st.markdown("<div class='section-header'>Average Battery by Brand</div>", unsafe_allow_html=True)
    bat_brand = df.groupby("brand")["battery_capacity_kwh"].mean().sort_values(ascending=False).reset_index()
    fig_bat_brand = px.bar(
        bat_brand, x="brand", y="battery_capacity_kwh", color="brand",
        title="Average Battery Capacity by Brand (kWh)",
        labels={"battery_capacity_kwh": "Avg Battery (kWh)", "brand": "Brand"},
        color_discrete_sequence=COLOR_SEQ,
    )
    st.plotly_chart(fig_style(fig_bat_brand, 380), use_container_width=True)


# ===========================================================================
# TAB 4 — Performance Analysis
# ===========================================================================
with tabs[4]:
    st.markdown("<div class='section-header'>Performance Analysis</div>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    # Top 15 by horsepower
    top_hp = df.nlargest(15, "horsepower")[["brand", "model", "year", "horsepower", "price_inr"]].copy()
    top_hp["label"] = top_hp["brand"] + " " + top_hp["model"] + " (" + top_hp["year"].astype(str) + ")"
    top_hp["price_lakh"] = top_hp["price_inr"] / 1e5
    fig_hp = px.bar(
        top_hp, x="horsepower", y="label", orientation="h", color="horsepower",
        title="Top 15 EVs by Horsepower",
        labels={"horsepower": "Horsepower (HP)", "label": ""},
        color_continuous_scale="Reds",
    )
    fig_hp.update_layout(yaxis={"categoryorder": "total ascending"})
    col_l.plotly_chart(fig_style(fig_hp, 500), use_container_width=True)

    # Top 15 by 0-60 (fastest = lowest)
    top_accel = df.nsmallest(15, "acceleration_0_60_mph")[
        ["brand", "model", "year", "acceleration_0_60_mph", "horsepower"]
    ].copy()
    top_accel["label"] = top_accel["brand"] + " " + top_accel["model"] + " (" + top_accel["year"].astype(str) + ")"
    fig_accel = px.bar(
        top_accel, x="acceleration_0_60_mph", y="label", orientation="h",
        color="acceleration_0_60_mph",
        title="Top 15 Fastest EVs (0–60 mph)",
        labels={"acceleration_0_60_mph": "0–60 mph (seconds)", "label": ""},
        color_continuous_scale="Greens_r",
    )
    fig_accel.update_layout(yaxis={"categoryorder": "total descending"})
    col_r.plotly_chart(fig_style(fig_accel, 500), use_container_width=True)

    # Horsepower vs Price
    st.markdown("<div class='section-header'>Horsepower vs Price Scatter</div>", unsafe_allow_html=True)
    df_p = df.copy()
    df_p["price_lakh"] = df_p["price_inr"] / 1e5
    fig_hp_price = px.scatter(
        df_p, x="horsepower", y="price_lakh",
        color="market_segment", size="annual_sales_units",
        hover_data=["brand", "model", "year"],
        title="Horsepower vs Price (₹ Lakhs) — sized by Annual Sales",
        labels={"horsepower": "Horsepower (HP)", "price_lakh": "Price (₹ Lakhs)"},
        color_discrete_sequence=COLOR_SEQ,
    )
    st.plotly_chart(fig_style(fig_hp_price, 480), use_container_width=True)

    col_l2, col_r2 = st.columns(2)

    # Top speed distribution
    fig_ts_hist = px.histogram(
        df, x="top_speed_mph", nbins=20, color="drive_type",
        title="Top Speed Distribution (mph)",
        labels={"top_speed_mph": "Top Speed (mph)"},
        color_discrete_sequence=COLOR_SEQ,
        barmode="overlay", opacity=0.8,
    )
    col_l2.plotly_chart(fig_style(fig_ts_hist, 380), use_container_width=True)

    # Torque vs Horsepower
    fig_torque = px.scatter(
        df, x="horsepower", y="torque_nm",
        color="drive_type",
        hover_data=["brand", "model"],
        title="Horsepower vs Torque (Nm)",
        labels={"horsepower": "Horsepower (HP)", "torque_nm": "Torque (Nm)"},
        color_discrete_sequence=COLOR_SEQ,
    )
    col_r2.plotly_chart(fig_style(fig_torque, 380), use_container_width=True)


# ===========================================================================
# TAB 5 — Customer & Safety Analysis
# ===========================================================================
with tabs[5]:
    st.markdown("<div class='section-header'>Customer & Safety Analysis</div>", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    # Customer rating by brand
    cust_brand = df.groupby("brand")["customer_rating"].mean().sort_values(ascending=False).reset_index()
    fig_cust = px.bar(
        cust_brand, x="brand", y="customer_rating", color="brand",
        title="Average Customer Rating by Brand",
        labels={"customer_rating": "Avg Rating", "brand": "Brand"},
        color_discrete_sequence=COLOR_SEQ,
    )
    fig_cust.update_layout(yaxis_range=[0, cust_brand["customer_rating"].max() * 1.15])
    col_l.plotly_chart(fig_style(fig_cust, 400), use_container_width=True)

    # Safety rating distribution
    safety_counts = df["safety_rating"].value_counts().sort_index().reset_index()
    safety_counts.columns = ["rating", "count"]
    fig_safety = px.bar(
        safety_counts, x="rating", y="count", color="rating",
        title="Safety Rating Distribution",
        labels={"rating": "Safety Rating", "count": "Count"},
        color_continuous_scale="Greens",
    )
    col_r.plotly_chart(fig_style(fig_safety, 400), use_container_width=True)

    # Customer rating vs Price
    st.markdown("<div class='section-header'>Rating vs Price & Sales</div>", unsafe_allow_html=True)
    df_cr = df.copy()
    df_cr["price_lakh"] = df_cr["price_inr"] / 1e5
    fig_rat_price = px.scatter(
        df_cr, x="price_lakh", y="customer_rating",
        color="market_segment", size="annual_sales_units",
        hover_data=["brand", "model", "year"],
        title="Price (₹ Lakhs) vs Customer Rating — sized by Sales",
        labels={"price_lakh": "Price (₹ Lakhs)", "customer_rating": "Customer Rating"},
        color_discrete_sequence=COLOR_SEQ,
        trendline="ols",
        trendline_color_override="#fbbf24",
    )
    st.plotly_chart(fig_style(fig_rat_price, 480), use_container_width=True)

    col_l2, col_r2 = st.columns(2)

    # Warranty years distribution
    war_counts = df["warranty_years"].value_counts().sort_index().reset_index()
    war_counts.columns = ["years", "count"]
    fig_war = px.bar(
        war_counts, x="years", y="count", color="years",
        title="Warranty Years Distribution",
        labels={"years": "Warranty (years)", "count": "Count"},
        color_continuous_scale="Purples",
    )
    col_l2.plotly_chart(fig_style(fig_war, 380), use_container_width=True)

    # Safety rating vs Customer rating scatter
    fig_sc = px.scatter(
        df, x="safety_rating", y="customer_rating",
        color="market_segment",
        size="annual_sales_units",
        hover_data=["brand", "model"],
        title="Safety Rating vs Customer Rating",
        labels={"safety_rating": "Safety Rating", "customer_rating": "Customer Rating"},
        color_discrete_sequence=COLOR_SEQ,
    )
    col_r2.plotly_chart(fig_style(fig_sc, 380), use_container_width=True)

    # Top rated models
    st.markdown("<div class='section-header'>Top 10 Highest-Rated EV Models</div>", unsafe_allow_html=True)
    top_rated = (
        df.groupby(["brand", "model"])
        .agg(
            avg_rating=("customer_rating", "mean"),
            avg_safety=("safety_rating", "mean"),
            avg_price_lakh=("price_inr", lambda x: round(x.mean() / 1e5, 2)),
            total_sales=("annual_sales_units", "sum"),
        )
        .sort_values("avg_rating", ascending=False)
        .head(10)
        .reset_index()
    )
    top_rated.columns = ["Brand", "Model", "Avg Rating", "Avg Safety", "Avg Price (₹L)", "Total Sales"]
    st.dataframe(
        top_rated.style.background_gradient(subset=["Avg Rating", "Avg Safety"], cmap="Greens"),
        use_container_width=True, height=380,
    )


# ===========================================================================
# TAB 6 — Country Analysis
# ===========================================================================
with tabs[6]:
    st.markdown("<div class='section-header'>Country of Origin Analysis</div>", unsafe_allow_html=True)

    country_grp = (
        df.groupby("country_of_origin")
        .agg(
            brands=("brand", "nunique"),
            models=("model", "nunique"),
            avg_price_lakh=("price_inr", lambda x: round(x.mean() / 1e5, 2)),
            avg_range=("range_miles", "mean"),
            avg_battery=("battery_capacity_kwh", "mean"),
            total_sales=("annual_sales_units", "sum"),
            avg_rating=("customer_rating", "mean"),
            count=("country_of_origin", "count"),
        )
        .round(2)
        .sort_values("total_sales", ascending=False)
        .reset_index()
    )

    col_l, col_r = st.columns(2)

    fig_ctry_sales = px.bar(
        country_grp, x="country_of_origin", y="total_sales", color="country_of_origin",
        title="Total Sales by Country of Origin",
        labels={"total_sales": "Total Annual Sales", "country_of_origin": "Country"},
        color_discrete_sequence=COLOR_SEQ,
    )
    col_l.plotly_chart(fig_style(fig_ctry_sales, 400), use_container_width=True)

    fig_ctry_price = px.bar(
        country_grp, x="country_of_origin", y="avg_price_lakh", color="country_of_origin",
        title="Average Price by Country (₹ Lakhs)",
        labels={"avg_price_lakh": "Avg Price (₹ Lakhs)", "country_of_origin": "Country"},
        color_discrete_sequence=COLOR_SEQ,
    )
    col_r.plotly_chart(fig_style(fig_ctry_price, 400), use_container_width=True)

    # Country summary table
    st.markdown("<div class='section-header'>Country Summary</div>", unsafe_allow_html=True)
    disp = country_grp.rename(columns={
        "country_of_origin": "Country", "brands": "Brands", "models": "Models",
        "avg_price_lakh": "Avg Price (₹L)", "avg_range": "Avg Range (mi)",
        "avg_battery": "Avg Battery (kWh)", "total_sales": "Total Sales",
        "avg_rating": "Avg Rating", "count": "Records",
    })
    st.dataframe(
        disp.style.background_gradient(subset=["Total Sales"], cmap="Blues"),
        use_container_width=True, height=280,
    )

    col_l2, col_r2 = st.columns(2)

    # Segment by country stacked
    seg_country = df.groupby(["country_of_origin", "market_segment"])["annual_sales_units"].sum().reset_index()
    fig_seg_ctry = px.bar(
        seg_country, x="country_of_origin", y="annual_sales_units", color="market_segment",
        title="Sales by Country & Market Segment",
        labels={"annual_sales_units": "Annual Sales", "country_of_origin": "Country"},
        color_discrete_sequence=COLOR_SEQ,
        barmode="stack",
    )
    col_l2.plotly_chart(fig_style(fig_seg_ctry, 400), use_container_width=True)

    # Avg range by country
    fig_range_ctry = px.bar(
        country_grp.sort_values("avg_range", ascending=False),
        x="country_of_origin", y="avg_range", color="country_of_origin",
        title="Average Range by Country (miles)",
        labels={"avg_range": "Avg Range (miles)", "country_of_origin": "Country"},
        color_discrete_sequence=COLOR_SEQ,
    )
    col_r2.plotly_chart(fig_style(fig_range_ctry, 400), use_container_width=True)


# ===========================================================================
# TAB 7 — EV Comparison Table
# ===========================================================================
with tabs[7]:
    st.markdown("<div class='section-header'>EV Comparison Table</div>", unsafe_allow_html=True)

    st.markdown("Use the filters on the left sidebar to narrow down vehicles.")

    # Build display table
    display_cols = [
        "brand", "model", "year", "variant", "market_segment",
        "price_usd", "price_inr", "battery_capacity_kwh", "range_miles",
        "charging_speed_kw", "acceleration_0_60_mph", "top_speed_mph",
        "horsepower", "torque_nm", "drive_type", "body_type",
        "seating_capacity", "safety_rating", "customer_rating",
        "annual_sales_units", "country_of_origin",
        "price_per_kwh_inr", "range_per_kwh", "range_per_10k_inr",
    ]
    available_cols = [c for c in display_cols if c in df.columns]
    df_display = df[available_cols].copy()

    # Format monetary columns
    df_display["price_usd"] = df_display["price_usd"].map(lambda x: f"${x:,.0f}")
    df_display["price_inr"] = df_display["price_inr"].map(lambda x: f"₹{x:,.0f}")
    df_display["price_per_kwh_inr"] = df_display["price_per_kwh_inr"].map(lambda x: f"₹{x:,.0f}")

    friendly_names = {
        "brand": "Brand", "model": "Model", "year": "Year", "variant": "Variant",
        "market_segment": "Segment", "price_usd": "Price (USD)", "price_inr": "Price (₹ INR)",
        "battery_capacity_kwh": "Battery (kWh)", "range_miles": "Range (mi)",
        "charging_speed_kw": "Charge (kW)", "acceleration_0_60_mph": "0-60 (s)",
        "top_speed_mph": "Top Speed (mph)", "horsepower": "HP", "torque_nm": "Torque (Nm)",
        "drive_type": "Drive", "body_type": "Body", "seating_capacity": "Seats",
        "safety_rating": "Safety ★", "customer_rating": "Rating",
        "annual_sales_units": "Sales/yr", "country_of_origin": "Country",
        "price_per_kwh_inr": "₹/kWh", "range_per_kwh": "mi/kWh",
        "range_per_10k_inr": "mi/₹10K",
    }
    df_display.rename(columns=friendly_names, inplace=True)

    # Search
    search_term = st.text_input("🔍 Search brand, model, or country", "")
    if search_term:
        mask = df_display.apply(lambda col: col.astype(str).str.contains(search_term, case=False, na=False)).any(axis=1)
        df_display = df_display[mask]

    st.markdown(f"**Showing {len(df_display):,} records**")
    st.dataframe(df_display, use_container_width=True, height=600)

    # Export
    csv_bytes = df[available_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download Filtered Data as CSV",
        data=csv_bytes,
        file_name="ev_market_filtered.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class='footer'>
        ⚡ EV Market Analysis 2026 &nbsp;|&nbsp;
        All monetary values in ₹ INR (1 USD = ₹83.50) &nbsp;|&nbsp;
        Data: ev_market_2026.csv &nbsp;|&nbsp;
        Built with Streamlit &amp; Plotly
    </div>
    """,
    unsafe_allow_html=True,
)
