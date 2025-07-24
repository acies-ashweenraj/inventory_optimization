import streamlit as st
import pandas as pd
import os
import difflib

st.title("Upload Inventory & Orders Data")

# Sample file paths
sample_order_path = "data/sample_orders.xlsx"
sample_stock_path = "data/sample_master.xlsx"

# Initialize session state for sample
if "use_sample" not in st.session_state:
    st.session_state.use_sample = False

# Expected Columns for Auto-Mapping
expected_orders_cols = {
    "Order Date": ["Order Date", "Date", "Order_Date", "OrderDate"],
    "SKU ID": ["SKU ID", "SKU", "Product Code", "Item Code"],
    "Order Quantity": ["Order Quantity", "Quantity", "Qty", "Order Qty"]
}

expected_stock_cols = {
    "SKU ID": ["SKU ID", "SKU", "Product Code"],
    "SKU Name": ["SKU Name", "Item Name"],
    "Category": ["Category", "Product Category"],
    "Current Stock Quantity": ["Current Stock Quantity", "Stock", "Available Stock"],
    "Unit Price": ["Unit Price", "Price"],
    "Average Lead Time": ["Average Lead Time", "Avg Lead Time", "Lead Time"],
    "Maximum Lead Time": ["Maximum Lead Time", "Max Lead Time"],
    "Units": ["Units", "Nos", "Kg", "Unit Type"],
    "Location": ["Location", "Warehouse", "Site"]
}

def auto_map(col_list, candidates):
    for name in candidates:
        match = difflib.get_close_matches(name, col_list, n=1, cutoff=0.6)
        if match:
            return match[0]
    return None


st.subheader("Step 1: Upload Your Excel Files")

col1, col2 = st.columns(2)
with col1:
    uploaded_orders = st.file_uploader("Upload Past Orders Excel", type=["xlsx"], key="orders")
with col2:
    uploaded_stock = st.file_uploader("Upload Inventory Master Excel", type=["xlsx"], key="stock")


if st.button("Use Sample Data"):
    st.session_state.use_sample = True
    st.success("Sample data selected.")

if st.session_state.use_sample:
    if os.path.exists(sample_order_path) and os.path.exists(sample_stock_path):
        uploaded_orders = sample_order_path
        uploaded_stock = sample_stock_path
    else:
        st.warning("Sample data files not found. Please upload your own files.")
        uploaded_orders = None
        uploaded_stock = None
        st.session_state.use_sample = False # Reset if samples are not found


