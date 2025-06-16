import pandas as pd
from math import floor
from datetime import datetime, timedelta
from Preassumptions import WAREHOUSE_SCHEDULE  

def warehouses_schedule(df):
    ss_df = df.sort_values(["Warehouse", "Year", "Month"]).reset_index(drop=True)
    
    for i in range(len(ss_df)):
        warehouse = ss_df.loc[i, "Warehouse"]
        dc = ss_df.loc[i, "DC"]
        year = int(ss_df.loc[i, "Year"])
        month = int(ss_df.loc[i, "Month"])
        
        total_demand = ss_df.loc[i, "Warehouse_Monthly_Demand"]
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
                "From": dc,
                "Echelon": warehouse,
                "Year": year,
                "Month": month,
                "Date_Time": order_dates[j],
                "Quantity": eoq
            }
            WAREHOUSE_SCHEDULE.append(order)


        if balance_demand > 0:
            balance_order_date = first_order_date + timedelta(days=no_of_orders * cycle)
            order = {
                "From": dc,
                "Echelon": warehouse,
                "Year": year,
                "Month": month,
                "Date_Time": balance_order_date,
                "Quantity": balance_demand
            }
            WAREHOUSE_SCHEDULE.append(order)

