import pandas as pd
from operations import operations
from Preassumptions import CODE_MAP,HOLDING_COST,LEAD_TIME,ORDERING_COST

def store_data(df):
    echelon_df=df
    for i in range(len(echelon_df)):

        ordering_cost = ORDERING_COST[CODE_MAP[echelon_df.loc[i,"Store"]]]
        holding_cost = HOLDING_COST[CODE_MAP[echelon_df.loc[i,"Store"]]]
        lead_time = LEAD_TIME[CODE_MAP[echelon_df.loc[i,"Store"]]]
        
        key = next((k for k, v in CODE_MAP.items() if v == "DC"), None)
        echelon_df.loc[i,"DC"]=key
        # echelon_df.loc[i,"monthly_eoq"]=operations.eoq_manual(ordering_cost,holding_cost,echelon_df.loc[i,"Store_Monthly_Demand"])
        echelon_df.loc[i,"monthly_eoq"]=operations.EOQ(ordering_cost,holding_cost,echelon_df.loc[i,"Store_Monthly_Demand"])

        echelon_df.loc[i,'cycle_time']=operations.cycle_time(echelon_df.loc[i,'monthly_eoq'],echelon_df.loc[i,'Store_Monthly_Demand'])
        echelon_df.loc[i,"cycle_time_in_days"]=operations.cycle_time_month_to_days(echelon_df.loc[i,"cycle_time"])
        echelon_df.loc[i,"cycle_time_in_hr"]=operations.cycle_time_days_to_hrs(echelon_df.loc[i,"cycle_time_in_days"])
        echelon_df.loc[i,"full_cycles_in_lead_time"]=operations.full_cycle_in_lead_time(lead_time,echelon_df.loc[i,"cycle_time"])
    
        echelon_df.loc[i,"effective_lead_time"]=operations.effective_lead_time(lead_time,echelon_df.loc[i,"full_cycles_in_lead_time"],echelon_df.loc[i,"cycle_time"])
        echelon_df.loc[i,"reorder_point"]=operations.reorder_point(echelon_df.loc[i,"Store_Monthly_Demand"],echelon_df.loc[i,"effective_lead_time"])

        dc_val = int(echelon_df.loc[i, "DC"]) 
        year_val = echelon_df.loc[i, "Year"]
        month_val = echelon_df.loc[i, "Month"]
        
        echelon_df.loc[i, "key"] = f"{dc_val}_{year_val}_{month_val}"
    return echelon_df
