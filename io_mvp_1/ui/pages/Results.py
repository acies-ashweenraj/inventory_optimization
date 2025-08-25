# import streamlit as st
# import pandas as pd
# import os
# import io

# st.set_page_config(page_title="Distribution & Schedule Results", layout="wide")

# # Paths to distribution and scheduling results
# BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# OUTPUT_DATA_PATH = os.path.join(BASE_PATH, "output_data")

# DISTRIBUTION_FILES = {
#     "DC → Warehouse Distribution": os.path.join(OUTPUT_DATA_PATH, "distribution", "dc_warehouse_distribution_df.xlsx"),
#     "Warehouse → Store Distribution": os.path.join(OUTPUT_DATA_PATH, "distribution", "warehouse_store_distribution_df.xlsx")
# }

# SCHEDULING_FILES = {
#     "Store Order Schedule": os.path.join(OUTPUT_DATA_PATH, "schedule_data", "stores_order_schedule.xlsx"),
#     "Warehouse Order Schedule": os.path.join(OUTPUT_DATA_PATH, "schedule_data", "warehouses_order_schedule.xlsx")
# }

# def load_excel(path):
#     try:
#         return pd.read_excel(path, engine="openpyxl")
#     except Exception as e:
#         st.error(f"Failed to load file: {e}")
#         return None

# def display_section(title, files_dict):
#     st.header(title)
#     selected = st.selectbox(f"Select {title.lower()} file:", list(files_dict.keys()), key=title)

#     file_path = files_dict[selected]
#     if not os.path.exists(file_path):
#         st.error(f"⚠️ File not found: {file_path}")
#         return

#     df = load_excel(file_path)
#     if df is not None:
#         st.dataframe(df, use_container_width=True)

#         # Save to BytesIO for download
#         buffer = io.BytesIO()
#         with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
#             df.to_excel(writer, index=False)
#         buffer.seek(0)

#         st.download_button(
#             label="Download Excel",
#             data=buffer,
#             file_name=os.path.basename(file_path),
#             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#         )

# def results_page():
#     st.title("MEIO Results – Distribution & Scheduling")

#     # Display Distribution Section
#     display_section("Distribution Results", DISTRIBUTION_FILES)

#     st.markdown("---")

#     # Display Scheduling Section
#     display_section("Scheduling Results", SCHEDULING_FILES)

# if __name__ == "__main__":
#     results_page()


import streamlit as st
import pandas as pd
import os
import io
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Distribution & Schedule Results", layout="wide")

# ------------------------------
# Paths
# ------------------------------
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DATA_PATH = os.path.join(BASE_PATH, "output_data")

DISTRIBUTION_FILES = {
    "DC → Warehouse Distribution": os.path.join(OUTPUT_DATA_PATH, "distribution", "dc_warehouse_distribution_df.xlsx"),
    "Warehouse → Store Distribution": os.path.join(OUTPUT_DATA_PATH, "distribution", "warehouse_store_distribution_df.xlsx"),
}

SCHEDULING_FILES = {
    "Warehouse Order Schedule": os.path.join(OUTPUT_DATA_PATH, "schedule_data", "warehouses_order_schedule.xlsx"),
    "Store Order Schedule": os.path.join(OUTPUT_DATA_PATH, "schedule_data", "stores_order_schedule.xlsx"),
}

# ------------------------------
# IO
# ------------------------------
def load_excel(path: str) -> pd.DataFrame | None:
    try:
        return pd.read_excel(path, engine="openpyxl")
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return None

# ------------------------------
# Time utilities
# ------------------------------
TIME_OPTIONS = [
    "Last 2 weeks",
    "Last 1 month",
    "Last 1 quarter (3 months)",
    "Last 6 months",
    "Last 1 year",
    "All time",
]

def detect_datetime_col(df: pd.DataFrame) -> str | None:
    dt_cols = df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns.tolist()
    if dt_cols:
        return dt_cols[0]
    candidates = [c for c in df.columns if isinstance(c, str)]
    common = ["order_date", "date", "schedule_date", "planned_date", "dispatch_date", "arrival_date"]
    for key in common:
        col = next((c for c in candidates if key in c.lower().replace(" ", "").replace("-", "")), None)
        if col:
            try:
                df[col] = pd.to_datetime(df[col], errors="raise")
                return col
            except Exception:
                pass
    for c in candidates:
        try:
            parsed = pd.to_datetime(df[c], errors="raise")
            if parsed.notna().mean() >= 0.8:
                df[c] = parsed
                return c
        except Exception:
            continue
    return None

def ensure_month_date(df: pd.DataFrame) -> str | None:
    if {"Year", "Month"}.issubset(df.columns):
        try:
            temp = pd.to_datetime(df["Year"].astype(int).astype(str) + "-" + df["Month"].astype(int).astype(str) + "-01")
            df["period_date"] = temp
            return "period_date"
        except Exception:
            return None
    return None

