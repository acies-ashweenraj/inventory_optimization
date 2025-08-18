# ui/pages/4_Cost_Comparison.py
import streamlit as st
import pandas as pd
import plotly.express as px
import os

from server.cost_comparison.prepare_dashboard import load_cost_dashboard_data
from server.config import cost_path

st.set_page_config(page_title="MEIO vs Non-MEIO Cost Comparison", layout="wide")
st.title("📊 MEIO vs Non-MEIO Cost Comparison")

# ----------------------------
# Load
# ----------------------------
with st.spinner("Loading dashboard data..."):
    df = load_cost_dashboard_data()

# Preserve only SKUs that exist (already filtered in backend, but double-safety)
df["SKU"] = df["SKU"].astype(str).str.upper()

# Build a robust total for UI selection
candidate_costs = [c for c in ["HoldingCost","OrderingCost","TransportCost","InventoryValue","TotalCost"] if c in df.columns]
if "TotalCost" not in candidate_costs:
    df["TotalCost"] = df[[c for c in candidate_costs if c != "TotalCost"]].select_dtypes(include="number").sum(axis=1)
    candidate_costs = ["TotalCost"] + [c for c in candidate_costs if c != "TotalCost"]

# Derive time if missing
if "Year" in df.columns and "Month" in df.columns and "YearMonth" not in df.columns:
    df["YearMonth"] = df["Year"].astype(str) + "-" + df["Month"].astype(str).str.zfill(2)

# Harmonize echelon column for UI expectations
if "Echelon_Type" not in df.columns and "Echelon" in df.columns:
    df["Echelon_Type"] = df["Echelon"]

# ----------------------------
# Sidebar Filters
# ----------------------------
st.sidebar.header("🔍 Filters")

# Cost metric picker
metric = st.sidebar.selectbox(
    "Cost Metric",
    options=candidate_costs,
    index=0
)

# Policy
policies = sorted(df["Policy"].dropna().unique().tolist())
sel_policies = st.sidebar.multiselect("Policy", policies, default=policies)

# Echelon
if "Echelon_Type" in df.columns:
    echelons = sorted(df["Echelon_Type"].dropna().unique().tolist())
    sel_echelon = st.sidebar.multiselect("Echelon", echelons, default=echelons)
else:
    sel_echelon = []

# Nodes
if "Node" in df.columns:
    nodes = sorted(df["Node"].dropna().unique().tolist())
    sel_nodes = st.sidebar.multiselect("Nodes", nodes, default=nodes)
else:
    sel_nodes = []

# SKUs
skus = sorted(df["SKU"].dropna().unique().tolist())
sel_skus = st.sidebar.multiselect("SKUs", skus, default=skus)

# Time range (YearMonth)
if "YearMonth" in df.columns:
    ym_sorted = sorted(df["YearMonth"].dropna().unique().tolist())
    sel_ym = st.sidebar.multiselect("Year-Month", ym_sorted, default=ym_sorted)
else:
    sel_ym = []

# Apply filters
mask = df["Policy"].isin(sel_policies)
if sel_echelon:
    mask &= df["Echelon_Type"].isin(sel_echelon)
if sel_nodes:
    mask &= df["Node"].isin(sel_nodes)
if sel_skus:
    mask &= df["SKU"].isin(sel_skus)
if sel_ym:
    mask &= df["YearMonth"].isin(sel_ym)

f = df[mask].copy()

# ----------------------------
# KPIs
# ----------------------------
st.subheader("📌 KPI Summary")

tot_meio = f.loc[f["Policy"]=="MEIO", metric].sum()
tot_non  = f.loc[f["Policy"]=="Non-MEIO", metric].sum()
savings  = tot_non - tot_meio
savings_pct = (savings / tot_non * 100) if tot_non else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Total {metric} (MEIO)", f"{tot_meio:,.2f}")
c2.metric(f"Total {metric} (Non-MEIO)", f"{tot_non:,.2f}")
c3.metric("Absolute Savings", f"{savings:,.2f}")
c4.metric("Savings %", f"{savings_pct:,.2f}%")

# ----------------------------
# Charts
# ----------------------------
st.markdown("---")
st.subheader(f"🏢 Echelon-wise {metric} (Grouped)")

