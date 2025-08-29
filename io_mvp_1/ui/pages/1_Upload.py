import streamlit as st
import pandas as pd
import os
import difflib
import sys
import traceback
import io
import time

# ------------------- IMPORT PIPELINE -------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from server.app import run_meio_pipeline

# ------------------- PATH SETUP -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.join(BASE_DIR, "..", "..", "shared_data")
SAMPLE_DIR = os.path.join(BASE_DIR, "..", "..", "server", "data")
os.makedirs(SHARED_DIR, exist_ok=True)

# ------------------- SESSION INIT -------------------
if "use_sample" not in st.session_state:
    st.session_state.use_sample = False
if "upload_status" not in st.session_state:
    st.session_state.upload_status = {
        "Orders": False,
        "Inventory": False,
        "Demand Forecast": False,
        "Lead Time": False,
        "Node Data": False
    }
if "uploaded_dataframes" not in st.session_state:
    st.session_state.uploaded_dataframes = {}
if "file_names" not in st.session_state:
    st.session_state.file_names = {}

# ------------------- FILE PATHS -------------------
sample_file_paths = {
    "Orders": os.path.join(SAMPLE_DIR, "sample_orders.xlsx"),
    "Inventory": os.path.join(SAMPLE_DIR, "sample_master.xlsx"),
    "Demand Forecast": os.path.join(SAMPLE_DIR, "Multi_Sku.xlsx"),
    "Lead Time": os.path.join(SAMPLE_DIR, "Leadtime_MultiSKU.xlsx"),
    "Node Data": os.path.join(SAMPLE_DIR, "Node_Costs.xlsx")
}
shared_save_paths = {
    "Orders": os.path.join(SHARED_DIR, "orders.xlsx"),
    "Inventory": os.path.join(SHARED_DIR, "inventory.xlsx"),
    "Demand Forecast": os.path.join(SHARED_DIR, "demand_forecast.xlsx"),
    "Lead Time": os.path.join(SHARED_DIR, "lead_time.xlsx"),
    "Node Data": os.path.join(SHARED_DIR, "node_data.xlsx")
}

