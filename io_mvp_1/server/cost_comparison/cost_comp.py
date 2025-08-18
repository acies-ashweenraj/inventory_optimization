import pandas as pd

def calculate_costs(schedule_df, product_master_df, node_cost_df, transport_cost_df=None):
    """
    schedule_df: output from scheduling (orders with From, Echelon, SKU, Quantity, Date_Time)
    product_master_df: contains SKU details like Unit_Cost, Category, etc.
    node_cost_df: contains Ordering Cost & Holding Cost for each node
    transport_cost_df: optional, contains From, To, Cost_per_Unit
    """

    # --- Merge Node Costs ---
    merged = schedule_df.merge(node_cost_df, left_on="Echelon", right_on="Node", how="left")

    # --- Merge Product Costs ---
    if "SKU" in product_master_df.columns:
        merged = merged.merge(product_master_df, on="SKU", how="left")

    # --- Ordering Cost ---
    merged["Ordering_Cost"] = merged["Ordering Cost"]  # from node master

    # --- Holding Cost ---
    # Assuming holding cost applies to inventory carried (EOQ/2 * holding_cost_per_unit * unit_price)
    if "Unit_Cost" in merged.columns:
        merged["Holding_Cost"] = (merged["Quantity"] / 2) * merged["Holding Cost"] * merged["Unit_Cost"]
    else:
        merged["Holding_Cost"] = (merged["Quantity"] / 2) * merged["Holding Cost"]

    # --- Transport Cost (if transport cost sheet given) ---
    if transport_cost_df is not None:
        merged = merged.merge(
            transport_cost_df, left_on=["From", "Echelon"], right_on=["From", "To"], how="left"
        )
        merged["Transport_Cost"] = merged["Quantity"] * merged["Cost_per_Unit"]
    else:
        merged["Transport_Cost"] = 0

    # --- Total Cost ---
    merged["Total_Cost"] = merged["Ordering_Cost"] + merged["Holding_Cost"] + merged["Transport_Cost"]

    # --- Group by Node, SKU, Month ---
    cost_summary = (
        merged.groupby(["From", "Echelon", "SKU", "Year", "Month"])
        [["Ordering_Cost", "Holding_Cost", "Transport_Cost", "Total_Cost"]]
        .sum()
        .reset_index()
    )

    return merged, cost_summary