import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# --- Paths ---
BASE_DIR = os.path.dirname(__file__)
SERVER_DATA_DIR = os.path.join(BASE_DIR, "data")
UI_DIST_DIR = os.path.join(BASE_DIR, "..", "ui", "output_data", "distribution")

# --- Load Data ---
product_master = pd.read_excel(os.path.join(SERVER_DATA_DIR, "Product_Master.xlsx"))
node_cost = pd.read_excel(os.path.join(SERVER_DATA_DIR, "Node_Costs.xlsx"))
dc_warehouse_dist = pd.read_excel(os.path.join(UI_DIST_DIR, "dc_warehouse_distribution_df.xlsx"))
warehouse_store_dist = pd.read_excel(os.path.join(UI_DIST_DIR, "warehouse_store_distribution_df.xlsx"))

print("✅ Data loaded")

# --- EOQ formula ---
def calculate_eoq(demand, ordering_cost, holding_cost):
    if demand > 0 and ordering_cost > 0 and holding_cost > 0:
        return np.sqrt((2 * demand * ordering_cost) / holding_cost)
    return 0

# --- Generate monthly dates ---
def generate_monthly_dates(year=2025):
    return [datetime(year, m, 1) for m in range(1, 13)]

# --- Generate EOQ spaced dates ---
def generate_eoq_dates(num_orders, year=2025):
    if num_orders <= 0:
        return []
    start = datetime(year, 1, 1)
    interval = 365 / num_orders
    return [(start + timedelta(days=int(i * interval))) for i in range(num_orders)]

# --- Build order schedule ---
def compute_schedule(df, echelon_col, demand_col, sku_col="ItemStat_Item", demand_horizon="monthly"):
    schedule = []
    for _, row in df.iterrows():
        sku = row[sku_col]
        demand = row[demand_col]
        echelon = row[echelon_col]

        # --- Normalize demand to annual ---
        if demand_horizon == "monthly":
            annual_demand = demand * 12
        elif demand_horizon == "weekly":
            annual_demand = demand * 52
        else:
            annual_demand = demand

        # --- Product cost ---
        prod_row = product_master.loc[product_master["SKU"] == sku]
        if prod_row.empty:
            continue
        prod_cost = prod_row["Product_Cost"].values[0]

        # --- Node costs ---
        node_row = node_cost.loc[node_cost["Node"] == echelon]
        if node_row.empty:
            continue
        ordering_cost = node_row["Ordering Cost"].values[0]
        holding_cost_rate = node_row["Holding Cost"].values[0]
        holding_cost = holding_cost_rate * prod_cost

        # =========================
        # Non-MEIO: monthly orders
        # =========================
        monthly_demand = annual_demand / 12
        for d in generate_monthly_dates():
            hc = (monthly_demand / 2) * holding_cost
            total_cost = ordering_cost + hc
            schedule.append({
                "SKU": sku,
                "Echelon": echelon,
                "Policy": "Non-MEIO",
                "Order_Date": d.strftime("%Y-%m-%d"),
                "Order_Qty": round(monthly_demand, 2),
                "Ordering_Cost": round(ordering_cost, 2),
                "Holding_Cost": round(hc, 2),
                "Total_Cost": round(total_cost, 2)
            })

        # =========================
        # MEIO: EOQ-based orders
        # =========================
        eoq = calculate_eoq(annual_demand, ordering_cost, holding_cost)
        num_orders = int(round(annual_demand / eoq)) if eoq > 0 else 0
        for d in generate_eoq_dates(num_orders):
            hc = (eoq / 2) * holding_cost
            total_cost = ordering_cost + hc
            schedule.append({
                "SKU": sku,
                "Echelon": echelon,
                "Policy": "EOQ",
                "Order_Date": d.strftime("%Y-%m-%d"),
                "Order_Qty": round(eoq, 2),
                "Ordering_Cost": round(ordering_cost, 2),
                "Holding_Cost": round(hc, 2),
                "Total_Cost": round(total_cost, 2)
            })

    return pd.DataFrame(schedule)

# --- Run for DC → Warehouse ---
dc_schedule = compute_schedule(dc_warehouse_dist, echelon_col="Warehouse", demand_col="Warehouse_Monthly_Demand", demand_horizon="monthly")

# --- Run for Warehouse → Store ---
store_schedule = compute_schedule(warehouse_store_dist, echelon_col="Store", demand_col="store_total_stock", demand_horizon="annual")

# --- Combine ---
all_schedule = pd.concat([dc_schedule, store_schedule], ignore_index=True)

print("\n--- Order Schedule (Sample) ---")
print(all_schedule.head(15).to_markdown(index=False))

# --- Save Output ---
OUTPUT_PATH = os.path.join(BASE_DIR, "multi_level_cost_comparison_schedule.xlsx")
all_schedule.to_excel(OUTPUT_PATH, index=False)
print(f"\n✅ Order schedule with dates saved to {OUTPUT_PATH}")
