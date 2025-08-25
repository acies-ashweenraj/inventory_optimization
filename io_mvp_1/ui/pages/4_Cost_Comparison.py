import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# ======================================================
# Page Config
# ======================================================
st.set_page_config(
    page_title="MEIO vs Non-MEIO Cost Comparison",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ======================================================
# Paths / Constants
# ======================================================
CURRENT_DIR = os.path.dirname(__file__)
DEFAULT_DATA_PATH = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "..", "server", "multi_level_cost_comparison.xlsx")
)

NUMERIC_COLS = [
    "Demand","Product_Cost","Ordering_Cost","Holding_Cost_per_unit","EOQ",
    "EOQ_Ordering_Cost","EOQ_Holding_Cost","EOQ_Total_Cost",
    "NonEOQ_Ordering_Cost","NonEOQ_Holding_Cost","NonEOQ_Total_Cost","Cost_Savings",
]
TOLERANCE = 0.01

# ======================================================
# Utilities
# ======================================================
@st.cache_data
def load_data(path: str) -> pd.DataFrame | None:
    if os.path.exists(path):
        return pd.read_excel(path)
    return None

def ensure_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "SKU" in df: df["SKU"] = df["SKU"].astype(str)  # ✅ make categorical
    if "Echelon" in df: df["Echelon"] = df["Echelon"].astype(str)
    for c in NUMERIC_COLS:
        if c in df: df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def recompute_costs(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["EOQ_Total_Cost"] = df["EOQ_Ordering_Cost"].fillna(0)+df["EOQ_Holding_Cost"].fillna(0)
    df["NonEOQ_Total_Cost"] = df["NonEOQ_Ordering_Cost"].fillna(0)+df["NonEOQ_Holding_Cost"].fillna(0)
    df["Cost_Savings"] = df["NonEOQ_Total_Cost"].fillna(0)-df["EOQ_Total_Cost"].fillna(0)
    df["Savings_Rate"] = (df["Cost_Savings"]/df["NonEOQ_Total_Cost"].replace(0,np.nan)).fillna(0)
    for c in ["EOQ_Total_Cost","NonEOQ_Total_Cost","Cost_Savings"]:
        df[c] = df[c].round(2)
    df["Savings_Rate"] = df["Savings_Rate"].round(4)
    return df

def agg_by_echelon(df):
    g = df.groupby("Echelon", as_index=False).agg(
        EOQ_Total_Cost=("EOQ_Total_Cost","sum"),
        NonEOQ_Total_Cost=("NonEOQ_Total_Cost","sum"),
        Cost_Savings=("Cost_Savings","sum"),
        Avg_EOQ=("EOQ","mean"),
        SKUs=("SKU","nunique"),
    )
    g["Savings_Rate"] = g["Cost_Savings"]/g["NonEOQ_Total_Cost"].replace(0,np.nan)
    return g.sort_values("Cost_Savings",ascending=False)

def agg_by_sku(df):
    g = df.groupby("SKU", as_index=False).agg(
        EOQ_Total_Cost=("EOQ_Total_Cost","sum"),
        NonEOQ_Total_Cost=("NonEOQ_Total_Cost","sum"),
        Cost_Savings=("Cost_Savings","sum"),
        Avg_EOQ=("EOQ","mean"),
        Echelons=("Echelon","nunique"),
    )
    g["Savings_Rate"] = g["Cost_Savings"]/g["NonEOQ_Total_Cost"].replace(0,np.nan)
    return g.sort_values("Cost_Savings",ascending=False)

def fmt_money(v: float) -> str:
    return f"₹{v:,.2f}"

# ======================================================
# Styles
# ======================================================
# st.markdown("""
# <style>
# .kpi-row {display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 15px 0 18px;}
# .kpi-card {
#     border:1px solid rgba(255,255,255,0.15);
#     background:rgba(30,30,30,0.7);
#     padding:12px;
#     border-radius:10px;
#     box-shadow:0 2px 4px rgba(0,0,0,0.3);
#     transition: all 0.2s ease-in-out;
# }
# .kpi-card:hover {background:rgba(60,60,60,0.85);}
# .kpi-title {font-size:0.8rem; color:rgba(255,255,255,0.65);}
# .kpi-value {font-size:1.2rem; font-weight:700; line-height:1.2;}
# .kpi-sub {font-size:0.75rem; color:rgba(255,255,255,0.55);}
# </style>
# """, unsafe_allow_html=True)

# def kpi_card(title, value, sub=""):
#     st.markdown(f"""
#     <div class="kpi-card">
#       <div class="kpi-title">{title}</div>
#       <div class="kpi-value">{value}</div>
#       {'<div class="kpi-sub">'+sub+'</div>' if sub else ''}
#     </div>""", unsafe_allow_html=True)

# Styles
# ======================================================
st.markdown("""
<style>
.kpi-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin: 20px 0 25px;
}

.kpi-card {
    border: none;
    background: linear-gradient(145deg, rgba(45,45,45,0.95), rgba(25,25,25,0.9));
    padding: 18px 14px;
    border-radius: 16px;
    box-shadow: 0 6px 12px rgba(0,0,0,0.35);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.45);
    background: linear-gradient(145deg, rgba(55,55,55,0.95), rgba(30,30,30,0.9));
}

.kpi-title {
    font-size: 0.9rem;
    color: rgba(255,255,255,0.7);
    margin-bottom: 4px;
    font-weight: 500;
}

.kpi-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 6px;
    line-height: 1.2;
}

.kpi-sub {
    font-size: 0.8rem;
    color: rgba(255,255,255,0.6);
    font-style: italic;
}
</style>
""", unsafe_allow_html=True)


def kpi_card(title, value, sub=""):
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-title">{title}</div>
      <div class="kpi-value">{value}</div>
      {'<div class="kpi-sub">'+sub+'</div>' if sub else ''}
    </div>""", unsafe_allow_html=True)


# ======================================================
# Data
# ======================================================
st.title("📊 Inventory Cost Comparison Dashboard")

df = load_data(DEFAULT_DATA_PATH)
if df is None:
    uploaded = st.file_uploader("Upload cost summary Excel", type=["xlsx"])
    if uploaded: df = pd.read_excel(uploaded)
    else: st.stop()

df = ensure_types(df)
df = recompute_costs(df)

# ======================================================
# Global Filters
# ======================================================
st.markdown("### 🔎 Global Filters")

echelons = sorted(df["Echelon"].unique())
skus = sorted(df["SKU"].unique())

col1, col2, col3 = st.columns([2,4,1])
sel_ech = col1.multiselect("Select Echelons", echelons, default=echelons)
sel_skus = col2.multiselect("Select SKUs", skus, default=skus)
top_n = col3.number_input("Top N SKUs",5,50,20)

fdf = df[df["Echelon"].isin(sel_ech) & df["SKU"].isin(sel_skus)]

if fdf.empty: st.warning("No data after filters"); st.stop()

# ======================================================
# Tabs
# ======================================================
tabs = st.tabs(["📌 KPIs Overview","📈 Charts & Visuals","📑 Summaries","📂 Detailed Data"])

# --- KPIs ---
with tabs[0]:
    st.markdown("#### Key Metrics")
    total_eoq,total_non,total_sav = fdf["EOQ_Total_Cost"].sum(),fdf["NonEOQ_Total_Cost"].sum(),fdf["Cost_Savings"].sum()
    rate = total_sav/total_non if total_non>0 else 0
    st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
    kpi_card("Total Cost Savings", fmt_money(total_sav), f"{rate:.2%} vs Non-EOQ")
    kpi_card("Total EOQ Cost", fmt_money(total_eoq))
    kpi_card("Total Non-EOQ Cost", fmt_money(total_non))
    kpi_card("Avg EOQ Size", f"{fdf['EOQ'].mean():,.2f} units")
    kpi_card("SKU Count", f"{fdf['SKU'].nunique()}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Charts ---
with tabs[1]:
    st.subheader("EOQ vs Non-EOQ Costs by SKU")
    fig1 = px.bar(
        fdf,
        x="SKU",
        y=["EOQ_Total_Cost","NonEOQ_Total_Cost"],
        barmode="group",
        hover_data=["Echelon"]
    )
    fig1.update_xaxes(type="category")  # ✅ categorical axis
    st.plotly_chart(fig1,use_container_width=True)

    st.subheader("Total Cost Savings by Echelon")
    ech = agg_by_echelon(fdf)
    fig2 = px.bar(ech,x="Echelon",y="Cost_Savings",text_auto=".2s",color="Cost_Savings")
    st.plotly_chart(fig2,use_container_width=True)

    st.subheader(f"Top {top_n} SKUs by Cost Savings")
    sku = agg_by_sku(fdf).head(top_n)
    fig3 = px.bar(
        sku.sort_values("Cost_Savings"),
        x="Cost_Savings",
        y="SKU",
        orientation="h",
        hover_data={"Savings_Rate":":.2%"},
        color="Cost_Savings"
    )
    fig3.update_yaxes(type="category")  # ✅ categorical axis
    st.plotly_chart(fig3,use_container_width=True)

# --- Summaries ---
with tabs[2]:
    colA,colB = st.columns(2)
    with colA:
        st.markdown("**Summary by Echelon**")
        ech = agg_by_echelon(fdf)
        st.dataframe(ech,use_container_width=True)
    with colB:
        st.markdown("**Summary by SKU**")
        sku = agg_by_sku(fdf)
        st.dataframe(sku,use_container_width=True)

# --- Detailed Data ---
with tabs[3]:
    st.subheader("Filtered Dataset")
    st.dataframe(fdf,use_container_width=True)
