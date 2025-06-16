import pandas as pd
from operations import operations
from Preassumptions import CODE_MAP,HOLDING_COST,LEAD_TIME,ORDERING_COST

def warehouse_data(df):
    forecasted_df=df
    for i in range(len(forecasted_df)):

        ordering_cost = ORDERING_COST[CODE_MAP[forecasted_df.loc[i,"Warehouse"]]]
        holding_cost = HOLDING_COST[CODE_MAP[forecasted_df.loc[i,"Warehouse"]]]
        lead_time = LEAD_TIME[CODE_MAP[forecasted_df.loc[i,"Warehouse"]]]


        forecasted_df.loc[i,"monthly_eoq"]=operations.eoq_manual(ordering_cost,holding_cost,forecasted_df.loc[i,"Warehouse_Monthly_Demand"])

        forecasted_df.loc[i,'cycle_time']=operations.cycle_time(forecasted_df.loc[i,'monthly_eoq'],forecasted_df.loc[i,'Warehouse_Monthly_Demand'])
        forecasted_df.loc[i,"cycle_time_in_days"]=operations.cycle_time_month_to_days(forecasted_df.loc[i,"cycle_time"])
        forecasted_df.loc[i,"cycle_time_in_hr"]=operations.cycle_time_days_to_hrs(forecasted_df.loc[i,"cycle_time_in_days"])
        forecasted_df.loc[i,"full_cycles_in_lead_time"]=operations.full_cycle_in_lead_time(lead_time,forecasted_df.loc[i,"cycle_time"])
    
        forecasted_df.loc[i,"effective_lead_time"]=operations.effective_lead_time(lead_time,forecasted_df.loc[i,"full_cycles_in_lead_time"],forecasted_df.loc[i,"cycle_time"])
        forecasted_df.loc[i,"reorder_point"]=operations.reorder_point(forecasted_df.loc[i,"Warehouse_Monthly_Demand"],forecasted_df.loc[i,"effective_lead_time"])

        forecasted_df["DC"] = forecasted_df["DC"].fillna(0).astype(float).astype(int)

        dc_val = int(forecasted_df.loc[i, "DC"]) 
        year_val = forecasted_df.loc[i, "Year"]
        month_val = forecasted_df.loc[i, "Month"]
        
        forecasted_df.loc[i, "key"] = f"{dc_val}_{year_val}_{month_val}"

    return forecasted_df

