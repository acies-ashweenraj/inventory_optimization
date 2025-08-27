import streamlit as st
import pandas as pd
import os
import io
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

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
# IO & Data Preprocessing
# ------------------------------
def load_excel(path: str) -> pd.DataFrame | None:
    """Loads an Excel file from the given path."""
    try:
        return pd.read_excel(path, engine="openpyxl")
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return None

def preprocess_dates(df: pd.DataFrame) -> tuple[pd.DataFrame, str | None]:
    """
    Detects and standardizes datetime columns, or creates one from 'Year' and 'Month'.
    Returns the processed DataFrame and the name of the datetime column.
    """
    df = df.copy()
    
    # 1. Look for existing datetime columns
    dt_cols = df.select_dtypes(include=["datetime64[ns]", "datetime64[ns, UTC]"]).columns.tolist()
    if dt_cols:
        return df, dt_cols[0]
    
    # 2. Look for common date-like column names and convert them
    candidates = [c for c in df.columns if isinstance(c, str)]
    common = ["order_date", "date", "schedule_date", "planned_date", "dispatch_date", "arrival_date", "date_time"]
    for key in common:
        col = next((c for c in candidates if key in c.lower().replace(" ", "").replace("-", "")), None)
        if col:
            try:
                df[col] = pd.to_datetime(df[col], errors="raise")
                return df, col
            except Exception:
                pass
    
    # 3. Handle 'Year' and 'Month' by combining them
    if {"Year", "Month"}.issubset(df.columns):
        try:
            # Drop NaN from Year and Month before converting
            df.dropna(subset=["Year", "Month"], inplace=True)
            df['combined_date'] = pd.to_datetime(
                df["Year"].astype(int).astype(str) + "-" + 
                df["Month"].astype(int).astype(str) + "-01",
                errors="coerce"
            )
            df.dropna(subset=["combined_date"], inplace=True) # drop rows where date conversion failed
            return df, "combined_date"
        except Exception:
            pass

    # 4. Fallback to trying to parse any other string column
    for c in candidates:
        try:
            parsed = pd.to_datetime(df[c], errors="raise")
            if parsed.notna().mean() >= 0.8: # Require at least 80% valid dates
                df[c] = parsed
                return df, c
        except Exception:
            continue
    
    return df, None