# ------------------- AUTO MAPPING HELPERS -------------------
expected_orders_columns = {
    "Order Date": ["Order Date", "Date", "Order_Date", "OrderDate"],
    "SKU ID": ["SKU ID", "SKU", "Product Code", "Item Code"],
    "Order Quantity": ["Order Quantity", "Quantity", "Qty", "Order Qty"]
}
expected_inventory_columns = {
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


def auto_map_column(source_columns, expected_variants):
    """Maps actual dataset column names to expected names using fuzzy matching"""
    for expected_name in expected_variants:
        matched_columns = difflib.get_close_matches(expected_name, source_columns, n=1, cutoff=0.6)
        if matched_columns:
            return matched_columns[0]
    return None


# ------------------- UI HEADER -------------------
title_col, button_col = st.columns([0.75, 0.25])
with title_col:
    st.title("Upload Data")
with button_col:
    if st.button("Use Sample Data"):
        success = True
        missing_sample_files = []

        for dataset_name in sample_file_paths:
            sample_file_path = sample_file_paths[dataset_name]
            if os.path.exists(sample_file_path):
                try:
                    uploaded_df = pd.read_excel(sample_file_path)
                    uploaded_df.to_excel(shared_save_paths[dataset_name], index=False)
                    st.session_state.uploaded_dataframes[dataset_name] = uploaded_df
                    st.session_state.upload_status[dataset_name] = True
                    st.session_state.file_names[dataset_name] = os.path.basename(sample_file_path)
                except Exception as e:
                    st.error(f"Error reading sample file for {dataset_name}: {e}")
                    success = False
            else:
                missing_sample_files.append(dataset_name)
                success = False

        if missing_sample_files:
            st.warning(f"Missing sample files for: {', '.join(missing_sample_files)}")
        elif success:
            st.success("Sample data loaded successfully!")
            st.session_state.use_sample = True

            try:
                orders_df = st.session_state.uploaded_dataframes.get("Orders")
                inventory_df = st.session_state.uploaded_dataframes.get("Inventory")

                if orders_df is None or inventory_df is None:
                    raise ValueError("Orders or Inventory sample data is missing or invalid.")

                # Auto-map columns
                orders_column_map = {k: auto_map_column(orders_df.columns.tolist(), v) or "" 
                                     for k, v in expected_orders_columns.items()}
                inventory_column_map = {k: auto_map_column(inventory_df.columns.tolist(), v) or "" 
                                        for k, v in expected_inventory_columns.items()}

                # Standardize Orders
                orders_df = orders_df[[orders_column_map["Order Date"],
                                       orders_column_map["SKU ID"],
                                       orders_column_map["Order Quantity"]]]
                orders_df.columns = ["Order Date", "SKU ID", "Order Quantity"]
                orders_df["Order Date"] = pd.to_datetime(orders_df["Order Date"], errors="coerce")

                # Standardize Inventory
                inventory_df = inventory_df[
                    [inventory_column_map[k] for k in expected_inventory_columns if inventory_column_map[k] in inventory_df.columns]
                ]
                inventory_df.columns = list(expected_inventory_columns.keys())[:len(inventory_df.columns)]

                # Aggregations
                orders_summary_df = orders_df.groupby("SKU ID").agg(
                    {"Order Quantity": ["sum", "mean", "std"]}
                ).reset_index()
                orders_summary_df.columns = ["SKU ID", "Order Quantity sum", "Order Quantity mean", "Order Quantity std"]

                latest_order_dates_df = orders_df.groupby("SKU ID")["Order Date"].max().reset_index(name="Last Order Date")

                def compute_median_order_interval(group):
                    group = group.sort_values("Order Date")
                    group["Days Between Orders"] = group["Order Date"].diff().dt.days
                    return pd.Series({"Median Days Between Orders": group["Days Between Orders"].median()})

                median_order_interval_df = orders_df.groupby("SKU ID").apply(compute_median_order_interval).reset_index()

                # Merge
                inventory_orders_df = (
                    inventory_df
                    .merge(orders_summary_df, on="SKU ID", how="left")
                    .merge(latest_order_dates_df, on="SKU ID", how="left")
                    .merge(median_order_interval_df, on="SKU ID", how="left")
                )
                inventory_orders_df.fillna(0, inplace=True)
                st.session_state["merged_df"] = inventory_orders_df

            except Exception as e:
                st.error(f"❌ Failed to process Inventory + Orders sample data: {e}")
                traceback.print_exc()

# ------------------- DROPDOWN FILE UPLOAD -------------------
st.markdown("### Select a dataset to upload")
selected_dataset = st.selectbox("Choose file to upload:", list(shared_save_paths.keys()))

uploaded_file = st.file_uploader(f"Upload {selected_dataset} (.xlsx)", type=["xlsx"], key=selected_dataset)
if uploaded_file:
    try:
        uploaded_df = pd.read_excel(uploaded_file)
        uploaded_df.to_excel(shared_save_paths[selected_dataset], index=False)
        st.session_state.upload_status[selected_dataset] = True
        st.session_state.uploaded_dataframes[selected_dataset] = uploaded_df
        st.session_state.file_names[selected_dataset] = uploaded_file.name
        st.success(f"{selected_dataset} uploaded successfully.")
        with st.expander(f" Preview {selected_dataset}"):
            st.dataframe(uploaded_df, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Failed to upload {selected_dataset}: {e}")
        traceback.print_exc()

# ------------------- PROCESS INVENTORY + ORDERS -------------------
if st.session_state.upload_status["Orders"] and st.session_state.upload_status["Inventory"]:
    if st.button("Submit"):
        try:
            orders_df = st.session_state.uploaded_dataframes["Orders"]
            inventory_df = st.session_state.uploaded_dataframes["Inventory"]

            # ---- Auto map ----
            orders_column_map = {k: auto_map_column(orders_df.columns.tolist(), v) or "" 
                                 for k, v in expected_orders_columns.items()}
            inventory_column_map = {k: auto_map_column(inventory_df.columns.tolist(), v) or "" 
                                    for k, v in expected_inventory_columns.items()}

            # ---- Standardize Orders ----
            orders_df = orders_df[[orders_column_map["Order Date"],
                                   orders_column_map["SKU ID"],
                                   orders_column_map["Order Quantity"]]]
            orders_df.columns = ["Order Date", "SKU ID", "Actual"]
            orders_df["Order Date"] = pd.to_datetime(orders_df["Order Date"], errors="coerce")

            # ---- Standardize Inventory ----
            inventory_df = inventory_df[
                [inventory_column_map[k] for k in expected_inventory_columns if inventory_column_map[k] in inventory_df.columns]
            ]
            inventory_df.columns = list(expected_inventory_columns.keys())[:len(inventory_df.columns)]

            # ---- Rename hierarchy columns ----
            hierarchy_rename_map = {}
            if "Location" in inventory_df.columns and "Store" not in inventory_df.columns:
                hierarchy_rename_map["Location"] = "Store"
            if "Warehouse_ID" in inventory_df.columns and "Warehouse" not in inventory_df.columns:
                hierarchy_rename_map["Warehouse_ID"] = "Warehouse"
            if "DC_ID" in inventory_df.columns and "DC" not in inventory_df.columns:
                hierarchy_rename_map["DC_ID"] = "DC"
            inventory_df.rename(columns=hierarchy_rename_map, inplace=True)

            # ---- Aggregations ----
            orders_summary_df = orders_df.groupby("SKU ID").agg({"Actual": ["sum", "mean", "std"]}).reset_index()
            orders_summary_df.columns = ["SKU ID", "Order Quantity sum", "Order Quantity mean", "Order Quantity std"]

            latest_order_dates_df = orders_df.groupby("SKU ID")["Order Date"].max().reset_index(name="Last Order Date")

            def compute_median_order_interval(group):
                group = group.sort_values("Order Date")
                group["Days Between Orders"] = group["Order Date"].diff().dt.days
                return pd.Series({"Median Days Between Orders": group["Days Between Orders"].median()})

            median_order_interval_df = orders_df.groupby("SKU ID").apply(compute_median_order_interval).reset_index()

            # ---- Merge ----
            inventory_orders_df = (
                inventory_df
                .merge(orders_summary_df, on="SKU ID", how="left")
                .merge(latest_order_dates_df, on="SKU ID", how="left")
                .merge(median_order_interval_df, on="SKU ID", how="left")
            )
            inventory_orders_df.fillna(0, inplace=True)

            # Save for pipeline
            merged_dataset_path = os.path.join(SHARED_DIR, "merged_data.xlsx")
            inventory_orders_df.to_excel(merged_dataset_path, index=False)

            st.session_state["merged_df"] = inventory_orders_df
            st.success(f"Data processed. Saved merged dataset to {merged_dataset_path}")

        except Exception as e:
            st.error(f"❌ Processing failed: {e}")
            traceback.print_exc()

# ------------------- STATUS TABLE WITH FILE NAME -------------------
st.markdown("### Upload Status Summary")
upload_status_records = []

for dataset_name in st.session_state.upload_status.keys():
    upload_status_records.append({
        "Dataset": dataset_name,
        "Status": "✅" if st.session_state.upload_status[dataset_name] else "❌",
        "File Name": st.session_state.file_names.get(dataset_name, "-")
    })

upload_status_df = pd.DataFrame(upload_status_records)
upload_status_html = upload_status_df.to_html(index=False, escape=False)

st.markdown(f"""
    <div style="border:1px solid #ddd; border-radius:10px; padding:10px; background-color:#f9f9f9">
        <style>
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 15px;
            }}
            th, td {{
                text-align: left;
                padding: 8px;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #f2f2f2;
            }}
        </style>
        {upload_status_html}
    </div>
""", unsafe_allow_html=True)

# ------------------- RUN MEIO ENGINE -------------------
st.markdown("### Run MEIO Engine")
if all([st.session_state.upload_status[k] for k in ["Demand Forecast", "Lead Time", "Node Data"]]):
    if "engine_run" not in st.session_state:
        st.session_state.engine_run = False

    if not st.session_state.engine_run:
        if st.button("Run MEIO Engine"):
            try:
                start = time.time()
                run_meio_pipeline()
                end = time.time()
                st.success("MEIO Engine executed successfully.")
                st.info(f"{end-start:.2f}")
                st.session_state.engine_run = True
            except Exception as e:
                st.error("❌ MEIO Engine failed.")
                tb = io.StringIO()
                traceback.print_exc(file=tb)
                st.code(tb.getvalue(), language="python")
    else:
        st.button("Run MEIO Engine", disabled=True)
else:
     st.warning("Upload all required MEIO input files to enable engine.")
