# server/cost_comparison/prepare_dashboard.py

import os
import pandas as pd
import numpy as np

from server.config import (
    cost_path,               # output_data/cost  (folder)
    node_costs_file,         # server/data/Node_Costs.xlsx
    product_cost_file        # server/data/Product_Master.xlsx
)

DASHBOARD_PARQUET = os.path.join(cost_path, "dashboard_costs.parquet")
DASHBOARD_EXCEL   = os.path.join(cost_path, "dashboard_costs.xlsx")

def _safe_num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0.0)

def _ensure_cols(df, cols):
    for c in cols:
        if c not in df.columns:
            df[c] = 0.0
    return df

def _standardize_cols(df):
    # normalize common columns
    rename_map = {
        "Item.[Stat Item]": "SKU",
        "Sku": "SKU",
        "Sku_ID": "SKU",
        "SkuId": "SKU",
        "Node_ID": "Node",
        "Location_ID": "Node",
        "Location": "Node",
        "EchelonType": "Echelon_Type",
        "Echelon": "Echelon",
        "Date": "Date",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    # strings
    if "SKU" in df.columns:
        df["SKU"] = df["SKU"].astype(str).str.strip().str.upper()
    if "Node" in df.columns:
        df["Node"] = df["Node"].astype(str).str.strip().str.upper()
    # time
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month
    if "Year" in df.columns and "Month" in df.columns:
        df["YearMonth"] = df["Year"].astype(str) + "-" + df["Month"].astype(str).str.zfill(2)
    return df

def _derive_echelon(df):
    # if not provided, derive from Node prefix
    if "Echelon" not in df.columns:
        if "Node" in df.columns:
            df["Echelon"] = df["Node"].str.split("_").str[0]
        else:
            df["Echelon"] = "UNKNOWN"
    # harmonize Echelon_Type for UI compatibility
    if "Echelon_Type" not in df.columns:
        df["Echelon_Type"] = df["Echelon"]
    return df

def _total_cost(df):
    # Build a robust TotalCost:
    # If component costs exist, sum components.
    # Else fallback to HoldingCost only.
    comp_cols = [c for c in df.columns if c.lower() in (
        "holdingcost", "orderingcost", "transportcost", "replenishmentcost", "stockoutcost"
    )]
    if comp_cols:
        df["TotalCost"] = df[comp_cols].apply(_safe_num).sum(axis=1)
    else:
        df["TotalCost"] = _safe_num(df.get("HoldingCost", 0))
    return df

def _load_cost_file(path, policy_label):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing cost file: {path}")
    if path.lower().endswith(".xlsx"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    df = _standardize_cols(df)
    df["Policy"] = policy_label
    # normalize numeric component names if they exist in various casings
    canon = {
        "HoldingCost": ["HoldingCost", "Holding_Cost", "Holding Cost"],
        "OrderingCost": ["OrderingCost", "Ordering_Cost", "Ordering Cost", "Order_Cost"],
        "TransportCost": ["TransportCost", "Transport_Cost", "Transport Cost", "Distribution_Cost"],
        "InventoryValue": ["InventoryValue", "Inventory_Value", "Inventory Value", "ProductCost", "Product_Cost"],
        "Quantity": ["Quantity", "Qty", "Order_Qty", "Order Quantity"],
    }
    for target, alts in canon.items():
        if target not in df.columns:
            for a in alts:
                if a in df.columns:
                    df = df.rename(columns={a: target})
                    break
    # ensure columns exist
    df = _ensure_cols(
        df,
        ["HoldingCost", "OrderingCost", "TransportCost", "InventoryValue", "Quantity"]
    )
    # compute total
    df = _total_cost(df)
    return df

def prepare_cost_dashboard():
    """
    Reads MEIO (EOQ) and Non-MEIO cost files produced by your pipeline,
    filters strictly to SKUs present in Product Master,
    merges Node attributes,
    and saves a single dashboard dataset (parquet + excel).
    Returns the dashboard DataFrame.
    """
    # ---- Input files from your pipeline outputs
    eoq_file      = os.path.join(cost_path, "eoq_cost.xlsx")        # MEIO
    noneoq_file   = os.path.join(cost_path, "non_eoq_cost.xlsx")    # Non-MEIO

    meio = _load_cost_file(eoq_file,     "MEIO")
    nonm = _load_cost_file(noneoq_file,  "Non-MEIO")

    # ---- Only use SKUs present in Product Master
    product = pd.read_excel(product_cost_file)
    if "SKU" not in product.columns:
        # try common variants
        for cand in ["Sku", "Item.[Stat Item]", "ItemStat_Item", "SKU_ID"]:
            if cand in product.columns:
                product = product.rename(columns={cand: "SKU"})
                break
    product["SKU"] = product["SKU"].astype(str).str.strip().str.upper()
    keep_skus = set(product["SKU"].unique())
    meio = meio[meio["SKU"].isin(keep_skus)].copy()
    nonm = nonm[nonm["SKU"].isin(keep_skus)].copy()

    # ---- Merge Node attributes (Echelon_Type, geo, etc.)
    node = pd.read_excel(node_costs_file)
    if "Node" not in node.columns:
        for cand in ["Node_ID", "Location_ID"]:
            if cand in node.columns:
                node = node.rename(columns={cand: "Node"})
                break
    node["Node"] = node["Node"].astype(str).str.strip().str.upper()

    # guarantee Node joinable
    for df in (meio, nonm):
        if "Node" not in df.columns:
            # try to build Node if missing
            if "Echelon" in df.columns and "NodeCode" in df.columns:
                df["Node"] = df["Echelon"].str.upper() + "_" + df["NodeCode"].astype(str)
            else:
                df["Node"] = "UNKNOWN"

    meio = meio.merge(node, on="Node", how="left", suffixes=("", "_node"))
    nonm = nonm.merge(node, on="Node", how="left", suffixes=("", "_node"))

    # ---- Derive/align echelon columns
    meio  = _derive_echelon(meio)
    nonm  = _derive_echelon(nonm)

    # ---- Concatenate
    all_df = pd.concat([meio, nonm], ignore_index=True)

    # Final hygiene
    if "Year" in all_df.columns and "Month" in all_df.columns:
        all_df["YearMonth"] = all_df["Year"].astype(str) + "-" + all_df["Month"].astype(str).str.zfill(2)
    if "SKU_Description" in product.columns and "SKU_Description" not in all_df.columns:
        all_df = all_df.merge(product[["SKU", "SKU_Description"]], on="SKU", how="left")

    # Save
    all_df.to_parquet(DASHBOARD_PARQUET, index=False)
    all_df.to_excel(DASHBOARD_EXCEL, index=False)

    return all_df

def load_cost_dashboard_data():
    """
    Loads the dashboard dataset if it exists; otherwise prepares it.
    """
    if os.path.exists(DASHBOARD_PARQUET):
        return pd.read_parquet(DASHBOARD_PARQUET)
    return prepare_cost_dashboard()
