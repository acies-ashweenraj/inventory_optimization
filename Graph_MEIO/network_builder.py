import pandas as pd
from entities import Node, Edge, Metrics
from operations import operations  # Import your helper class

def build_network(network_df, cost_df, lead_df, forecasted_df):
    nodes = {}
    edges = []

    # Convert week to datetime
    forecasted_df['week'] = pd.to_datetime(forecasted_df['week'])

    # Normalize keys to match
    forecasted_df['node'] = forecasted_df['node'].astype(str).str.strip().str.upper()
    forecasted_df['sku'] = forecasted_df['sku'].astype(str).str.strip().str.upper()
    network_df['node_name'] = network_df['node_name'].astype(str).str.strip().str.upper()
    cost_df['node'] = cost_df['node'].astype(str).str.strip().str.upper()
    cost_df['sku'] = cost_df['sku'].astype(str).str.strip().str.upper()

    # Debug prints to inspect matching
    print("🔍 Unique node values in forecasted_df:", forecasted_df['node'].unique())
    print("🔍 Unique node names in network_df:", network_df['node_name'].unique())

    # Loop over each node
    for _, row in network_df.iterrows():
        node_code = row["node_code"]
        node_name = row["node_name"]
        node_type = row["node_type"]
        capacity = row["capacity"]

        print(f"🔁 Checking node: {node_name}")
        relevant_demand = forecasted_df[forecasted_df["node"] == node_name]
        print(f"   ✅ Demand rows found: {len(relevant_demand)}")

        sku_list = relevant_demand["sku"].unique().tolist()

        cost_row = cost_df[(cost_df["node"] == node_name) & (cost_df["sku"].isin(sku_list))]

        if not cost_row.empty:
            cost_row = cost_row.iloc[0]
            holding_cost = cost_row["holding_cost_unitmonth"]
            ordering_cost = cost_row["ordering_cost_order"]
        else:
            holding_cost = ordering_cost = 0
            print(f"[WARNING] No cost data found for node: {node_name} and SKUs: {sku_list}")

        metric_objects = []
        for sku in sku_list:
            sku_demand = relevant_demand[relevant_demand["sku"] == sku].copy()
            sku_demand = sku_demand.sort_values("week")
            sku_demand.set_index("week", inplace=True)

            monthly_demand = sku_demand["actual"].resample("ME").sum()
            avg_demand = monthly_demand.mean()
            std_demand = monthly_demand.std()

            if avg_demand == 0 or pd.isna(avg_demand):
                continue

            try:
                eoq = operations.EOQ(ordering_cost, holding_cost, avg_demand)
            except Exception as e:
                print(f"[ERROR] EOQ calculation failed for node {node_name}, SKU {sku}: {e}")
                eoq = 0

            z_score = 1.65
            safety_stock = operations.safety_stock(z_score, 1, std_demand)
            rop = operations.reorder_point(avg_demand, 1)

            avg_inventory = (eoq / 2) + safety_stock
            inv_turnover = 12 * avg_demand / avg_inventory
            coverage_time = avg_inventory / avg_demand if avg_demand else 0

            metrics = Metrics(
                sku_id=sku,
                demand=avg_demand,
                safety_stock=safety_stock,
                rop=rop,
                inventory_turnover_ratio=inv_turnover,
                average_inventory=avg_inventory,
                stock_coverage_time=coverage_time,
                eoq=eoq,
                std_demand=std_demand
            )
            metric_objects.append(metrics)

        node_obj = Node(
            code=node_code,
            name=node_name,
            type=node_type,
            holding_cost=holding_cost,
            ordering_cost=ordering_cost,
            capacity=capacity,
            service_level=95,
            metrics=metric_objects,
            sku_list=sku_list
        )

        nodes[node_code] = node_obj

    # Build edges
    for _, row in lead_df.iterrows():
        edge = Edge(
            source=row["source_node"].strip().upper(),
            target=row["target_node"].strip().upper(),
            lead_time=row["lead_time_days"],
            reverse_flow=False
        )
        edges.append(edge)

    return nodes, edges
