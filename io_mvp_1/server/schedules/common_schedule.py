# import pandas as pd
# from math import floor,ceil
# from datetime import datetime, timedelta
# from server.Preassumptions import STORE_SCHEDULE, WAREHOUSE_SCHEDULE

# def common_schedule_func(df, echelon_type):
#     if echelon_type.lower() == "warehouse":
#         echelon_col = "Warehouse"
#         parent_col = "DC"
#         demand_col = "Warehouse_Monthly_Demand"
#         output = WAREHOUSE_SCHEDULE
#     elif echelon_type.lower() == "store":
#         echelon_col = "Store"
#         parent_col = "Warehouse"
#         demand_col = "Store_Monthly_Demand"
#         output = STORE_SCHEDULE
#     else:
#         raise ValueError("Invalid echelon_type. Use 'warehouse' or 'store'.")

#     ss_df = df.sort_values([echelon_col, "Year", "Month","ItemStat_Item"]).reset_index(drop=True)

#     for i in range(len(ss_df)):
#         echelon_name = ss_df.loc[i, echelon_col]
#         parent_name = ss_df.loc[i, parent_col]
#         year = int(ss_df.loc[i, "Year"])
#         month = int(ss_df.loc[i, "Month"])
#         SKU = str(ss_df.loc[i,"ItemStat_Item"])

#         total_demand = ss_df.loc[i, demand_col]
#         eoq = ss_df.loc[i, "monthly_eoq"]
#         cycle = int(ss_df.loc[i, "cycle_time_in_days"])
#         full_cycles = int(ss_df.loc[i, "full_cycles_in_lead_time"])
#         days_before_start = cycle * full_cycles

#         no_of_orders = floor(total_demand / eoq)
#         balance_demand = total_demand % eoq

#         month_start = datetime(year, month, 1)
#         first_order_date = month_start - timedelta(days=days_before_start)
#         order_dates = [first_order_date + timedelta(days=j * cycle) for j in range(no_of_orders)]

#         for j in range(no_of_orders):
#             order = {
#                 "From": parent_name,
#                 "Echelon": echelon_name,
#                 "Year": year,
#                 "Month": month,
#                 "Date_Time": order_dates[j],
#                 "SKU" : SKU,
#                 "Quantity": ceil(eoq)
#             }
#             output.append(order)

#         if balance_demand > 0:
#             balance_order_date = first_order_date + timedelta(days=no_of_orders * cycle)
#             order = {
#                 "From": parent_name,
#                 "Echelon": echelon_name,
#                 "Year": year,
#                 "Month": month,
#                 "Date_Time": balance_order_date,
#                 "SKU" : SKU,
#                 "Quantity": ceil(balance_demand)
#             }
#             output.append(order)

import pandas as pd
from math import ceil
from datetime import datetime, timedelta
from calendar import monthrange
from server.Preassumptions import STORE_SCHEDULE, WAREHOUSE_SCHEDULE

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

    ss_df = df.sort_values([echelon_col, "Year", "Month", "ItemStat_Item"]).reset_index(drop=True)

    for i in range(len(ss_df)):
        echelon_name = ss_df.loc[i, echelon_col]
        parent_name = ss_df.loc[i, parent_col]
        year = int(ss_df.loc[i, "Year"])
        month = int(ss_df.loc[i, "Month"])
        SKU = str(ss_df.loc[i, "ItemStat_Item"])

        total_demand = ss_df.loc[i, demand_col]
        eoq = ss_df.loc[i, "monthly_eoq"]
        cycle_days = int(ss_df.loc[i, "cycle_time_in_days"])
        full_cycles = int(ss_df.loc[i, "full_cycles_in_lead_time"])

        if total_demand <= 0 or eoq <= 0:
            continue

         # --- number of orders ---
        num_orders = total_demand // eoq
        balance_demand = total_demand % eoq
        if balance_demand > 0:
            num_orders += 1
        num_orders = int(num_orders)

        # --- month boundaries ---
        days_in_month = monthrange(year, month)[1]
        month_start = datetime(year, month, 1)
        month_end = datetime(year, month, days_in_month)

        # --- spread evenly across the month (not just from the 1st) ---
        interval = days_in_month / num_orders
        planned_dates = [month_start + timedelta(days=round((j + 0.5) * interval)) 
                         for j in range(num_orders)]  
        # ↑ put orders in the middle of each interval instead of stacking on day 1

        # --- apply lead time shift ---
        lead_shift = cycle_days * full_cycles
        order_dates = [d - timedelta(days=lead_shift) for d in planned_dates]

        # --- clip back to month start if shifted too early ---
        order_dates = [max(month_start, d) for d in order_dates]

        # --- assign quantities ---
        for j, od in enumerate(order_dates):
            if j < num_orders - 1 or balance_demand == 0:
                qty = ceil(eoq)
            else:
                qty = ceil(balance_demand)
            output.append({
                "From": parent_name,
                "Echelon": echelon_name,
                "Year": year,
                "Month": month,
                "Date_Time": od,
                "SKU": SKU,
                "Quantity": qty
            })

    return pd.DataFrame(output)