def apply_date_range_filter(df: pd.DataFrame, date_col: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Applies a date range filter to the DataFrame."""
    df_filtered = df.copy()
    df_filtered[date_col] = pd.to_datetime(df_filtered[date_col], errors="coerce")
    df_filtered = df_filtered[df_filtered[date_col].notna()]
    if df_filtered.empty:
        return df_filtered
    
    return df_filtered[(df_filtered[date_col].dt.date >= start_date) & (df_filtered[date_col].dt.date <= end_date)]

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

    # Create pivot table
    pivot = df.pivot_table(index="DC", columns="Warehouse",
                           values="Warehouse_Monthly_Demand",
                           aggfunc="sum", fill_value=0)
    if pivot.empty:
        st.info("No data to display in heatmap.")
        return

    total_demand = pivot.values.sum()
    if total_demand == 0:
        st.info("Total demand is zero, cannot calculate percentages.")
        return

    # Prepare x, y, z
    x = pivot.columns.tolist()
    y = pivot.index.tolist()
    z = pivot.values  # actual values for hover
    z_percent = (z / total_demand) * 100  # percentage for text display

    text_labels = [[f"{val:.1f}%" for val in row] for row in z_percent]

    fig = go.Figure(
        data=go.Heatmap(
            z=z,  # actual values drive color intensity
            x=x,
            y=y,
            colorscale="Blues",
            text=text_labels,  # percentage text inside tiles
            texttemplate="%{text}",
            textfont={"size": 12, "color": "black"},
            hovertemplate="DC: %{y}<br>Warehouse: %{x}<br>Demand: %{z}<extra></extra>"
        )
    )

    fig.update_layout(
        title="DC ↔ Warehouse Heatmap (Demand % of Total)",
        xaxis_title="Warehouse",
        yaxis_title="DC",
        margin=dict(l=10, r=10, t=40, b=10)
    )

    st.plotly_chart(fig, use_container_width=True)

def show_wh_store_sankey(df: pd.DataFrame):
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
    demand_col = None
    for cand in ["Store_Monthly_Demand", "Quantity", "Demand", "Monthly_Demand", "Warehouse_Store_Demand"]:
        if cand in df.columns:
            demand_col = cand
            break
    if demand_col is None or not {"Warehouse", "Store"}.issubset(df.columns):
        st.info("Expected columns not found for Warehouse → Store Heatmap.")
        return

    # Pivot data
    pivot = df.pivot_table(index="Warehouse", columns="Store", values=demand_col, aggfunc="sum", fill_value=0)
    if pivot.empty:
        st.info("No data to display in heatmap.")
        return

    # Calculate percentage for display
    total_demand = pivot.values.sum()
    percent_matrix = (pivot / total_demand * 100).round(1)

    # Prepare x, y, z for Heatmap
    x = pivot.columns.tolist()
    y = pivot.index.tolist()
    z_actual = pivot.values
    z_percent = percent_matrix.values

    fig = go.Figure(
        data=go.Heatmap(
            z=z_percent,
            x=x,
            y=y,
            colorscale="Greens",
            text=[[f"{val:.1f}%" for val in row] for row in z_percent],  # Show % inside tile
            texttemplate="%{text}",
            textfont={"size": 12, "color": "black"},
            hovertemplate="Warehouse: %{y}<br>Store: %{x}<br>Demand: %{customdata}<extra></extra>",
            customdata=z_actual  # Hover shows actual demand
        )
    )

    fig.update_layout(
        title=f"Warehouse ↔ Store Heatmap ({demand_col})",
        xaxis_title="Store",
        yaxis_title="Warehouse",
        margin=dict(l=10, r=10, t=40, b=10)
    )

    st.plotly_chart(fig, use_container_width=True)



# def show_demand_over_time_line_chart(df: pd.DataFrame, demand_col: str):
#     df, date_col = preprocess_dates(df)
#     if date_col is None or demand_col not in df.columns:
#         return
#     df_agg = df.groupby(pd.Grouper(key=date_col, freq='M'))[demand_col].sum().reset_index()
#     fig = px.line(df_agg, x=date_col, y=demand_col, title=f"{demand_col} Over Time")
#     st.plotly_chart(fig, use_container_width=True)

def show_monthly_eoq_bar_chart(df: pd.DataFrame):
    if "monthly_eoq" not in df.columns or "ItemStat_Item" not in df.columns:
        return
    g = df.groupby("ItemStat_Item")["monthly_eoq"].sum().reset_index()
    fig = px.bar(g, x="ItemStat_Item", y="monthly_eoq", title="Monthly Economic Order Quantity (EOQ) by Item")
    st.plotly_chart(fig, use_container_width=True)


# ------------------------------
# Scheduling visuals
# ------------------------------

def show_orders_by_route(df: pd.DataFrame):
    if "Route_ID" not in df.columns:
        st.info("Expected column 'Route_ID' not found for orders by route chart.")
        return
    g = df["Route_ID"].value_counts().reset_index()
    g.columns = ["Route_ID", "Order_Count"]
    fig = px.pie(g, values="Order_Count", names="Route_ID", title="Order Distribution by Route")
    st.plotly_chart(fig, use_container_width=True)

def show_orders_by_echelon(df: pd.DataFrame):
    if "Echelon" not in df.columns:
        st.info("Expected column 'Echelon' not found for orders by echelon chart.")
        return
    g = df["Echelon"].value_counts().reset_index()
    g.columns = ["Echelon", "Order_Count"]
    fig = px.pie(g, values="Order_Count", names="Echelon", title="Order Distribution by Echelon")
    st.plotly_chart(fig, use_container_width=True)


def show_quantity_over_time(df: pd.DataFrame):
    df, date_col = preprocess_dates(df)
    if date_col is None or "Quantity" not in df.columns:
        st.info("Expected columns 'Quantity' and a datetime column not found.")
        return
    df_agg = df.groupby(pd.Grouper(key=date_col, freq='D'))["Quantity"].sum().reset_index()
    fig = px.line(df_agg, x=date_col, y="Quantity", title="Total Quantity Over Time")
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------
# Filters
# ------------------------------
DISTRO_FILTER_WHITELIST = ["DC", "Warehouse", "Store", "ItemStat_Item"]
SCHED_FILTER_WHITELIST = ["From", "Echelon", "SKU", "Route_ID"]

def render_filters(df: pd.DataFrame, whitelist: list[str], key_prefix: str) -> pd.DataFrame:
    st.subheader("Filters")
    filtered = df.copy()

    usable_cols = [c for c in whitelist if c in filtered.columns]
    
    # Use columns to put filters on a single line
    cols = st.columns(len(usable_cols))
    
    for i, colname in enumerate(usable_cols):
        with cols[i]:
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

    # Create 3 columns for file selector, timeframe display, and date range input
    col1, col2, col3 = st.columns([2, 2, 3])

    # File selector
    with col1:
        selected_key = st.selectbox(
            f"Select {title.lower()} file:", 
            list(files_dict.keys()), 
            key=f"{title}_selectfile"
        )

    file_path = files_dict[selected_key]
    if not os.path.exists(file_path):
        st.error(f"⚠️ File not found: {file_path}")
        return

    df, date_col = preprocess_dates(load_excel(file_path))
    if df is None or df.empty:
        st.warning("No data found in the file.")
        return

    # Show timeframe and date range picker on the same line
    if date_col:
        min_date = pd.to_datetime(df[date_col].min()).date()
        max_date = pd.to_datetime(df[date_col].max()).date()

        

        with col2:
            start_date, end_date = st.date_input(
                "Select a date range",
                [min_date, max_date],
                key=f"{title}_date_range"
            )
            filtered_df_by_date = apply_date_range_filter(df, date_col, start_date, end_date)
    else:
        st.info("No datetime column to filter by.")
        filtered_df_by_date = df
# def display_section(title: str, files_dict: dict, is_distribution: bool = False):
#     st.header(title)
    
#     col1, col2 = st.columns(2)
#     with col1:
#         selected_key = st.selectbox(f"Select {title.lower()} file:", list(files_dict.keys()), key=f"{title}_selectfile")
    
#     file_path = files_dict[selected_key]
#     if not os.path.exists(file_path):
#         st.error(f"⚠️ File not found: {file_path}")
#         return

#     # Load data and preprocess dates in one go to ensure all subsequent uses get the correct DataFrame
#     df, date_col = preprocess_dates(load_excel(file_path))

#     if df is None or df.empty:
#         st.warning("No data found in the file.")
#         return
    
#     with col2:
#         if date_col:
#             # Display overall date range for user information
#             min_date = pd.to_datetime(df[date_col].min()).date()
#             max_date = pd.to_datetime(df[date_col].max()).date()
#             st.markdown(f"**Overall Timeframe:** `{min_date}` to `{max_date}`")

#             start_date, end_date = st.date_input(
#                 "Select a date range",
#                 [min_date, max_date],
#                 key=f"{title}_date_range"
#             )
#             filtered_df_by_date = apply_date_range_filter(df, date_col, start_date, end_date)
#         else:
#             st.info("No datetime column to filter by.")
#             filtered_df_by_date = df
    
    tab1, tab2 = st.tabs(["📊 Data, Filters & Visuals", "📥 Download"])

    with tab1:
        key_prefix = selected_key.replace(" ", "_")
        if is_distribution:
            final_filtered_df = render_filters(filtered_df_by_date, DISTRO_FILTER_WHITELIST, key_prefix)
        else:
            final_filtered_df = render_filters(filtered_df_by_date, SCHED_FILTER_WHITELIST, key_prefix)
        
        st.subheader("Visualizations")
        
        if is_distribution:
            if selected_key == "DC → Warehouse Distribution":
                col_viz1, col_viz2 = st.columns(2)
                
                show_dc_wh_sankey(final_filtered_df)
                
                show_dc_wh_heatmap(final_filtered_df)
            elif selected_key == "Warehouse → Store Distribution":
                col_viz1, col_viz2 = st.columns(2)
                show_wh_store_sankey(final_filtered_df)
                
                show_wh_store_heatmap(final_filtered_df)
                

        else: # Scheduling
            col_viz3, col_viz4 = st.columns(2)
            
            show_orders_by_echelon(final_filtered_df)
            show_quantity_over_time(final_filtered_df)

    with tab2:
        st.subheader("Download Options")
        filtered_buffer = io.BytesIO()
        with pd.ExcelWriter(filtered_buffer, engine="openpyxl") as writer:
            final_filtered_df.to_excel(writer, index=False)
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


    # (KEEP your existing tabs, filters, visualizations, and download buttons here)

