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

NUMERIC_COLUMNS = [
    "Demand", "Product_Cost", "Ordering_Cost", "Holding_Cost_per_unit", "EOQ",
    "EOQ_Ordering_Cost", "EOQ_Holding_Cost", "EOQ_Total_Cost",
    "NonEOQ_Ordering_Cost", "NonEOQ_Holding_Cost", "NonEOQ_Total_Cost", "Cost_Savings",
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

def ensure_types(input_df: pd.DataFrame) -> pd.DataFrame:
    df_copy = input_df.copy()
    if "SKU" in df_copy:
        df_copy["SKU"] = df_copy["SKU"].astype(str)
    if "Echelon" in df_copy:
        df_copy["Echelon"] = df_copy["Echelon"].astype(str)
    for col in NUMERIC_COLUMNS:
        if col in df_copy:
            df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce")
    return df_copy

def recompute_costs(input_df: pd.DataFrame) -> pd.DataFrame:
    df_copy = input_df.copy()
    df_copy["EOQ_Total_Cost"] = df_copy["EOQ_Ordering_Cost"].fillna(0) + df_copy["EOQ_Holding_Cost"].fillna(0)
    df_copy["NonEOQ_Total_Cost"] = df_copy["NonEOQ_Ordering_Cost"].fillna(0) + df_copy["NonEOQ_Holding_Cost"].fillna(0)
    df_copy["Cost_Savings"] = df_copy["NonEOQ_Total_Cost"].fillna(0) - df_copy["EOQ_Total_Cost"].fillna(0)
    df_copy["Savings_Rate"] = (df_copy["Cost_Savings"] / df_copy["NonEOQ_Total_Cost"].replace(0, np.nan)).fillna(0)
    for col in ["EOQ_Total_Cost", "NonEOQ_Total_Cost", "Cost_Savings"]:
        df_copy[col] = df_copy[col].round(2)
    df_copy["Savings_Rate"] = df_copy["Savings_Rate"].round(4)
    return df_copy

def aggregate_by_echelon(input_df: pd.DataFrame) -> pd.DataFrame:
    aggregated_df = input_df.groupby("Echelon", as_index=False).agg(
        EOQ_Total_Cost=("EOQ_Total_Cost", "sum"),
        NonEOQ_Total_Cost=("NonEOQ_Total_Cost", "sum"),
        Cost_Savings=("Cost_Savings", "sum"),
        Avg_EOQ=("EOQ", "mean"),
        SKUs=("SKU", "nunique"),
    )
    aggregated_df["Savings_Rate"] = aggregated_df["Cost_Savings"] / aggregated_df["NonEOQ_Total_Cost"].replace(0, np.nan)
    return aggregated_df.sort_values("Cost_Savings", ascending=False)

def aggregate_by_sku(input_df: pd.DataFrame) -> pd.DataFrame:
    aggregated_df = input_df.groupby("SKU", as_index=False).agg(
        EOQ_Total_Cost=("EOQ_Total_Cost", "sum"),
        NonEOQ_Total_Cost=("NonEOQ_Total_Cost", "sum"),
        Cost_Savings=("Cost_Savings", "sum"),
        Avg_EOQ=("EOQ", "mean"),
        Echelons=("Echelon", "nunique"),
    )
    aggregated_df["Savings_Rate"] = aggregated_df["Cost_Savings"] / aggregated_df["NonEOQ_Total_Cost"].replace(0, np.nan)
    return aggregated_df.sort_values("Cost_Savings", ascending=False)

def format_money(value: float) -> str:
    return f"₹{value:,.2f}"

# ======================================================
# KPI Card Renderer (simple, no flexbox)
# ======================================================
def kpi_card(title, value, sub=""):
    st.markdown(f"""
        <div style="
            border:1px solid #e0e0e0;
            background:#fff;
            padding:14px 12px;
            border-radius:14px;
            box-shadow:0 2px 6px rgba(0,0,0,0.1);
            text-align:center;
        ">
            <div style="font-size:0.85rem;color:#555;font-weight:600;margin-bottom:4px;">{title}</div>
            <div style="font-size:1.4rem;font-weight:700;color:#222;margin-bottom:4px;">{value}</div>
            {f'<div style="font-size:0.8rem;color:#888;font-style:italic;">{sub}</div>' if sub else ''}
        </div>
    """, unsafe_allow_html=True)

# ======================================================
# Data
# ======================================================
st.title("📊 Inventory Cost Comparison Dashboard")

dataframe = load_data(DEFAULT_DATA_PATH)
if dataframe is None:
    uploaded_file = st.file_uploader("Upload cost summary Excel", type=["xlsx"])
    if uploaded_file:
        dataframe = pd.read_excel(uploaded_file)
    else:
        st.stop()

dataframe = ensure_types(dataframe)
dataframe = recompute_costs(dataframe)

# ======================================================
# Global Filters with Proper Select All
# ======================================================
st.markdown("### 🔎 Global Filters")
col_echelon, col_sku, col_topn_overall = st.columns([2, 3, 2])

# ----------------- Echelon Filter -----------------
with col_echelon:
    st.markdown("**Echelon Filter**")
    with st.expander("Echelon",expanded = False):
        all_echelons = sorted(dataframe["Echelon"].unique())
        select_all_echelons = st.checkbox("Select All Echelons", value=True, key="select_all_echelons")
        selected_echelons = st.multiselect(
            label="",  # no duplicate label
            options=all_echelons,
            default=all_echelons if select_all_echelons else [],
            key="selected_echelons"
        )

# ----------------- SKU Filter -----------------
with col_sku:
    st.markdown("**SKU Filter**")
    with st.expander("SKU",expanded = False):
        all_skus = sorted(dataframe["SKU"].unique())
        select_all_skus = st.checkbox("Select All SKUs", value=True, key="select_all_skus")
        selected_skus = st.multiselect(
            label="",
            options=all_skus,
            default=all_skus if select_all_skus else [],
            key="selected_skus"
        )

# # ----------------- Top N SKUs -----------------
# with col_topn_overall:
#     # st.markdown("**Top N SKUs**")
#     top_n_skus = st.number_input(
#         label="blah",   # hide label
#         min_value=1,
#         max_value=50,
#         value=20,
#         step=0,
#         key="top_n_skus"
#     )

# Filter dataframe
filtered_df = dataframe[
    dataframe["Echelon"].isin(selected_echelons) &
    dataframe["SKU"].isin(selected_skus)
]

if filtered_df.empty:
    st.warning("No data after filters")
    st.stop()

# ======================================================
# Tabs
# ======================================================
tabs = st.tabs(["📌 KPIs Overview", "📈 Charts & Visuals", "📂 Detailed Data"])

# --- KPIs ---
with tabs[0]:
    st.markdown("#### Key Metrics")
    total_eoq_cost = filtered_df["EOQ_Total_Cost"].sum()
    total_noneoq_cost = filtered_df["NonEOQ_Total_Cost"].sum()
    total_savings = filtered_df["Cost_Savings"].sum()
    savings_rate = total_savings / total_noneoq_cost if total_noneoq_cost > 0 else 0

    # Arrange KPI cards in 3 columns
    metrics = [
        ("Total Cost Savings", format_money(total_savings), " "),
        ("Total EOQ Cost", format_money(total_eoq_cost), " "),
        ("Total Non-EOQ Cost", format_money(total_noneoq_cost), " "),
        ("Avg EOQ Size", f"{filtered_df['EOQ'].mean():,.2f} units", " "),
        ("SKU Count", f"{filtered_df['SKU'].nunique()}", " ")
    ]

    for i in range(0, len(metrics), 3):
        col1, col2, col3 = st.columns(3)
        for col, metric in zip([col1, col2, col3], metrics[i:i+3]):
            with col:
                kpi_card(*metric)
        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)

