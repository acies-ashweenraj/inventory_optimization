# from Preassumptions import HOLDING_COST, ORDERING_COST, CODE_MAP
from server.Preassumptions import HOLDING_COST, ORDERING_COST
import pandas as pd

def non_eoq_cost_function(df):
    cost_df = df.copy()

    cost_df["Echelon"] = cost_df["Store"]
    cost_df["From"] = cost_df["Warehouse"]

    cost_df["total_cost_non_eoq"] = 0.0

    for i in range(len(cost_df)):
        echelon_code = cost_df.loc[i, "Echelon"]
        echelon_name = echelon_code

        # holding_cost = HOLDING_COST[echelon_name]
        # ordering_cost = ORDERING_COST[echelon_name]
        holding_cost = HOLDING_COST.get(echelon_name, 0)
        ordering_cost = ORDERING_COST.get(echelon_name, 0)
        stock = cost_df.loc[i, "store_total_stock"]
        cycle_days = cost_df.loc[i, "cycle_time_in_days"]

        total_cost = ordering_cost + (stock / 2) * (holding_cost )
        cost_df.loc[i, "total_cost_non_eoq"] = total_cost

    final_cost_df = cost_df.groupby(["From", "Echelon", "Year", "Month"])["total_cost_non_eoq"].sum().reset_index()

    return final_cost_df
