import os
import pandas as pd
from server.app_function_call import aggregate

def run_meio_pipeline():
    """
    Run the MEIO pipeline using uploaded/shared data.
    Ensures the right dataframe (Orders/Demand) is used for aggregation.
    """

    shared_dir = os.path.join(os.path.dirname(__file__), "..", "shared_data")

    # Priority: use processed merged data if available
    merged_path = os.path.join(shared_dir, "merged_data.xlsx")
    orders_path = os.path.join(shared_dir, "orders.xlsx")

    if os.path.exists(merged_path):
        print("Loading merged data...")
        df = pd.read_excel(merged_path)

        # Ensure we have demand column
        if "Actual" not in df.columns and "Order Quantity" in df.columns:
            df = df.rename(columns={"Order Quantity": "Actual"})
        if "Order Date" not in df.columns and "Date" in df.columns:
            df = df.rename(columns={"Date": "Order Date"})

    elif os.path.exists(orders_path):
        print("Loading orders data...")
        df = pd.read_excel(orders_path)

        # Rename columns to match aggregation requirements
        rename_map = {}
        if "Order Quantity" in df.columns:
            rename_map["Order Quantity"] = "Actual"
        if "Order Date" in df.columns:
            rename_map["Order Date"] = "Order Date"  # keep same but ensure existence
        if rename_map:
            df = df.rename(columns=rename_map)
    else:
        raise FileNotFoundError("No valid Orders or Merged data found in shared_data/")

    # Run aggregations
    store_df, warehouse_df, dc_df = aggregate(df)
    return store_df, warehouse_df, dc_df
