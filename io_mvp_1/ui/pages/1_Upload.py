import streamlit as st
import pandas as pd
import os
import difflib
import sys
import traceback
import io

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from server.app import run_meio_pipeline

# ------------------- PATH SETUP -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.join(BASE_DIR, "..", "..", "shared_data")
SAMPLE_DIR = os.path.join(BASE_DIR, "..", "..", "server\data")
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

# ------------------- FILE PATHS -------------------
sample_paths = {
    "Orders": os.path.join(SAMPLE_DIR, "sample_orders.xlsx"),
    "Inventory": os.path.join(SAMPLE_DIR, "sample_master.xlsx"),
    "Demand Forecast": os.path.join(SAMPLE_DIR, "Multi_Sku.xlsx"),
    "Lead Time": os.path.join(SAMPLE_DIR, "Leadtime_MultiSKU.xlsx"),
    "Node Data": os.path.join(SAMPLE_DIR, "Node_Costs.xlsx")
}
save_paths = {
    "Orders": os.path.join(SHARED_DIR, "orders.xlsx"),
    "Inventory": os.path.join(SHARED_DIR, "inventory.xlsx"),
    "Demand Forecast": os.path.join(SHARED_DIR, "demand_forecast.xlsx"),
    "Lead Time": os.path.join(SHARED_DIR, "lead_time.xlsx"),
    "Node Data": os.path.join(SHARED_DIR, "node_data.xlsx")
}
# ------------------- AUTO MAPPING HELPERS -------------------
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
# ------------------- UI HEADER -------------------
col1, col2 = st.columns([0.75, 0.25])
with col1:
    st.title("Upload Inventory, Orders & MEIO Data")
with col2:
    if st.button(" Use Sample Data"):
        
        success = True
        missing_files = []

        # Load sample files safely
        for key in sample_paths:
            sample_file = sample_paths[key]
            if os.path.exists(sample_file):
                try:
                    df = pd.read_excel(sample_file)
                    df.to_excel(save_paths[key], index=False)
                    st.session_state.uploaded_dataframes[key] = df
                    st.session_state.upload_status[key] = True
                except Exception as e:
                    st.error(f" Error reading sample file for {key}: {e}")
                    success = False
            else:
                missing_files.append(key)
                success = False

        if missing_files:
            st.warning(f" Missing sample files for: {', '.join(missing_files)}")
        elif success:
            st.success(" Sample data loaded successfully!")
            st.session_state.use_sample = True
        

            try:
                # Now process Orders + Inventory
                df_orders = st.session_state.uploaded_dataframes.get("Orders")
                df_stock = st.session_state.uploaded_dataframes.get("Inventory")

                if df_orders is None or df_stock is None:
                    raise ValueError("Orders or Inventory sample data is missing or invalid.")

                order_mappings = {k: auto_map(df_orders.columns.tolist(), v) or "" for k, v in expected_orders_cols.items()}
                stock_mappings = {k: auto_map(df_stock.columns.tolist(), v) or "" for k, v in expected_stock_cols.items()}

                orders_df = df_orders[[order_mappings["Order Date"], order_mappings["SKU ID"], order_mappings["Order Quantity"]]]
                orders_df.columns = ["Order Date", "SKU ID", "Order Quantity"]
                orders_df["Order Date"] = pd.to_datetime(orders_df["Order Date"], errors="coerce")

                stock_df = df_stock[[stock_mappings[k] for k in expected_stock_cols if stock_mappings[k] in df_stock.columns]]
                stock_df.columns = list(expected_stock_cols.keys())[:len(stock_df.columns)]

                agg_orders = orders_df.groupby("SKU ID").agg({"Order Quantity": ["sum", "mean", "std"]}).reset_index()
                agg_orders.columns = ["SKU ID", "Order Quantity sum", "Order Quantity mean", "Order Quantity std"]

                last_order_df = orders_df.groupby("SKU ID")["Order Date"].max().reset_index(name="Last Order Date")

                def compute_median_days(group):
                    group = group.sort_values("Order Date")
                    group["Days Between Orders"] = group["Order Date"].diff().dt.days
                    return pd.Series({"Median Days Between Orders": group["Days Between Orders"].median()})
                median_days_df = orders_df.groupby("SKU ID").apply(compute_median_days).reset_index()

                merged_df = stock_df.merge(agg_orders, on="SKU ID", how="left")\
                                    .merge(last_order_df, on="SKU ID", how="left")\
                                    .merge(median_days_df, on="SKU ID", how="left")
                merged_df.fillna(0, inplace=True)
                st.session_state["merged_df"] = merged_df

                
            except Exception as e:
                st.error(f"❌ Failed to process Inventory + Orders sample data: {e}")
                traceback.print_exc()