def apply_time_filter(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    date_col = detect_datetime_col(df)
    monthly_only = False
    if date_col is None:
        date_col = ensure_month_date(df)
        monthly_only = date_col is not None
    if date_col is None:
        return df
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df[df[date_col].notna()]
    if df.empty:
        return df
    end = df[date_col].max()
    chosen = mode
    if monthly_only and mode == "Last 2 weeks":
        st.caption("ℹ️ Data is monthly; using 1 month for the 'Last 2 weeks' selection.")
        chosen = "Last 1 month"
    if chosen == "Last 2 weeks":
        start = end - pd.Timedelta(days=14)
    elif chosen == "Last 1 month":
        start = end - pd.DateOffset(months=1)
    elif chosen == "Last 1 quarter (3 months)":
        start = end - pd.DateOffset(months=3)
    elif chosen == "Last 6 months":
        start = end - pd.DateOffset(months=6)
    elif chosen == "Last 1 year":
        start = end - pd.DateOffset(years=1)
    elif chosen == "All time":
        start = df[date_col].min()
    else:
        start = df[date_col].min()
    return df[(df[date_col] >= start) & (df[date_col] <= end)]

# ------------------------------
# Distribution visuals
# ------------------------------
def show_dc_wh_sankey(df: pd.DataFrame):
    required = {"DC", "Warehouse", "Warehouse_Monthly_Demand"}
    if not required.issubset(df.columns):
        st.info("Expected columns not found for DC → Warehouse Sankey.")
        return
    g = df.groupby(["DC", "Warehouse"])["Warehouse_Monthly_Demand"].sum().reset_index()
    nodes = sorted(set(g["DC"]).union(set(g["Warehouse"])))
    idx = {n: i for i, n in enumerate(nodes)}
    sources = g["DC"].map(idx)
    targets = g["Warehouse"].map(idx)
    values  = g["Warehouse_Monthly_Demand"]
    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=14, thickness=18, line=dict(color="black", width=0.5), label=nodes),
        link=dict(source=sources, target=targets, value=values),
    )])
    fig.update_layout(title_text="DC → Warehouse Flow (Monthly Demand)", font_size=12, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

def show_dc_wh_heatmap(df: pd.DataFrame):
    required = {"DC", "Warehouse", "Warehouse_Monthly_Demand"}
    if not required.issubset(df.columns):
        return
    pivot = df.pivot_table(index="DC", columns="Warehouse", values="Warehouse_Monthly_Demand", aggfunc="sum", fill_value=0)
    if pivot.empty:
        st.info("No data to display in heatmap.")
        return
    fig = px.imshow(pivot, aspect="auto")
    fig.update_layout(title="DC ↔ Warehouse Heatmap (Monthly Demand)", margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

def show_wh_store_sankey(df: pd.DataFrame):
    """
    Generates and displays a Sankey diagram for Warehouse to Store flow.

    It now checks for "store_total_stock" as a priority, followed by other
    demand-related columns.

    Args:
        df (pd.DataFrame): The input DataFrame containing distribution data.
    """
    demand_col = None
    for cand in ["store_total_stock", "Quantity", "Demand", "Monthly_Demand", "Store_Monthly_Demand"]:
        if cand in df.columns:
            demand_col = cand
            break

    if demand_col is None or not {"Warehouse", "Store"}.issubset(df.columns):
        st.info("Expected columns not found for Warehouse → Store Sankey.")
        return

    g = df.groupby(["Warehouse", "Store"])[demand_col].sum().reset_index()
    nodes = sorted(set(g["Warehouse"]).union(set(g["Store"])))
    idx = {n: i for i, n in enumerate(nodes)}
    sources = g["Warehouse"].map(idx)
    targets = g["Store"].map(idx)
    values = g[demand_col]

    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=14, thickness=18, line=dict(color="black", width=0.5), label=nodes),
        link=dict(source=sources, target=targets, value=values),
    )])
    fig.update_layout(title_text=f"Warehouse → Store Flow ({demand_col})", font_size=12, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)


