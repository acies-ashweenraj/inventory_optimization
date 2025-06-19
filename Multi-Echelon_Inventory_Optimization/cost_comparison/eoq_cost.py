import pandas as pd
from schedules import store_schedule
from Preassumptions import HOLDING_COST, ORDERING_COST, CODE_MAP
from echelon_aggregation import Store

def eoq_cost_function(df, cyc_df):

    calc_df = df.copy().reset_index(drop=True)
    cycle_df = cyc_df.copy().reset_index(drop=True)

    cycle_df.rename(columns={"Store": "Echelon"}, inplace=True)

    merged_df = pd.merge(
        calc_df,
        cycle_df[["Echelon", "Year", "Month", "cycle_time_in_days"]],
        on=["Echelon", "Year", "Month"],
        how="left"
    )

    total_costs = []
    for i, row in merged_df.iterrows():
        echelon_code = row["Echelon"]
        echelon_name = CODE_MAP[echelon_code]
        holding_cost = HOLDING_COST[echelon_name]
        ordering_cost = ORDERING_COST[echelon_name]
        quantity = row["Quantity"]
        cycle_time = row["cycle_time_in_days"]

        total_cost = ordering_cost + (quantity / 2) * ((holding_cost * cycle_time) / 30)
        total_costs.append(total_cost)

    merged_df["total_cost_eoq"] = total_costs

    monthly_total_cost_df = merged_df.groupby(
        ["From", "Echelon", "Year", "Month"]
    )["total_cost_eoq"].sum().reset_index()

    return monthly_total_cost_df