# ------------------- DROPDOWN FILE UPLOAD -------------------
st.markdown("###  Select a dataset to upload")
selected = st.selectbox("Choose file to upload:", list(save_paths.keys()))

uploaded_file = st.file_uploader(f"Upload {selected} (.xlsx)", type=["xlsx"], key=selected)
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.to_excel(save_paths[selected], index=False)
        st.session_state.upload_status[selected] = True
        st.session_state.uploaded_dataframes[selected] = df
        st.success(f"{selected} uploaded successfully.")
        with st.expander(f" Preview {selected}"):
            st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Failed to upload {selected}: {e}")
        traceback.print_exc()

# ------------------- PROCESS INVENTORY + ORDERS -------------------
if st.session_state.upload_status["Orders"] and st.session_state.upload_status["Inventory"]:
    st.markdown("")
    if st.button("Submit"):
        try:
            df_orders = st.session_state.uploaded_dataframes["Orders"]
            df_stock = st.session_state.uploaded_dataframes["Inventory"]

            order_mappings = {k: auto_map(df_orders.columns.tolist(), v) or "" for k, v in expected_orders_cols.items()}
            stock_mappings = {k: auto_map(df_stock.columns.tolist(), v) or "" for k, v in expected_stock_cols.items()}

            orders_df = df_orders[[order_mappings["Order Date"], order_mappings["SKU ID"], order_mappings["Order Quantity"]]]
            orders_df.columns = ["Order Date", "SKU ID", "Order Quantity"]
            orders_df["Order Date"] = pd.to_datetime(orders_df["Order Date"], errors="coerce")

            stock_df = df_stock[[stock_mappings[k] for k in expected_stock_cols if stock_mappings[k] in df_stock.columns]]
            stock_df.columns = list(expected_stock_cols.keys())[:len(stock_df.columns)]

            agg_orders = orders_df.groupby("SKU ID").agg({"Order Quantity": ["sum", "mean", "std"]}).reset_index()
            agg_orders.columns = ["SKU ID", "Order Quantity sum", "Order Quantity mean", "Order Quantity std"]

            last_order_df = orders_df.groupby("SKU ID")["Order Date"].max().reset_index(name="Last Order Date")

            def compute_median_days(group):
                group = group.sort_values("Order Date")
                group["Days Between Orders"] = group["Order Date"].diff().dt.days
                return pd.Series({"Median Days Between Orders": group["Days Between Orders"].median()})
            median_days_df = orders_df.groupby("SKU ID").apply(compute_median_days).reset_index()

            merged_df = stock_df.merge(agg_orders, on="SKU ID", how="left")\
                                .merge(last_order_df, on="SKU ID", how="left")\
                                .merge(median_days_df, on="SKU ID", how="left")
            merged_df.fillna(0, inplace=True)

            st.session_state["merged_df"] = merged_df
            st.success(" Inventory + Orders processed.")
            with st.expander(" See Merged Data"):
                st.dataframe(merged_df, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Processing failed: {e}")
            traceback.print_exc()

# ------------------- STATUS TABLE -------------------
st.markdown("### 📋 Upload Status Summary")
st.dataframe(pd.DataFrame({
    "Dataset": list(st.session_state.upload_status.keys()),
    "Status": ["✅" if v else "❌" for v in st.session_state.upload_status.values()]
}), use_container_width=True)

# ------------------ RUN MEIO ENGINE -------------------
st.markdown("###  Run MEIO Engine")
if all([st.session_state.upload_status[k] for k in ["Demand Forecast", "Lead Time", "Node Data"]]):
    if st.button("Run MEIO Engine"):
        try:
            run_meio_pipeline()
            st.success(" MEIO Engine executed successfully.")
        except Exception as e:
            st.error("❌ MEIO Engine failed.")
            tb = io.StringIO()
            traceback.print_exc(file=tb)
            st.code(tb.getvalue(), language="python")
else:
    st.warning("Upload all required MEIO input files to enable engine.")
