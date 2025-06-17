import pandas as pd
from math import floor
from datetime import datetime, timedelta
from Preassumptions import STORE_SCHEDULE, WAREHOUSE_SCHEDULE

def common_schedule_func(df, echelon_type):
    if echelon_type.lower() == "warehouse":
        echelon_col = "Warehouse"
        parent_col = "DC"
        demand_col = "Warehouse_Monthly_Demand"
        output = WAREHOUSE_SCHEDULE
    elif echelon_type.lower() == "store":
        echelon_col = "Store"
        parent_col = "Warehouse"
        demand_col = "Store_Monthly_Demand"
        output = STORE_SCHEDULE
    else:
        raise ValueError("Invalid echelon_type. Use 'warehouse' or 'store'.")

    ss_df = df.sort_values([echelon_col, "Year", "Month"]).reset_index(drop=True)

    for i in range(len(ss_df)):
        echelon_name = ss_df.loc[i, echelon_col]
        parent_name = ss_df.loc[i, parent_col]
        year = int(ss_df.loc[i, "Year"])
        month = int(ss_df.loc[i, "Month"])

        total_demand = ss_df.loc[i, demand_col]
        eoq = ss_df.loc[i, "monthly_eoq"]
        cycle = int(ss_df.loc[i, "cycle_time_in_days"])
        full_cycles = int(ss_df.loc[i, "full_cycles_in_lead_time"])
        days_before_start = cycle * full_cycles

        no_of_orders = floor(total_demand / eoq)
        balance_demand = total_demand % eoq

        month_start = datetime(year, month, 1)
        first_order_date = month_start - timedelta(days=days_before_start)
        order_dates = [first_order_date + timedelta(days=j * cycle) for j in range(no_of_orders)]

        for j in range(no_of_orders):
            order = {
                "From": parent_name,
                "Echelon": echelon_name,
                "Year": year,
                "Month": month,
                "Date_Time": order_dates[j],
                "Quantity": eoq
            }
            output.append(order)

        if balance_demand > 0:
            balance_order_date = first_order_date + timedelta(days=no_of_orders * cycle)
            order = {
                "From": parent_name,
                "Echelon": echelon_name,
                "Year": year,
                "Month": month,
                "Date_Time": balance_order_date,
                "Quantity": balance_demand
            }
            output.append(order)