if uploaded_orders and uploaded_stock:
    try:
        if st.session_state.use_sample: # For sample data, read directly
            df_orders = pd.read_excel(uploaded_orders)
            df_stock = pd.read_excel(uploaded_stock)
        else: # For user uploaded files, uploaded_orders and uploaded_stock are file-like objects
            df_orders = pd.read_excel(uploaded_orders)
            df_stock = pd.read_excel(uploaded_stock)

        order_mappings = {
            k: auto_map(df_orders.columns.tolist(), v) or ""
            for k, v in expected_orders_cols.items()
        }
        stock_mappings = {
            k: auto_map(df_stock.columns.tolist(), v) or ""
            for k, v in expected_stock_cols.items()
        }

        st.markdown("### Auto-Mapped Columns")
        mapping_df = pd.DataFrame({
            "Standard Name": list(order_mappings.keys()) + list(stock_mappings.keys()),
            "Mapped Column": list(order_mappings.values()) + list(stock_mappings.values()),
            "Sheet": ["Orders"] * len(order_mappings) + ["Inventory"] * len(stock_mappings)
        })
        st.dataframe(mapping_df, use_container_width=True)

        st.subheader("Edit Mappings (Optional)")
        with st.expander("Edit Orders Column Mapping"):
            for k in expected_orders_cols:
                current_map = order_mappings[k]
                try:
                    default_index = df_orders.columns.get_loc(current_map) if current_map in df_orders.columns else 0
                except KeyError:
                    default_index = 0 # Fallback if column not found
                order_mappings[k] = st.selectbox(
                    f"Map for: {k}",
                    df_orders.columns,
                    index=default_index,
                    key=f"order_{k}"
                )

        with st.expander("Edit Inventory Column Mapping"):
            for k in expected_stock_cols:
                current_map = stock_mappings[k]
                try:
                    default_index = df_stock.columns.get_loc(current_map) if current_map in df_stock.columns else 0
                except KeyError:
                    default_index = 0 # Fallback if column not found
                stock_mappings[k] = st.selectbox(
                    f"Map for: {k}",
                    df_stock.columns,
                    index=default_index,
                    key=f"stock_{k}"
                )

        if st.button("Submit & Process Data"):
            try:
                orders_df = df_orders[[
                    order_mappings["Order Date"], order_mappings["SKU ID"], order_mappings["Order Quantity"]
                ]].rename(columns={
                    order_mappings["Order Date"]: "Order Date",
                    order_mappings["SKU ID"]: "SKU ID",
                    order_mappings["Order Quantity"]: "Order Quantity"
                })
                orders_df["Order Date"] = pd.to_datetime(orders_df["Order Date"], errors="coerce")

                stock_df = df_stock[[
                    stock_mappings["SKU ID"], stock_mappings["SKU Name"], stock_mappings["Category"],
                    stock_mappings["Current Stock Quantity"], stock_mappings["Unit Price"],
                    stock_mappings["Average Lead Time"], stock_mappings["Maximum Lead Time"],
                    stock_mappings["Units"], stock_mappings["Location"]
                ]].rename(columns={
                    stock_mappings["SKU ID"]: "SKU ID",
                    stock_mappings["SKU Name"]: "SKU Name",
                    stock_mappings["Category"]: "Category",
                    stock_mappings["Current Stock Quantity"]: "Current Stock Quantity",
                    stock_mappings["Unit Price"]: "Unit Price",
                    stock_mappings["Average Lead Time"]: "Average Lead Time",
                    stock_mappings["Maximum Lead Time"]: "Maximum Lead Time",
                    stock_mappings["Units"]: "Units",
                    stock_mappings["Location"]: "Location"
                })

                agg_orders = orders_df.groupby("SKU ID").agg({
                    "Order Quantity": ["sum", "mean", "std"]
                }).reset_index()
                agg_orders.columns = ["SKU ID", "Order Quantity sum", "Order Quantity mean", "Order Quantity std"]

                last_order_df = orders_df.groupby("SKU ID")["Order Date"].max().reset_index(name="Last Order Date")

                def compute_median_days(group):
                    group = group.sort_values("Order Date")
                    group["Days Between Orders"] = group["Order Date"].diff().dt.days
                    return pd.Series({
                        "Median Days Between Orders": group["Days Between Orders"].median()
                    })

                median_days_df = orders_df.groupby("SKU ID").apply(compute_median_days).reset_index()

                merged_df = pd.merge(stock_df, agg_orders, on="SKU ID", how="left")
                merged_df = pd.merge(merged_df, last_order_df, on="SKU ID", how="left")
                merged_df = pd.merge(merged_df, median_days_df, on="SKU ID", how="left")

                merged_df = merged_df.loc[:, ~merged_df.columns.duplicated()]
                merged_df.fillna(0, inplace=True)

                st.session_state["orders_df"] = orders_df
                st.session_state["stock_df"] = stock_df
                st.session_state["merged_df"] = merged_df

                st.success("Data uploaded and processed successfully.")

                with st.expander("See Processed Data (Click to Expand)"):
                    st.dataframe(merged_df, use_container_width=True)

            except Exception as e:
                st.error(f"Error during processing: {e}")

    except Exception as e:
        st.error(f"Error reading uploaded files: {e}")


# --- Step 2: Upload MEIO Data ---
st.subheader("Step 2: Upload MEIO Data")

uploaded_meio_file1 = st.file_uploader("Upload Demand Forecasted Data", type=["xlsx"], key="demand_forecast")
uploaded_meio_file2 = st.file_uploader("Upload Lead Time Data", type=["xlsx"], key="lead_time")
uploaded_meio_file3 = st.file_uploader("Upload Node Data", type=["xlsx"], key="node_data")

meio_dataframes = {}

if uploaded_meio_file1:
    try:
        meio_dataframes["demand_forecast"] = pd.read_excel(uploaded_meio_file1)
    except Exception as e:
        st.error(f"Error reading demand_forecast file: {e}")

if uploaded_meio_file2:
    try:
        meio_dataframes["lead_time"] = pd.read_excel(uploaded_meio_file2)
    except Exception as e:
        st.error(f"Error reading Lead Time: {e}")

if uploaded_meio_file3:
    try:
        meio_dataframes["node_data"] = pd.read_excel(uploaded_meio_file3)
    except Exception as e:
        st.error(f"Error reading Node Data: {e}")

if meio_dataframes:
    st.subheader("MEIO Data Preview")
    selected_meio_file = st.selectbox("Select MEIO File to View", list(meio_dataframes.keys()))
    if selected_meio_file:
        st.dataframe(meio_dataframes[selected_meio_file], use_container_width=True)
else:
    st.info("Upload MEIO files to view their content.")