# --- Charts ---
with tabs[1]:
    st.subheader("EOQ vs Non-EOQ Costs by SKU")
    fig_sku = px.bar(
        filtered_df,
        x="SKU",
        y=["EOQ_Total_Cost", "NonEOQ_Total_Cost"],
        barmode="group",
        hover_data=["Echelon"]
    )
    fig_sku.update_xaxes(type="category")
    st.plotly_chart(fig_sku, use_container_width=True)

    st.subheader("Total Cost Savings by Echelon")
    aggregated_echelon_df = aggregate_by_echelon(filtered_df)
    fig_echelon = px.bar(
        aggregated_echelon_df,
        x="Echelon",
        y="Cost_Savings",
        text_auto=".2s",
        color="Cost_Savings"
    )
    st.plotly_chart(fig_echelon, use_container_width=True)

    # st.subheader(f"Top {top_n_skus} SKUs by Cost Savings")
    # aggregated_sku_df = aggregate_by_sku(filtered_df).head(top_n_skus)
    # fig_top_sku = px.bar(
    #     aggregated_sku_df.sort_values("Cost_Savings"),
    #     x="Cost_Savings",
    #     y="SKU",
    #     orientation="h",
    #     hover_data={"Savings_Rate":":.2%"},
    #     color="Cost_Savings"
    # )
    # fig_top_sku.update_yaxes(type="category")
    # st.plotly_chart(fig_top_sku, use_container_width=True)

# --- Detailed Data ---
with tabs[2]:
    st.subheader("Filtered Dataset")
    st.dataframe(filtered_df, use_container_width=True)

    # Download Options
    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download as CSV",
        data=csv_data,
        file_name="detailed_data.csv",
        mime="text/csv",
    )
