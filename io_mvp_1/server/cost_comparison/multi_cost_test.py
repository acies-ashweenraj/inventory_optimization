# import os
# import pandas as pd
# import numpy as np

# # --- Paths ---
# BASE_DIR = os.path.dirname(__file__)
# SERVER_DATA_DIR = os.path.join(BASE_DIR, "data")
# UI_DIST_DIR = os.path.join(BASE_DIR, "..", "ui", "output_data", "distribution")

# # --- Load Data ---
# product_master = pd.read_excel(os.path.join(SERVER_DATA_DIR, "Product_Master.xlsx"))
# node_cost = pd.read_excel(os.path.join(SERVER_DATA_DIR, "Node_Costs.xlsx"))
# dc_warehouse_dist = pd.read_excel(os.path.join(UI_DIST_DIR, "dc_warehouse_distribution_df.xlsx"))
# warehouse_store_dist = pd.read_excel(os.path.join(UI_DIST_DIR, "warehouse_store_distribution_df.xlsx"))

# print("✅ Data loaded")

# # --- EOQ formula ---
# def calculate_eoq(demand, ordering_cost, holding_cost):
#     if demand > 0 and ordering_cost > 0 and holding_cost > 0:
#         return np.sqrt((2 * demand * ordering_cost) / holding_cost)
#     return 0

# # --- Compute cost summary ---
# def compute_cost_summary(df, echelon_col, demand_col, sku_col="ItemStat_Item", demand_horizon="monthly"):
#     records = []

#     for _, row in df.iterrows():
#         sku = row[sku_col]
#         demand = row[demand_col]
#         echelon = row[echelon_col]

#         # --- Normalize demand to annual ---
#         if demand_horizon == "monthly":
#             annual_demand = demand * 12
#         elif demand_horizon == "weekly":
#             annual_demand = demand * 52
#         else:
#             annual_demand = demand

#         # --- Product cost ---
#         prod_row = product_master.loc[product_master["SKU"] == sku]
#         if prod_row.empty:
#             continue
#         prod_cost = prod_row["Product_Cost"].values[0]

#         # --- Node costs ---
#         node_row = node_cost.loc[node_cost["Node"] == echelon]
#         if node_row.empty:
#             continue
#         ordering_cost = node_row["Ordering Cost"].values[0]
#         holding_cost_rate = node_row["Holding Cost"].values[0]
#         holding_cost = holding_cost_rate * prod_cost  # annual holding cost per unit

#         # =======================
#         # EOQ Policy
#         # =======================
#         eoq = calculate_eoq(annual_demand, ordering_cost, holding_cost)
#         num_orders_eoq = annual_demand / eoq if eoq > 0 else 0
#         eoq_ordering_cost = num_orders_eoq * ordering_cost
#         eoq_holding_cost = (eoq / 2) * holding_cost
#         eoq_total = eoq_ordering_cost + eoq_holding_cost

#         # =======================
#         # Non-MEIO (monthly orders)
#         # =======================
#         q_non = annual_demand / 12  # order qty each month
#         non_ordering_cost = 12 * ordering_cost
#         non_holding_cost = (q_non / 2) * holding_cost * 12 / 12  # average inventory * H
#         non_total = non_ordering_cost + non_holding_cost

#         # =======================
#         # Record
#         # =======================
#         records.append({
#             "SKU": sku,
#             "Echelon": echelon,
#             "Demand": annual_demand,
#             "Product_Cost": prod_cost,
#             "Ordering_Cost": ordering_cost,
#             "Holding_Cost_per_unit": holding_cost,
#             "EOQ": round(eoq, 2),
#             "EOQ_Ordering_Cost": round(eoq_ordering_cost, 2),
#             "EOQ_Holding_Cost": round(eoq_holding_cost, 2),
#             "EOQ_Total_Cost": round(eoq_total, 2),
#             "NonEOQ_Ordering_Cost": round(non_ordering_cost, 2),
#             "NonEOQ_Holding_Cost": round(non_holding_cost, 2),
#             "NonEOQ_Total_Cost": round(non_total, 2),
#             "Cost_Savings": round(non_total - eoq_total, 2)
#         })

#     return pd.DataFrame(records)

# # --- Run for DC → Warehouse ---
# dc_summary = compute_cost_summary(dc_warehouse_dist, echelon_col="Warehouse", demand_col="Warehouse_Monthly_Demand", demand_horizon="monthly")

# # --- Run for Warehouse → Store ---
# store_summary = compute_cost_summary(warehouse_store_dist, echelon_col="Store", demand_col="store_total_stock", demand_horizon="annual")

# # --- Combine summaries ---
# all_summary = pd.concat([dc_summary, store_summary], ignore_index=True)

# # --- Deduplicate (SKU + Echelon) ---
# all_summary = all_summary.groupby(["SKU", "Echelon"], as_index=False).first()

# print("\n--- Cost Summary (Sample) ---")
# print(all_summary.head(10).to_markdown(index=False))

# # --- Save Output ---
# OUTPUT_PATH = os.path.join(BASE_DIR, "multi_level_cost_summary.xlsx")
# all_summary.to_excel(OUTPUT_PATH, index=False)
# print(f"\n✅ Cost summary saved to {OUTPUT_PATH}")