def show_wh_store_heatmap(df: pd.DataFrame):
    """
    Generates and displays a heatmap for Warehouse to Store demand.

    It checks for "Store_Monthly_Demand" and other demand-related columns
    to use for the heatmap values.

    Args:
        df (pd.DataFrame): The input DataFrame containing distribution data.
    """
    demand_col = None
    for cand in ["Store_Monthly_Demand", "Quantity", "Demand", "Monthly_Demand", "Warehouse_Store_Demand"]:
        if cand in df.columns:
            demand_col = cand
            break

    if demand_col is None or not {"Warehouse", "Store"}.issubset(df.columns):
        st.info("Expected columns not found for Warehouse → Store Heatmap.")
        return

    pivot = df.pivot_table(index="Warehouse", columns="Store", values=demand_col, aggfunc="sum", fill_value=0)
    
    if pivot.empty:
        st.info("No data to display in heatmap.")
        return

    fig = px.imshow(pivot, aspect="auto")
    fig.update_layout(title=f"Warehouse ↔ Store Heatmap ({demand_col})", margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------
# Filters
# ------------------------------
DISTRO_FILTER_WHITELIST = ["Year", "Month", "DC", "Warehouse", "Store", "ItemStat_Item"]
SCHED_FILTER_WHITELIST = ["Year", "Month", "DC", "Warehouse", "Store", "SKU", "Route_ID"]

def render_filters(df: pd.DataFrame, whitelist: list[str], key_prefix: str) -> pd.DataFrame:
    st.subheader("Filters")
    filtered = df.copy()

    # Apply time filter first if applicable
    if "Year" in whitelist and "Month" in whitelist:
        selection = st.selectbox("Time range", TIME_OPTIONS, index=5, key=f"{key_prefix}_time_filter")
        filtered = apply_time_filter(filtered, selection)

    # Now filter by other columns
    usable_cols = [c for c in whitelist if c in filtered.columns and c not in ["Year", "Month"]]

    # Use a single column layout for simplicity
    for colname in usable_cols:
        unique_vals = pd.Series(filtered[colname].dropna().unique()).sort_values().tolist()
        if len(unique_vals) > 0 and len(unique_vals) <= 200:
            options = ["All"] + unique_vals
            chosen = st.multiselect(f"Select {colname}", options, default=["All"], key=f"{key_prefix}_{colname}")
            
            if "All" not in chosen:
                filtered = filtered[filtered[colname].isin(chosen)]

    with st.expander("View Filtered Data"):
        st.dataframe(filtered, use_container_width=True)
        
    return filtered

# ------------------------------
# Section view
# ------------------------------
def display_section(title: str, files_dict: dict, is_distribution: bool = False):
    st.header(title)
    selected_key = st.selectbox(f"Select {title.lower()} file:", list(files_dict.keys()), key=f"{title}_selectfile")

    file_path = files_dict[selected_key]
    if not os.path.exists(file_path):
        st.error(f"⚠️ File not found: {file_path}")
        return

    df = load_excel(file_path)
    if df is None or df.empty:
        st.warning("No data found in the file.")
        return

    tab1, tab2 = st.tabs(["📊 Data, Filters & Visuals", "📥 Download"])

    with tab1:
        key_prefix = selected_key.replace(" ", "_")
        if is_distribution:
            filtered_df = render_filters(df, DISTRO_FILTER_WHITELIST, key_prefix)
        else:
            filtered_df = render_filters(df, SCHED_FILTER_WHITELIST, key_prefix)
        
        # This section was previously in tab2
        selection_viz = st.selectbox("Time range (visuals)", TIME_OPTIONS, index=5, key=f"{selected_key}_viz_time")
        viz_df = apply_time_filter(filtered_df, selection_viz)
        if is_distribution:
            if selected_key == "DC → Warehouse Distribution":
                show_dc_wh_sankey(viz_df)
                show_dc_wh_heatmap(viz_df)
            elif selected_key == "Warehouse → Store Distribution":
                show_wh_store_sankey(viz_df)
                show_wh_store_heatmap(viz_df)
        else:
            st.subheader("Scheduling Trends")
            date_col = detect_datetime_col(viz_df)
            if date_col:
                series = viz_df.groupby(viz_df[date_col].dt.date).size().reset_index(name="Orders")
                fig = px.line(series, x=date_col, y="Orders", title=f"Orders Over Time ({date_col})")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No datetime-like column found to visualize scheduling trends.")

    with tab2:
        st.subheader("Download Options")
        filtered_buffer = io.BytesIO()
        with pd.ExcelWriter(filtered_buffer, engine="openpyxl") as writer:
            filtered_df.to_excel(writer, index=False)
        filtered_buffer.seek(0)
        st.download_button(
            label="⬇️ Download Current View (Excel)",
            data=filtered_buffer,
            file_name=f"filtered_{os.path.basename(file_path)}",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        full_buffer = io.BytesIO()
        with pd.ExcelWriter(full_buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        full_buffer.seek(0)
        st.download_button(
            label="⬇️ Download Original Excel",
            data=full_buffer,
            file_name=os.path.basename(file_path),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ------------------------------
# Main
# ------------------------------
def results_page():
    st.title("📦 MEIO Results – Distribution & Scheduling")
    display_section("Distribution Results", DISTRIBUTION_FILES, is_distribution=True)
    st.markdown("---")
    display_section("Scheduling Results", SCHEDULING_FILES, is_distribution=False)

if __name__ == "__main__":
    results_page()
