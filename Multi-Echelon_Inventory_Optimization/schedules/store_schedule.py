import pandas as pd
from math import floor
from datetime import datetime, timedelta
from Preassumptions import STORE_SCHEDULE  # Assumes SCHEDULE = [] is defined there

def stores_schedule(df):
    # No need to group if each row is monthly per store
    ss_df = df.sort_values(["Store", "Year", "Month"]).reset_index(drop=True)
    
    for i in range(len(ss_df)):
        store = ss_df.loc[i, "Store"]
        warehouse = ss_df.loc[i, "Warehouse"]
        year = int(ss_df.loc[i, "Year"])
        month = int(ss_df.loc[i, "Month"])
        
        total_demand = ss_df.loc[i, "Store_Monthly_Demand"]
        eoq = ss_df.loc[i, "monthly_eoq"]
        cycle = int(ss_df.loc[i, "cycle_time_in_days"])
        full_cycles = int(ss_df.loc[i, "full_cycles_in_lead_time"])
        days_before_start = cycle * full_cycles
        
        no_of_orders = floor(total_demand / eoq)
        balance_demand = total_demand % eoq
        
        # Get first of the month
        month_start = datetime(year, month, 1)
        # First order date
        first_order_date = month_start - timedelta(days=days_before_start)
        
        # Create order dates
        order_dates = [first_order_date + timedelta(days=j * cycle) for j in range(no_of_orders)]

        # Append full EOQ orders
        for j in range(no_of_orders):
            order = {
                "From": warehouse,
                "Echelon": store,
                "Year": year,
                "Month": month,
                "Date_Time": order_dates[j],
                "Quantity": eoq
            }
            STORE_SCHEDULE.append(order)

        # Add balance order if any
        if balance_demand > 0:
            balance_order_date = first_order_date + timedelta(days=no_of_orders * cycle)
            order = {
                "From": warehouse,
                "Echelon": store,
                "Year": year,
                "Month": month,
                "Date_Time": balance_order_date,
                "Quantity": balance_demand
            }
            STORE_SCHEDULE.append(order)

