import os
import pandas as pd
import numpy as np

# --- Helper: EOQ calculation ---
def calculate_eoq(demand, ordering_cost, holding_cost):
    """
    Calculates the Economic Order Quantity (EOQ).
    """
    try:
        if demand > 0 and ordering_cost > 0 and holding_cost > 0:
            return np.sqrt((2 * demand * ordering_cost) / holding_cost)
        else:
            return 0
    except:
        return 0

# --- Cost Calculation Function ---
def compute_costs(df, echelon_col, demand_col, sku_col="ItemStat_Item"):
    """
    Computes EOQ and Non-EOQ costs for a given distribution DataFrame.
    """
    # --- Paths ---
    BASE_DIR = os.path.dirname(__file__)
    SERVER_DATA_DIR = os.path.join(BASE_DIR, "data")
    
    # --- Load Data ---
    try:
        product_master = pd.read_excel(os.path.join(SERVER_DATA_DIR, "Product_Master.xlsx"))
        node_cost = pd.read_excel(os.path.join(SERVER_DATA_DIR, "Node_Costs.xlsx"))
    except FileNotFoundError as e:
        print(f"Error loading required data files: {e}")
        return pd.DataFrame()

    results = []
    for _, row in df.iterrows():
        sku = row[sku_col]
        demand = row[demand_col]
        echelon = row[echelon_col]

        # Get product cost
        prod_cost = product_master.loc[product_master["SKU"] == sku, "Product_Cost"].values
        if len(prod_cost) == 0:
            continue
        prod_cost = prod_cost[0]

        # Get node costs
        node_row = node_cost.loc[node_cost["Node"] == echelon]
        if node_row.empty:
            continue
        ordering_cost = node_row["Ordering Cost"].values[0]
        holding_cost_rate = node_row["Holding Cost"].values[0]

        # Holding cost = % of product cost
        holding_cost = holding_cost_rate * prod_cost

        # --- EOQ Policy ---
        eoq = calculate_eoq(demand, ordering_cost, holding_cost)
        ordering_cost_eoq = (demand / eoq) * ordering_cost if eoq > 0 else 0
        holding_cost_eoq = (eoq / 2) * holding_cost if eoq > 0 else 0
        total_cost_eoq = ordering_cost_eoq + holding_cost_eoq

        # --- Non-EOQ Policy (order once per year = demand in one lot) ---
        ordering_cost_non = ordering_cost
        holding_cost_non = (demand / 2) * holding_cost
        total_cost_non = ordering_cost_non + holding_cost_non

        # --- Savings ---
        savings = total_cost_non - total_cost_eoq

        results.append({
            "SKU": sku,
            "Echelon": echelon,
            "Demand": demand,
            "Product_Cost": prod_cost,
            "Ordering_Cost": ordering_cost,
            "Holding_Cost_per_unit": holding_cost,
            "EOQ": round(eoq, 2),
            # EOQ Policy
            "EOQ_Ordering_Cost": round(ordering_cost_eoq, 2),
            "EOQ_Holding_Cost": round(holding_cost_eoq, 2),
            "EOQ_Total_Cost": round(total_cost_eoq, 2),
            # Non-EOQ Policy
            "NonEOQ_Ordering_Cost": round(ordering_cost_non, 2),
            "NonEOQ_Holding_Cost": round(holding_cost_non, 2),
            "NonEOQ_Total_Cost": round(total_cost_non, 2),
            # Comparison
            "Cost_Savings": round(savings, 2)
        })
    return pd.DataFrame(results)

# ----------------------------------------------------------------------
# This is the new function that will be imported and called.
# It encapsulates the main logic of your original script.
# ----------------------------------------------------------------------
def run_multi_level_cost_comparison():
    """
    Loads distribution data, computes costs for different echelons,
    combines the results, and saves them to an Excel file.
    
    Returns:
        pd.DataFrame: A DataFrame with the combined cost comparison results.
    """
    # --- Paths ---
    BASE_DIR = os.path.dirname(__file__)
    SERVER_DATA_DIR = os.path.join(BASE_DIR, "data")
    UI_DIST_DIR = os.path.join(BASE_DIR, "..", "ui", "output_data", "distribution")

    # --- Load Data ---
    try:
        dc_warehouse_dist = pd.read_excel(os.path.join(UI_DIST_DIR, "dc_warehouse_distribution_df.xlsx"))
        warehouse_store_dist = pd.read_excel(os.path.join(UI_DIST_DIR, "warehouse_store_distribution_df.xlsx"))
        print("✅ Data loaded")
    except FileNotFoundError as e:
        print(f"Error loading required distribution data: {e}")
        return pd.DataFrame()

    # --- Run for DC → Warehouse ---
    dc_results = compute_costs(dc_warehouse_dist, echelon_col="Warehouse", demand_col="Warehouse_Monthly_Demand")

    # --- Run for Warehouse → Store ---
    store_results = compute_costs(warehouse_store_dist, echelon_col="Store", demand_col="store_total_stock")

    # --- Combine ---
    all_results = pd.concat([dc_results, store_results], ignore_index=True)

    print("\n--- EOQ vs Non-EOQ Cost Comparison (Sample) ---")
    print(all_results.head(10))

    # --- Save Output ---
    OUTPUT_PATH = os.path.join(BASE_DIR, "multi_level_cost_comparison.xlsx")
    all_results.to_excel(OUTPUT_PATH, index=False)
    print(f"\n✅ Results saved to {OUTPUT_PATH}")
    
    return all_results

# If you run this file directly, it will execute the function.
if __name__ == "__main__":
    run_multi_level_cost_comparison()