"""
EV Market 2026 - Streamlit Dashboard
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
# Custom CSS  (all Unicode only inside HTML strings, safe for browsers)
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    html, body, [class*="css"] { font-family: 'Segoe UI', system-ui, sans-serif; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #0f1620 100%);
        border-right: 2px solid #00b4d8;
    }
    section[data-testid="stSidebar"] * { color: #e0e6f0 !important; }
    section[data-testid="stSidebar"] .sidebar-title {
        color: #4fc3f7 !important; font-size: 1.15rem; font-weight: 700;
    }

    .kpi-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #252b3b 100%);
        border: 1px solid #2e3347;
        border-radius: 14px;
        padding: 20px 16px 16px 16px;
        text-align: center;
        margin-bottom: 10px;
        transition: border-color 0.2s;
    }
    .kpi-card:hover { border-color: #00b4d8; }
    .kpi-label {
        font-size: 0.70rem;
        color: #8b9abf;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 1.50rem;
        font-weight: 800;
        color: #4fc3f7;
        line-height: 1.1;
    }
    .kpi-sub { font-size: 0.68rem; color: #6b7799; margin-top: 5px; }

    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #4fc3f7;
        border-left: 4px solid #00b4d8;
        padding-left: 12px;
        margin: 22px 0 12px 0;
        letter-spacing: 0.02em;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 0.82rem;
        font-weight: 600;
        padding: 8px 16px;
        border-radius: 6px 6px 0 0;
    }
    .stTabs [aria-selected="true"] { color: #00b4d8 !important; }

    .footer {
        text-align: center;
        color: #6b7799;
        font-size: 0.74rem;
        padding: 20px 0 8px 0;
        border-top: 1px solid #2e3347;
        margin-top: 40px;
    }

    div[data-testid="stMetric"] label { color: #8b9abf !important; font-size: 0.75rem; }
    div[data-testid="stMetric"] div   { color: #4fc3f7 !important; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Plotly dark theme helper
# ---------------------------------------------------------------------------
PLOTLY_TEMPLATE = "plotly_dark"
COLOR_SEQ = px.colors.qualitative.Bold
ACCENT = "#4fc3f7"
GOLD   = "#ffd700"
BG     = "rgba(0,0,0,0)"
CARD   = "rgba(19,35,56,0.85)"


def fig_style(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(family="Segoe UI, system-ui, sans-serif", size=12, color="#c8d4e8"),
        height=height,
        margin=dict(l=10, r=10, t=44, b=10),
        legend=dict(
            bgcolor="rgba(255,255,255,0.04)",
            bordercolor="#2e3347",
            borderwidth=1,
            font_size=10,
        ),
        title_font=dict(size=14, color="#ffffff"),
    )
    fig.update_xaxes(gridcolor="#1e3a5f", zerolinecolor="#1e3a5f")
    fig.update_yaxes(gridcolor="#1e3a5f", zerolinecolor="#1e3a5f")
    return fig


def kpi_card(col, label: str, value: str, sub: str = "") -> None:
    col.markdown(
        f"<div class='kpi-card'>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'>{value}</div>"
        f"<div class='kpi-sub'>{sub}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    st.markdown(f"<div class='section-header'>{title}</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading & processing EV dataset ...")
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
# Sidebar — Global Filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        "<div style='padding:12px 0 4px 0; font-size:1.3rem; font-weight:800;"
        " color:#4fc3f7; letter-spacing:-0.5px;'>⚡ EV Market 2026</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='font-size:0.78rem;color:#8b9abf;margin-bottom:12px;'>"
        "Data Analytics & BI Dashboard</div>",
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("**🔍 Global Filters**")

    all_brands = sorted(df_full["brand"].dropna().unique())
    sel_brands = st.multiselect("Brand", all_brands, default=all_brands, key="brand_filter")

    year_min, year_max = int(df_full["year"].min()), int(df_full["year"].max())
    sel_years = st.slider("Year Range", year_min, year_max, (year_min, year_max), key="year_filter")

    all_segments = sorted(df_full["market_segment"].dropna().unique())
    sel_segments = st.multiselect("Market Segment", all_segments, default=all_segments, key="seg_filter")

    all_countries = sorted(df_full["country_of_origin"].dropna().unique())
    sel_countries = st.multiselect("Country", all_countries, default=all_countries, key="country_filter")

    p_min = round(float(df_full["price_inr"].min()) / 1e5, 1)
    p_max = round(float(df_full["price_inr"].max()) / 1e5, 1)
    sel_price = st.slider("Price Range (Rs Lakhs)", p_min, p_max, (p_min, p_max), step=1.0, key="price_filter")

    st.divider()
    st.markdown(f"**Exchange Rate:** `1 USD = Rs {USD_TO_INR:,.2f}`")
    st.markdown("**All prices in Rs INR**")
    st.divider()
    st.caption(f"📊 {len(df_full):,} records loaded")
    st.caption(f"🏷️ {df_full['brand'].nunique()} brands | {df_full['model'].nunique()} models")
    st.caption(f"🌍 {df_full['country_of_origin'].nunique()} countries")


# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def apply_filters(
    brands: list,
    years: tuple,
    segments: list,
    countries: list,
    price_lakh: tuple,
) -> pd.DataFrame:
    mask = (
        df_full["brand"].isin(brands)
        & df_full["year"].between(*years)
        & df_full["market_segment"].isin(segments)
        & df_full["country_of_origin"].isin(countries)
        & df_full["price_inr"].between(price_lakh[0] * 1e5, price_lakh[1] * 1e5)
    )
    return df_full[mask].copy()


df = apply_filters(sel_brands, sel_years, sel_segments, sel_countries, sel_price)

# ---------------------------------------------------------------------------
# Header banner
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div style='background:linear-gradient(90deg,#0d1b2a 0%,#1a2540 50%,#0d1b2a 100%);
                padding:22px 28px 18px 28px; border-radius:14px;
                border:1px solid #2e3347; margin-bottom:20px;
                box-shadow: 0 4px 20px rgba(0,180,216,0.12);'>
        <h1 style='color:#4fc3f7;margin:0;font-size:1.85rem;font-weight:900;
                   letter-spacing:-0.5px;line-height:1.1;'>
            ⚡ EV Market Analysis 2026
        </h1>
        <p style='color:#8b9abf;margin:5px 0 0 0;font-size:0.9rem;'>
            Data Analytics &amp; Business Intelligence Dashboard &nbsp;|&nbsp;
            <span style='color:#ffd700;'>All prices in &#8377; INR</span> &nbsp;|&nbsp;
            1 USD = &#8377;{USD_TO_INR:,.2f} &nbsp;|&nbsp;
            <span style='color:#4fc3f7;font-weight:600;'>{len(df):,} records</span> selected
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if len(df) == 0:
    st.warning("⚠️ No records match the current filters. Please widen your selection in the sidebar.")
    st.stop()

# ---------------------------------------------------------------------------
# TABS
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
    section("Key Performance Indicators")

    avg_price   = df["price_inr"].mean()
    med_price   = df["price_inr"].median()
    avg_range   = df["range_miles"].mean()
    avg_bat     = df["battery_capacity_kwh"].mean()
    avg_ppkwh   = df["price_per_kwh_inr"].mean()
    avg_r10k    = df["range_per_10k_inr"].mean()
    total_sales = df["annual_sales_units"].sum()
    avg_rating  = df["customer_rating"].mean()
    avg_safety  = df["safety_rating"].mean()
    avg_chg     = df["charging_speed_kw"].mean()

    r1 = st.columns(5)
    kpi_card(r1[0], "Avg EV Price",    f"Rs {avg_price/1e5:.2f}L",   "Lakhs INR")
    kpi_card(r1[1], "Median Price",    f"Rs {med_price/1e5:.2f}L",   "Lakhs INR")
    kpi_card(r1[2], "Avg Range",       f"{avg_range:.0f} mi",         "miles / charge")
    kpi_card(r1[3], "Avg Battery",     f"{avg_bat:.1f} kWh",          "capacity")
    kpi_card(r1[4], "Total Sales",     f"{total_sales/1e6:.2f}M",     "annual units")

    r2 = st.columns(5)
    kpi_card(r2[0], "Price / kWh",     f"Rs {avg_ppkwh:,.0f}",        "INR per kWh")
    kpi_card(r2[1], "Range / Rs 10K",  f"{avg_r10k:.3f} mi",          "miles per Rs 10,000")
    kpi_card(r2[2], "Avg Rating",      f"{avg_rating:.2f} / 10",      "customer score")
    kpi_card(r2[3], "Avg Safety",      f"{avg_safety:.2f} / 5",       "safety stars")
    kpi_card(r2[4], "Avg Charging",    f"{avg_chg:.0f} kW",           "avg charge speed")

    c1, c2 = st.columns(2)

    seg_counts = df["market_segment"].value_counts().reset_index()
    seg_counts.columns = ["Segment", "Count"]
    fig_seg = px.pie(seg_counts, names="Segment", values="Count",
                     title="Records by Market Segment", hole=0.45,
                     color_discrete_sequence=COLOR_SEQ)
    c1.plotly_chart(fig_style(fig_seg, 380), use_container_width=True)

    country_counts = df["country_of_origin"].value_counts().reset_index()
    country_counts.columns = ["Country", "Count"]
    fig_ctry = px.bar(country_counts, x="Country", y="Count", color="Country",
                      title="Records by Country of Origin",
                      color_discrete_sequence=COLOR_SEQ)
    c2.plotly_chart(fig_style(fig_ctry, 380), use_container_width=True)

    section("Price & Range Distribution")
    c3, c4 = st.columns(2)

    fig_ph = px.histogram(df, x=df["price_inr"] / 1e5, nbins=35, title="Price Distribution (Rs Lakhs)",
                          labels={"x": "Price (Rs Lakhs)"}, color_discrete_sequence=[ACCENT])
    fig_ph.update_xaxes(title="Price (Rs Lakhs)")
    c3.plotly_chart(fig_style(fig_ph, 360), use_container_width=True)

    fig_rh = px.histogram(df, x="range_miles", nbins=35, title="Range Distribution (miles)",
                          labels={"range_miles": "Range (miles)"}, color_discrete_sequence=["#a78bfa"])
    c4.plotly_chart(fig_style(fig_rh, 360), use_container_width=True)


# ===========================================================================
# TAB 1 — Sales Analysis
# ===========================================================================
with tabs[1]:
    section("Annual Sales Analysis")

    brand_sales = df.groupby("brand")["annual_sales_units"].sum().sort_values(ascending=False).reset_index()
    fig_bs = px.bar(brand_sales, x="brand", y="annual_sales_units", color="brand",
                    title="Total Annual Sales by Brand",
                    labels={"annual_sales_units": "Annual Sales", "brand": "Brand"},
                    color_discrete_sequence=COLOR_SEQ)
    st.plotly_chart(fig_style(fig_bs, 430), use_container_width=True)

    c1, c2 = st.columns(2)

    yr_sales = df.groupby("year")["annual_sales_units"].sum().reset_index()
    fig_yr = px.line(yr_sales, x="year", y="annual_sales_units", markers=True,
                     title="Annual Sales Trend by Model Year",
                     labels={"annual_sales_units": "Sales Units", "year": "Year"},
                     color_discrete_sequence=[ACCENT])
    fig_yr.update_traces(line_width=3, marker_size=9)
    c1.plotly_chart(fig_style(fig_yr, 380), use_container_width=True)

    seg_sales = df.groupby("market_segment")["annual_sales_units"].sum().reset_index()
    fig_ss = px.pie(seg_sales, names="market_segment", values="annual_sales_units", hole=0.4,
                    title="Sales Share by Market Segment", color_discrete_sequence=COLOR_SEQ)
    c2.plotly_chart(fig_style(fig_ss, 380), use_container_width=True)

    section("Top 15 EV Models by Annual Sales")
    top15 = df.groupby(["brand", "model"])["annual_sales_units"].sum().sort_values(ascending=False).head(15).reset_index()
    top15["label"] = top15["brand"] + "  " + top15["model"]
    fig_top = px.bar(top15, x="annual_sales_units", y="label", orientation="h",
                     title="Top 15 EV Models by Annual Sales",
                     labels={"annual_sales_units": "Annual Sales", "label": ""},
                     color="annual_sales_units", color_continuous_scale="Blues")
    fig_top.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_style(fig_top, 520), use_container_width=True)

    c3, c4 = st.columns(2)
    body_sales = df.groupby("body_type")["annual_sales_units"].sum().sort_values(ascending=False).reset_index()
    fig_body = px.bar(body_sales, x="body_type", y="annual_sales_units", color="body_type",
                      title="Sales by Body Type",
                      labels={"annual_sales_units": "Sales", "body_type": "Body Type"},
                      color_discrete_sequence=COLOR_SEQ)
    c3.plotly_chart(fig_style(fig_body, 360), use_container_width=True)

    ctry_s = df.groupby("country_of_origin")["annual_sales_units"].sum().reset_index()
    fig_cs = px.pie(ctry_s, names="country_of_origin", values="annual_sales_units", hole=0.4,
                    title="Sales Share by Country", color_discrete_sequence=COLOR_SEQ)
    c4.plotly_chart(fig_style(fig_cs, 360), use_container_width=True)


# ===========================================================================
# TAB 2 — Price Analysis
# ===========================================================================
with tabs[2]:
    section("Price Analysis — All values in Rs INR")

    c1, c2 = st.columns(2)
    bp = df.groupby("brand")["price_inr"].mean().sort_values(ascending=False).reset_index()
    bp["price_lakh"] = bp["price_inr"] / 1e5
    fig_bp = px.bar(bp, x="brand", y="price_lakh", color="brand",
                    title="Average EV Price by Brand (Rs Lakhs)",
                    labels={"price_lakh": "Avg Price (Rs Lakhs)", "brand": "Brand"},
                    color_discrete_sequence=COLOR_SEQ)
    c1.plotly_chart(fig_style(fig_bp, 400), use_container_width=True)

    dbox = df.copy(); dbox["price_lakh"] = dbox["price_inr"] / 1e5
    fig_box = px.box(dbox, x="market_segment", y="price_lakh", color="market_segment",
                     title="Price Distribution by Segment (Rs Lakhs)",
                     labels={"price_lakh": "Price (Rs Lakhs)", "market_segment": "Segment"},
                     color_discrete_sequence=COLOR_SEQ)
    c2.plotly_chart(fig_style(fig_box, 400), use_container_width=True)

    section("Price vs Range Scatter")
    ds = df.copy(); ds["price_lakh"] = ds["price_inr"] / 1e5
    fig_sc = px.scatter(ds, x="price_lakh", y="range_miles",
                        color="market_segment", size="annual_sales_units",
                        hover_data=["brand", "model", "year", "battery_capacity_kwh"],
                        title="Price (Rs Lakhs) vs Range (miles) — bubble = annual sales",
                        labels={"price_lakh": "Price (Rs Lakhs)", "range_miles": "Range (miles)"},
                        color_discrete_sequence=COLOR_SEQ, size_max=30)
    st.plotly_chart(fig_style(fig_sc, 480), use_container_width=True)

    c3, c4 = st.columns(2)
    ppkwh = df.groupby("brand")["price_per_kwh_inr"].mean().sort_values(ascending=False).reset_index()
    fig_ppkwh = px.bar(ppkwh, x="brand", y="price_per_kwh_inr", color="brand",
                       title="Average Price per kWh by Brand (Rs/kWh)",
                       labels={"price_per_kwh_inr": "Rs/kWh", "brand": "Brand"},
                       color_discrete_sequence=COLOR_SEQ)
    c3.plotly_chart(fig_style(fig_ppkwh, 400), use_container_width=True)

    fig_bat_p = px.scatter(ds, x="battery_capacity_kwh", y="price_lakh", color="brand",
                           hover_data=["model", "year"],
                           title="Battery Capacity vs Price (Rs Lakhs)",
                           labels={"battery_capacity_kwh": "Battery (kWh)", "price_lakh": "Price (Rs Lakhs)"},
                           color_discrete_sequence=COLOR_SEQ)
    c4.plotly_chart(fig_style(fig_bat_p, 400), use_container_width=True)

    section("Avg Price Heatmap — Brand x Year (Rs Lakhs)")
    pivot = df.pivot_table(values="price_inr", index="brand", columns="year", aggfunc="mean") / 1e5
    fig_heat = px.imshow(pivot.round(1), title="Avg Price (Rs Lakhs) — Brand x Year",
                         color_continuous_scale="Blues", aspect="auto", text_auto=True)
    fig_heat.update_layout(coloraxis_colorbar_title="Rs Lakhs")
    st.plotly_chart(fig_style(fig_heat, 560), use_container_width=True)


# ===========================================================================
# TAB 3 — Technology
# ===========================================================================
with tabs[3]:
    section("Battery & Technology Analysis")

    c1, c2 = st.columns(2)
    fig_bat_hist = px.histogram(df, x="battery_capacity_kwh", nbins=28, color="market_segment",
                                title="Battery Capacity Distribution (kWh)",
                                labels={"battery_capacity_kwh": "Battery (kWh)"},
                                color_discrete_sequence=COLOR_SEQ, barmode="overlay", opacity=0.8)
    c1.plotly_chart(fig_style(fig_bat_hist, 380), use_container_width=True)

    fig_chg_hist = px.histogram(df, x="charging_speed_kw", nbins=28, color="market_segment",
                                title="Charging Speed Distribution (kW)",
                                labels={"charging_speed_kw": "Charging Speed (kW)"},
                                color_discrete_sequence=COLOR_SEQ, barmode="overlay", opacity=0.8)
    c2.plotly_chart(fig_style(fig_chg_hist, 380), use_container_width=True)

    c3, c4 = st.columns(2)
    ap = df["autopilot_level"].value_counts().reset_index()
    ap.columns = ["level", "count"]
    ap_map = {0: "L0 - No Assist", 1: "L1 - Driver Assist", 2: "L2 - Partial Auto", 3: "L3 - Conditional"}
    ap["label"] = ap["level"].map(ap_map).fillna("L3+")
    fig_ap = px.pie(ap, names="label", values="count", hole=0.45,
                    title="Autopilot Level Distribution", color_discrete_sequence=COLOR_SEQ)
    c3.plotly_chart(fig_style(fig_ap, 380), use_container_width=True)

    dt = df["drive_type"].value_counts().reset_index(); dt.columns = ["drive_type", "count"]
    fig_dt = px.pie(dt, names="drive_type", values="count", hole=0.45,
                    title="Drive Type Distribution", color_discrete_sequence=COLOR_SEQ)
    c4.plotly_chart(fig_style(fig_dt, 380), use_container_width=True)

    section("Battery Capacity vs Range")
    fig_rb = px.scatter(df, x="battery_capacity_kwh", y="range_miles", color="brand",
                        size="annual_sales_units",
                        hover_data=["model", "year", "drive_type"],
                        title="Battery Capacity (kWh) vs Range (miles)",
                        labels={"battery_capacity_kwh": "Battery (kWh)", "range_miles": "Range (miles)"},
                        color_discrete_sequence=COLOR_SEQ, trendline="ols",
                        trendline_color_override="#ffd700")
    st.plotly_chart(fig_style(fig_rb, 460), use_container_width=True)

    section("Average Battery Capacity by Brand")
    bat_brand = df.groupby("brand")["battery_capacity_kwh"].mean().sort_values(ascending=False).reset_index()
    fig_bb = px.bar(bat_brand, x="brand", y="battery_capacity_kwh", color="brand",
                    title="Average Battery Capacity by Brand (kWh)",
                    labels={"battery_capacity_kwh": "Avg Battery (kWh)", "brand": "Brand"},
                    color_discrete_sequence=COLOR_SEQ)
    st.plotly_chart(fig_style(fig_bb, 380), use_container_width=True)


# ===========================================================================
# TAB 4 — Performance
# ===========================================================================
with tabs[4]:
    section("Performance Analysis")

    r1 = st.columns(5)
    kpi_card(r1[0], "Max Horsepower",   f"{df['horsepower'].max():.0f} HP",          "peak power")
    kpi_card(r1[1], "Avg Horsepower",   f"{df['horsepower'].mean():.0f} HP",          "average power")
    kpi_card(r1[2], "Fastest 0-60",     f"{df['acceleration_0_60_mph'].min():.2f} s", "seconds")
    kpi_card(r1[3], "Avg Top Speed",    f"{df['top_speed_mph'].mean():.0f} mph",       "average")
    kpi_card(r1[4], "Avg Torque",       f"{df['torque_nm'].mean():.0f} Nm",            "average")

    c1, c2 = st.columns(2)
    top_hp = df.nlargest(15, "horsepower")[["brand", "model", "year", "horsepower"]].copy()
    top_hp["label"] = top_hp["brand"] + " " + top_hp["model"] + " (" + top_hp["year"].astype(str) + ")"
    fig_hp = px.bar(top_hp, x="horsepower", y="label", orientation="h", color="horsepower",
                    title="Top 15 EVs by Horsepower",
                    labels={"horsepower": "Horsepower (HP)", "label": ""},
                    color_continuous_scale="Reds")
    fig_hp.update_layout(yaxis={"categoryorder": "total ascending"})
    c1.plotly_chart(fig_style(fig_hp, 500), use_container_width=True)

    top_ac = df.nsmallest(15, "acceleration_0_60_mph")[["brand", "model", "year", "acceleration_0_60_mph", "horsepower"]].copy()
    top_ac["label"] = top_ac["brand"] + " " + top_ac["model"] + " (" + top_ac["year"].astype(str) + ")"
    fig_ac = px.bar(top_ac, x="acceleration_0_60_mph", y="label", orientation="h",
                    color="acceleration_0_60_mph",
                    title="Top 15 Fastest EVs (0-60 mph)",
                    labels={"acceleration_0_60_mph": "0-60 mph (seconds)", "label": ""},
                    color_continuous_scale="Greens_r")
    fig_ac.update_layout(yaxis={"categoryorder": "total descending"})
    c2.plotly_chart(fig_style(fig_ac, 500), use_container_width=True)

    section("Horsepower vs Price Scatter")
    dp = df.copy(); dp["price_lakh"] = dp["price_inr"] / 1e5
    fig_hpp = px.scatter(dp, x="horsepower", y="price_lakh", color="market_segment",
                         size="annual_sales_units", hover_data=["brand", "model", "year"],
                         title="Horsepower vs Price (Rs Lakhs)",
                         labels={"horsepower": "Horsepower (HP)", "price_lakh": "Price (Rs Lakhs)"},
                         color_discrete_sequence=COLOR_SEQ)
    st.plotly_chart(fig_style(fig_hpp, 460), use_container_width=True)

    c3, c4 = st.columns(2)
    fig_ts = px.histogram(df, x="top_speed_mph", nbins=22, color="drive_type",
                          title="Top Speed Distribution (mph)",
                          labels={"top_speed_mph": "Top Speed (mph)"},
                          color_discrete_sequence=COLOR_SEQ, barmode="overlay", opacity=0.8)
    c3.plotly_chart(fig_style(fig_ts, 360), use_container_width=True)

    fig_tq = px.scatter(df, x="horsepower", y="torque_nm", color="drive_type",
                        hover_data=["brand", "model"],
                        title="Horsepower vs Torque (Nm)",
                        labels={"horsepower": "HP", "torque_nm": "Torque (Nm)"},
                        color_discrete_sequence=COLOR_SEQ)
    c4.plotly_chart(fig_style(fig_tq, 360), use_container_width=True)


# ===========================================================================
# TAB 5 — Customer & Safety
# ===========================================================================
with tabs[5]:
    section("Customer & Safety Analysis")

    c1, c2 = st.columns(2)
    cb = df.groupby("brand")["customer_rating"].mean().sort_values(ascending=False).reset_index()
    fig_cr = px.bar(cb, x="brand", y="customer_rating", color="brand",
                    title="Average Customer Rating by Brand (out of 10)",
                    labels={"customer_rating": "Avg Rating", "brand": "Brand"},
                    color_discrete_sequence=COLOR_SEQ)
    fig_cr.update_layout(yaxis_range=[0, cb["customer_rating"].max() * 1.15])
    c1.plotly_chart(fig_style(fig_cr, 400), use_container_width=True)

    sc = df["safety_rating"].value_counts().sort_index().reset_index(); sc.columns = ["rating", "count"]
    fig_sf = px.bar(sc, x="rating", y="count", color="rating",
                    title="Safety Rating Distribution (Stars)",
                    labels={"rating": "Safety Rating", "count": "Count"},
                    color_continuous_scale="Greens")
    c2.plotly_chart(fig_style(fig_sf, 400), use_container_width=True)

    section("Rating vs Price & Sales")
    dcr = df.copy(); dcr["price_lakh"] = dcr["price_inr"] / 1e5
    fig_rp = px.scatter(dcr, x="price_lakh", y="customer_rating", color="market_segment",
                        size="annual_sales_units", hover_data=["brand", "model", "year"],
                        title="Price (Rs Lakhs) vs Customer Rating",
                        labels={"price_lakh": "Price (Rs Lakhs)", "customer_rating": "Customer Rating"},
                        color_discrete_sequence=COLOR_SEQ, trendline="ols",
                        trendline_color_override="#ffd700")
    st.plotly_chart(fig_style(fig_rp, 460), use_container_width=True)

    c3, c4 = st.columns(2)
    wc = df["warranty_years"].value_counts().sort_index().reset_index(); wc.columns = ["years", "count"]
    fig_wc = px.bar(wc, x="years", y="count", color="years",
                    title="Warranty Years Distribution",
                    labels={"years": "Warranty (years)", "count": "Count"},
                    color_continuous_scale="Purples")
    c3.plotly_chart(fig_style(fig_wc, 360), use_container_width=True)

    fig_ss2 = px.scatter(df, x="safety_rating", y="customer_rating", color="market_segment",
                         size="annual_sales_units", hover_data=["brand", "model"],
                         title="Safety Rating vs Customer Rating",
                         labels={"safety_rating": "Safety Rating", "customer_rating": "Customer Rating"},
                         color_discrete_sequence=COLOR_SEQ)
    c4.plotly_chart(fig_style(fig_ss2, 360), use_container_width=True)

    section("Top 10 Highest-Rated EV Models")
    top_rated = (
        df.groupby(["brand", "model"])
        .agg(avg_rating=("customer_rating", "mean"), avg_safety=("safety_rating", "mean"),
             avg_price_lakh=("price_inr", lambda x: round(x.mean() / 1e5, 2)),
             total_sales=("annual_sales_units", "sum"))
        .sort_values("avg_rating", ascending=False).head(10).reset_index()
    )
    top_rated.columns = ["Brand", "Model", "Avg Rating", "Avg Safety", "Avg Price (Rs L)", "Total Sales"]
    st.dataframe(
        top_rated.style.background_gradient(subset=["Avg Rating", "Avg Safety"], cmap="Greens"),
        use_container_width=True, height=380,
    )


# ===========================================================================
# TAB 6 — Country Analysis
# ===========================================================================
with tabs[6]:
    section("Country of Origin Analysis")

    cg = (
        df.groupby("country_of_origin")
        .agg(brands=("brand", "nunique"), models=("model", "nunique"),
             avg_price_lakh=("price_inr", lambda x: round(x.mean() / 1e5, 2)),
             avg_range=("range_miles", "mean"), avg_battery=("battery_capacity_kwh", "mean"),
             total_sales=("annual_sales_units", "sum"), avg_rating=("customer_rating", "mean"),
             count=("country_of_origin", "count"))
        .round(2).sort_values("total_sales", ascending=False).reset_index()
    )

    c1, c2 = st.columns(2)
    fig_cts = px.bar(cg, x="country_of_origin", y="total_sales", color="country_of_origin",
                     title="Total Annual Sales by Country",
                     labels={"total_sales": "Total Sales", "country_of_origin": "Country"},
                     color_discrete_sequence=COLOR_SEQ)
    c1.plotly_chart(fig_style(fig_cts, 380), use_container_width=True)

    fig_ctp = px.bar(cg, x="country_of_origin", y="avg_price_lakh", color="country_of_origin",
                     title="Average Price by Country (Rs Lakhs)",
                     labels={"avg_price_lakh": "Avg Price (Rs L)", "country_of_origin": "Country"},
                     color_discrete_sequence=COLOR_SEQ)
    c2.plotly_chart(fig_style(fig_ctp, 380), use_container_width=True)

    section("Country Summary Table")
    disp = cg.rename(columns={
        "country_of_origin": "Country", "brands": "Brands", "models": "Models",
        "avg_price_lakh": "Avg Price (Rs L)", "avg_range": "Avg Range (mi)",
        "avg_battery": "Avg Battery (kWh)", "total_sales": "Total Sales",
        "avg_rating": "Avg Rating", "count": "Records",
    })
    st.dataframe(disp.style.background_gradient(subset=["Total Sales"], cmap="Blues"),
                 use_container_width=True, height=280)

    c3, c4 = st.columns(2)
    scs = df.groupby(["country_of_origin", "market_segment"])["annual_sales_units"].sum().reset_index()
    fig_scs = px.bar(scs, x="country_of_origin", y="annual_sales_units", color="market_segment",
                     title="Sales by Country & Segment",
                     labels={"annual_sales_units": "Annual Sales", "country_of_origin": "Country"},
                     color_discrete_sequence=COLOR_SEQ, barmode="stack")
    c3.plotly_chart(fig_style(fig_scs, 380), use_container_width=True)

    fig_crng = px.bar(cg.sort_values("avg_range", ascending=False), x="country_of_origin", y="avg_range",
                      color="country_of_origin", title="Average Range by Country (miles)",
                      labels={"avg_range": "Avg Range (mi)", "country_of_origin": "Country"},
                      color_discrete_sequence=COLOR_SEQ)
    c4.plotly_chart(fig_style(fig_crng, 380), use_container_width=True)


# ===========================================================================
# TAB 7 — EV Comparison Table
# ===========================================================================
with tabs[7]:
    section("EV Comparison Table")
    st.caption("Use the sidebar filters to narrow down. Search any field below.")

    display_cols = [
        "brand", "model", "year", "variant", "market_segment",
        "price_usd", "price_inr", "battery_capacity_kwh", "range_miles",
        "charging_speed_kw", "acceleration_0_60_mph", "top_speed_mph",
        "horsepower", "torque_nm", "drive_type", "body_type",
        "seating_capacity", "safety_rating", "customer_rating",
        "annual_sales_units", "country_of_origin",
        "price_per_kwh_inr", "range_per_kwh", "range_per_10k_inr",
    ]
    avail = [c for c in display_cols if c in df.columns]
    dd = df[avail].copy()
    dd["price_usd"] = dd["price_usd"].map(lambda x: f"${x:,.0f}")
    dd["price_inr"] = dd["price_inr"].map(lambda x: f"Rs {x:,.0f}")
    dd["price_per_kwh_inr"] = dd["price_per_kwh_inr"].map(lambda x: f"Rs {x:,.0f}")

    rename_map = {
        "brand": "Brand", "model": "Model", "year": "Year", "variant": "Variant",
        "market_segment": "Segment", "price_usd": "Price (USD)", "price_inr": "Price (INR)",
        "battery_capacity_kwh": "Battery (kWh)", "range_miles": "Range (mi)",
        "charging_speed_kw": "Charge (kW)", "acceleration_0_60_mph": "0-60 (s)",
        "top_speed_mph": "Top Speed (mph)", "horsepower": "HP", "torque_nm": "Torque (Nm)",
        "drive_type": "Drive", "body_type": "Body", "seating_capacity": "Seats",
        "safety_rating": "Safety", "customer_rating": "Rating",
        "annual_sales_units": "Sales/yr", "country_of_origin": "Country",
        "price_per_kwh_inr": "Rs/kWh", "range_per_kwh": "mi/kWh",
        "range_per_10k_inr": "mi/Rs10K",
    }
    dd.rename(columns=rename_map, inplace=True)

    search = st.text_input("🔍 Search brand, model, variant, country ...", "")
    if search.strip():
        mask = dd.apply(lambda col: col.astype(str).str.contains(search.strip(), case=False, na=False)).any(axis=1)
        dd = dd[mask]

    st.markdown(f"**Showing {len(dd):,} records**")
    st.dataframe(dd, use_container_width=True, height=620)

    csv_bytes = df[avail].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️  Download Filtered Data as CSV",
        data=csv_bytes,
        file_name="ev_market_filtered.csv",
        mime="text/csv",
    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class='footer'>
        ⚡ EV Market Analysis 2026 &nbsp;|&nbsp;
        All prices in &#8377; INR (1 USD = &#8377;{USD_TO_INR:,.2f}) &nbsp;|&nbsp;
        Dataset: ev_market_2026.csv &nbsp;|&nbsp;
        Built with Python · Pandas · Plotly · Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
