import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px
import plotly.graph_objects as go

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
# Default backend output location (adjust if your structure differs)
CURRENT_DIR = os.path.dirname(__file__)
DEFAULT_DATA_PATH = os.path.abspath(
    os.path.join(CURRENT_DIR, "..", "..", "server", "multi_level_cost_comparison.xlsx")
)

NUMERIC_COLS = [
    "Demand",
    "Product_Cost",
    "Ordering_Cost",
    "Holding_Cost_per_unit",
    "EOQ",
    "EOQ_Ordering_Cost",
    "EOQ_Holding_Cost",
    "EOQ_Total_Cost",
    "NonEOQ_Ordering_Cost",
    "NonEOQ_Holding_Cost",
    "NonEOQ_Total_Cost",
    "Cost_Savings",
]
TOLERANCE = 0.01  # ₹0.01 tolerance for floating point sums


# ======================================================
# Utilities
# ======================================================
@st.cache_data
def load_data(default_path: str) -> pd.DataFrame | None:
    """Load cost comparison data from default path; fall back to None if missing."""
    if os.path.exists(default_path):
        try:
            df = pd.read_excel(default_path)
            return df
        except Exception as e:
            st.error(f"Failed to read default file at {default_path}:\n{e}")
            return None
    return None


def ensure_types(df: pd.DataFrame) -> pd.DataFrame:
    """Cast dtypes for safety."""
    df = df.copy()
    if "SKU" in df.columns:
        df["SKU"] = df["SKU"].astype(str)
    if "Echelon" in df.columns:
        df["Echelon"] = df["Echelon"].astype(str)
    for c in NUMERIC_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def recompute_costs(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute totals and savings to guarantee correctness."""
    df = df.copy()

    # Recompute totals from components
    df["EOQ_Total_Cost_calc"] = df["EOQ_Ordering_Cost"].fillna(0) + df["EOQ_Holding_Cost"].fillna(0)
    df["NonEOQ_Total_Cost_calc"] = df["NonEOQ_Ordering_Cost"].fillna(0) + df["NonEOQ_Holding_Cost"].fillna(0)

    # If provided columns deviate beyond tolerance, replace with computed
    def within_tol(a, b, tol):
        mask = a.notna() & b.notna()
        out = pd.Series(False, index=a.index)
        out[mask] = (a[mask] - b[mask]).abs() <= tol
        return out.fillna(False)

    eoq_ok = within_tol(df["EOQ_Total_Cost"], df["EOQ_Total_Cost_calc"], TOLERANCE) if "EOQ_Total_Cost" in df else pd.Series(False, index=df.index)
    noneoq_ok = within_tol(df["NonEOQ_Total_Cost"], df["NonEOQ_Total_Cost_calc"], TOLERANCE) if "NonEOQ_Total_Cost" in df else pd.Series(False, index=df.index)

    # Replace values where needed (or if missing)
    df["EOQ_Total_Cost"] = np.where(eoq_ok, df["EOQ_Total_Cost"], df["EOQ_Total_Cost_calc"])
    df["NonEOQ_Total_Cost"] = np.where(noneoq_ok, df["NonEOQ_Total_Cost"], df["NonEOQ_Total_Cost_calc"])

    # Recompute savings from totals
    df["Cost_Savings"] = df["NonEOQ_Total_Cost"].fillna(0) - df["EOQ_Total_Cost"].fillna(0)

    # Savings Rate (guard divide-by-zero)
    denom = df["NonEOQ_Total_Cost"].replace(0, np.nan)
    df["Savings_Rate"] = (df["Cost_Savings"] / denom).fillna(0.0)

    # Round for neat display (no logic loss beyond a paisa)
    for c in ["EOQ_Total_Cost", "NonEOQ_Total_Cost", "Cost_Savings"]:
        df[c] = df[c].round(2)
    df["Savings_Rate"] = df["Savings_Rate"].round(6)

    return df.drop(columns=["EOQ_Total_Cost_calc", "NonEOQ_Total_Cost_calc"], errors="ignore")


def agg_by_echelon(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("Echelon", as_index=False).agg(
        EOQ_Total_Cost=("EOQ_Total_Cost", "sum"),
        NonEOQ_Total_Cost=("NonEOQ_Total_Cost", "sum"),
        Cost_Savings=("Cost_Savings", "sum"),
        Avg_EOQ=("EOQ", "mean"),
        SKUs=("SKU", "nunique"),
    )
    g["Savings_Rate"] = (g["Cost_Savings"] / g["NonEOQ_Total_Cost"].replace(0, np.nan)).fillna(0.0)
    return g.sort_values("Cost_Savings", ascending=False)


def agg_by_sku(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("SKU", as_index=False).agg(
        EOQ_Total_Cost=("EOQ_Total_Cost", "sum"),
        NonEOQ_Total_Cost=("NonEOQ_Total_Cost", "sum"),
        Cost_Savings=("Cost_Savings", "sum"),
        Avg_EOQ=("EOQ", "mean"),
        Echelons=("Echelon", "nunique"),
    )
    g["Savings_Rate"] = (g["Cost_Savings"] / g["NonEOQ_Total_Cost"].replace(0, np.nan)).fillna(0.0)
    return g.sort_values(["Cost_Savings", "Savings_Rate"], ascending=[False, False])


def fmt_money(v: float) -> str:
    return f"₹{v:,.2f}"


# ======================================================
# Styles
# ======================================================
CSS = """
<style>
.container-block {margin-bottom: 8px;}

.kpi-row {display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin: 8px 0 18px;}
.kpi-card {border:1px solid rgba(255,255,255,0.10); background:rgba(255,255,255,0.04); padding:14px 16px; border-radius:14px;}
.kpi-title {font-size:0.92rem; color:rgba(255,255,255,0.65); margin-bottom:6px;}
.kpi-value {font-size:1.45rem; font-weight:700; line-height:1.2;}
.kpi-sub {font-size:0.85rem; color:rgba(255,255,255,0.60); margin-top:6px;}

.filter-row {display:grid; grid-template-columns: 2fr 4fr 1fr 1fr; gap: 10px; align-items:end; margin-top:6px;}
.filter-box {border:1px solid rgba(255,255,255,0.10); border-radius:12px; padding:10px 12px;}

table {font-size: 0.92rem;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def kpi_card(title: str, value: str, sub: str = ""):
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-title">{title}</div>
          <div class="kpi-value">{value}</div>
          {'<div class="kpi-sub">'+sub+'</div>' if sub else ''}
        </div>
        """,
        unsafe_allow_html=True
    )


# ======================================================
# Data Ingress
# ======================================================
st.title("Inventory Cost Comparison Dashboard")

df = load_data(DEFAULT_DATA_PATH)

# Optional fallback: let user upload if backend file is missing
if df is None:
    uploaded = st.file_uploader("Upload 'multi_level_cost_comparison.xlsx'", type=["xlsx"])
    if uploaded:
        df = pd.read_excel(uploaded)
    else:
        st.stop()

# Prepare + recompute
df = ensure_types(df)
df = recompute_costs(df)

# ======================================================
# Top Filters
# ======================================================
st.markdown("#### Filters")

# Build options
echelon_options = sorted(df["Echelon"].dropna().unique())
sku_options = sorted(df["SKU"].dropna().unique())

# Session defaults for select-all behavior
if "select_all_skus" not in st.session_state:
    st.session_state.select_all_skus = True

# Filter row (no sidebar)
with st.container():
    col_ech, col_sku, col_topn, col_reset = st.columns([2, 4, 1, 1])
    with col_ech:
        sel_echelons = st.multiselect(
            "Echelon",
            options=echelon_options,
            default=echelon_options,
            placeholder="Select echelons",
        )
    with col_sku:
        sel_all = st.checkbox("Select all SKUs", value=st.session_state.select_all_skus, key="select_all_skus")
        sel_skus = st.multiselect(
            "SKU(s)",
            options=sku_options,
            default=sku_options if sel_all else [],
            placeholder="Select SKUs"
        )
    with col_topn:
        top_n = st.number_input("Top N (SKUs by savings)", min_value=5, max_value=50, value=20, step=1)
    with col_reset:
        if st.button("Reset Filters", use_container_width=True):
            st.session_state.select_all_skus = True
            st.rerun()

# Apply filters
filt = (df["Echelon"].isin(sel_echelons)) & (df["SKU"].isin(sel_skus))
fdf = df.loc[filt].copy()

if fdf.empty:
    st.warning("No data for the current filters.")
    st.stop()

st.markdown("---")

# ======================================================
# KPIs
# ======================================================
total_eoq = float(fdf["EOQ_Total_Cost"].sum())
total_noneoq = float(fdf["NonEOQ_Total_Cost"].sum())
total_sav = float(fdf["Cost_Savings"].sum())
avg_eoq = float(fdf["EOQ"].mean()) if "EOQ" in fdf.columns else 0.0
sku_count = int(fdf["SKU"].nunique())

savings_rate = (total_sav / total_noneoq) if total_noneoq > 0 else 0.0

st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
kpi_card("Total Cost Savings", fmt_money(total_sav), f"{savings_rate:.2%} vs Non‑EOQ")
kpi_card("Total EOQ Cost", fmt_money(total_eoq))
kpi_card("Total Non‑EOQ Cost", fmt_money(total_noneoq))
kpi_card("Average EOQ Order Size", f"{avg_eoq:,.2f} units")
kpi_card("Number of SKUs", f"{sku_count}")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ======================================================
# Charts
# ======================================================
st.subheader("Visual Analysis")

# 1) EOQ vs Non-EOQ Total Cost by SKU (grouped)
st.markdown("**EOQ vs Non‑EOQ Total Cost by SKU (grouped)**")
fig1 = px.bar(
    fdf,
    x="SKU",
    y=["EOQ_Total_Cost", "NonEOQ_Total_Cost"],
    barmode="group",
    hover_data=["Echelon"],
    title="EOQ vs Non‑EOQ Total Cost by SKU (split by Echelon in hover)",
)
fig1.update_layout(xaxis_title="SKU", yaxis_title="Total Cost (₹)")
st.plotly_chart(fig1, use_container_width=True)

# 2) Total Savings by Echelon
st.markdown("**Total Cost Savings by Echelon**")
by_ech = agg_by_echelon(fdf)
fig2 = px.bar(
    by_ech,
    x="Echelon",
    y="Cost_Savings",
    text_auto=".2s",
    title="Total Cost Savings by Echelon",
)
fig2.update_layout(xaxis_title="Echelon", yaxis_title="Cost Savings (₹)")
st.plotly_chart(fig2, use_container_width=True)

# 3) Top-N SKUs by Cost Savings (horizontal)
st.markdown(f"**Top {top_n} SKUs by Cost Savings**")
by_sku = agg_by_sku(fdf)
top_sku = by_sku.head(int(top_n))
fig3 = px.bar(
    top_sku.sort_values("Cost_Savings"),
    x="Cost_Savings",
    y="SKU",
    orientation="h",
    hover_data={"Savings_Rate": ":.2%"},
    text_auto=".2s",
    title=f"Top {len(top_sku)} SKUs by Absolute Cost Savings",
)
fig3.update_layout(xaxis_title="Cost Savings (₹)", yaxis_title="SKU")
st.plotly_chart(fig3, use_container_width=True)

# 4) Waterfall: Non-EOQ Total → EOQ Total via echelon savings
st.markdown("**Cost Bridge (Waterfall): Non‑EOQ → EOQ by Echelon savings**")
echelon_order = by_ech.sort_values("Cost_Savings", ascending=False)["Echelon"].tolist()
wf = go.Figure(go.Waterfall(
    name="Savings",
    orientation="h",
    measure=["absolute"] + ["relative"] * len(echelon_order) + ["total"],
    x=[total_noneoq] + (-by_ech.set_index("Echelon").loc[echelon_order]["Cost_Savings"]).tolist() + [total_eoq],
    y=["Non‑EOQ Total"] + echelon_order + ["EOQ Total"],
))
wf.update_layout(title="Waterfall: Contribution of Echelon Savings", xaxis_title="₹ Amount")
st.plotly_chart(wf, use_container_width=True)

st.markdown("---")

# ======================================================
# Summaries & Downloads
# ======================================================
st.subheader("Summaries")

c_sum1, c_sum2 = st.columns(2)
with c_sum1:
    st.markdown("**Summary by Echelon**")
    st.dataframe(by_ech, use_container_width=True)
    csv1 = by_ech.to_csv(index=False).encode("utf-8")
    st.download_button("Download Echelon Summary (CSV)", data=csv1, file_name="summary_by_echelon.csv", mime="text/csv")

with c_sum2:
    st.markdown("**Summary by SKU**")
    st.dataframe(by_sku, use_container_width=True)
    csv2 = by_sku.to_csv(index=False).encode("utf-8")
    st.download_button("Download SKU Summary (CSV)", data=csv2, file_name="summary_by_sku.csv", mime="text/csv")

st.markdown("---")

st.subheader("Filtered Rows")
st.dataframe(fdf, use_container_width=True)
csv3 = fdf.to_csv(index=False).encode("utf-8")
st.download_button("Download Filtered Data (CSV)", data=csv3, file_name="filtered_cost_comparison.csv", mime="text/csv")

# ======================================================
# Optional Integrity Details (collapsible)
# ======================================================
with st.expander("Data Integrity Checks (optional)"):
    # Recompute one more time to show drift if any (should be zero after recompute)
    check = fdf.copy()
    check["EOQ_calc"] = check["EOQ_Ordering_Cost"].fillna(0) + check["EOQ_Holding_Cost"].fillna(0)
    check["NonEOQ_calc"] = check["NonEOQ_Ordering_Cost"].fillna(0) + check["NonEOQ_Holding_Cost"].fillna(0)
    e_mis = (check["EOQ_Total_Cost"] - check["EOQ_calc"]).abs() > TOLERANCE
    n_mis = (check["NonEOQ_Total_Cost"] - check["NonEOQ_calc"]).abs() > TOLERANCE
    st.write({
        "EOQ_Total_Cost mismatches (>₹0.01)": int(e_mis.sum()),
        "NonEOQ_Total_Cost mismatches (>₹0.01)": int(n_mis.sum()),
    })