if "Echelon_Type" in f.columns:
    g_ech = f.groupby(["Echelon_Type","Policy"], as_index=False)[metric].sum()
    fig1 = px.bar(g_ech, x="Echelon_Type", y=metric, color="Policy", barmode="group")
    st.plotly_chart(fig1, use_container_width=True)

st.subheader(f"🎯 SKU-wise {metric} (Top 20 by Non-MEIO)")
g_sku = f.groupby(["SKU","Policy"], as_index=False)[metric].sum()
# reindex to show top by Non-MEIO for clear comparison
top_skus = (
    g_sku[g_sku["Policy"]=="Non-MEIO"]
    .nlargest(20, metric)["SKU"]
    .tolist()
)
g_sku_top = g_sku[g_sku["SKU"].isin(top_skus)]
fig2 = px.bar(g_sku_top, x="SKU", y=metric, color="Policy", barmode="group")
fig2.update_layout(xaxis={"type": "category"})
st.plotly_chart(fig2, use_container_width=True)

if "YearMonth" in f.columns:
    st.subheader(f"⏳ Monthly Trend of {metric}")
    g_time = f.groupby(["YearMonth","Policy"], as_index=False)[metric].sum().sort_values("YearMonth")
    fig3 = px.line(g_time, x="YearMonth", y=metric, color="Policy", markers=True)
    st.plotly_chart(fig3, use_container_width=True)

# Savings treemap by Echelon → SKU
st.subheader("🧭 Savings Treemap (Non-MEIO − MEIO)")
# build savings at SKU level within echelon
piv = (
    f.pivot_table(index=["Echelon_Type","SKU"], columns="Policy", values=metric, aggfunc="sum")
    .fillna(0.0)
    .reset_index()
)
if "MEIO" in piv.columns and "Non-MEIO" in piv.columns:
    piv["Savings"] = piv["Non-MEIO"] - piv["MEIO"]
    fig4 = px.treemap(
        piv,
        path=["Echelon_Type", "SKU"],
        values="Savings",
        color="Savings",
        color_continuous_scale="Tealgrn",
        title="Savings by Echelon and SKU"
    )
    st.plotly_chart(fig4, use_container_width=True)

# Waterfall of component savings (if components exist)
comp_cols = [c for c in ["HoldingCost","OrderingCost","TransportCost"] if c in f.columns]
if comp_cols:
    st.subheader("🏗️ Savings Waterfall by Components")
    comp = {}
    for c in comp_cols:
        comp[c] = f.loc[f["Policy"]=="Non-MEIO", c].sum() - f.loc[f["Policy"]=="MEIO", c].sum()
    wf = pd.DataFrame({"Component": list(comp.keys()), "Savings": list(comp.values())})
    wf_sorted = wf.sort_values("Savings", ascending=False)
    # build waterfall-like bar
    fig5 = px.bar(wf_sorted, x="Component", y="Savings", color="Savings", color_continuous_scale="Bluered")
    st.plotly_chart(fig5, use_container_width=True)

# Optional: Node map if you have geo columns
if {"Latitude","Longitude"}.issubset(f.columns):
    st.subheader("🗺️ Node Savings Map")
    # aggregate savings per node
    pn = (
        f.pivot_table(index=["Node","Latitude","Longitude"], columns="Policy", values=metric, aggfunc="sum")
        .fillna(0.0)
        .reset_index()
    )
    if "MEIO" in pn.columns and "Non-MEIO" in pn.columns:
        pn["Savings"] = pn["Non-MEIO"] - pn["MEIO"]
        fig6 = px.scatter_mapbox(
            pn, lat="Latitude", lon="Longitude", size="Savings", color="Savings",
            hover_name="Node", mapbox_style="carto-positron", zoom=1, height=500
        )
        st.plotly_chart(fig6, use_container_width=True)

# ----------------------------
# Table & Download
# ----------------------------
st.markdown("---")
st.subheader("📑 Filtered Detailed Data")
st.dataframe(f, use_container_width=True)

dl_name = f"dashboard_costs_filtered_{metric}.csv"
st.download_button("⬇️ Download filtered CSV", data=f.to_csv(index=False).encode("utf-8"), file_name=dl_name, mime="text/csv")

# Quick link to the full prepared file
st.caption(f"Source: {os.path.join(cost_path, 'dashboard_costs.xlsx')}")
