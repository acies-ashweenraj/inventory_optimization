import pandas as pd
from operations import operations
from Preassumptions import CODE_MAP,HOLDING_COST,LEAD_TIME,ORDERING_COST,Z_SCORE


def dc_data(df):
    echelon_df=df
    for i in range(len(echelon_df)):

        ordering_cost = ORDERING_COST[CODE_MAP[echelon_df.loc[i,"DC"]]]
        holding_cost = HOLDING_COST[CODE_MAP[echelon_df.loc[i,"DC"]]]
        lead_time = LEAD_TIME[CODE_MAP[echelon_df.loc[i,"DC"]]]

        # echelon_df.loc[i,"monthly_eoq"]=operations.eoq_manual(ordering_cost,holding_cost,echelon_df.loc[i,"DC_Monthly_Demand"])

        echelon_df.loc[i,"monthly_eoq"]=operations.EOQ(ordering_cost,holding_cost,echelon_df.loc[i,"DC_Monthly_Demand"])

        echelon_df.loc[i,'cycle_time']=operations.cycle_time(echelon_df.loc[i,'monthly_eoq'],echelon_df.loc[i,'DC_Monthly_Demand'])
        echelon_df.loc[i,"cycle_time_in_days"]=operations.cycle_time_month_to_days(echelon_df.loc[i,"cycle_time"])
        echelon_df.loc[i,"cycle_time_in_hr"]=operations.cycle_time_days_to_hrs(echelon_df.loc[i,"cycle_time_in_days"])
        echelon_df.loc[i,"full_cycles_in_lead_time"]=operations.full_cycle_in_lead_time(lead_time,echelon_df.loc[i,"cycle_time"])
    
        echelon_df.loc[i,"effective_lead_time"]=operations.effective_lead_time(lead_time,echelon_df.loc[i,"full_cycles_in_lead_time"],echelon_df.loc[i,"cycle_time"])
        echelon_df.loc[i,"reorder_point"]=operations.reorder_point(echelon_df.loc[i,"DC_Monthly_Demand"],echelon_df.loc[i,"effective_lead_time"])
        echelon_df.loc[i,"safety_stock"] = operations.safety_stock(Z_SCORE,lead_time,echelon_df.loc[i,"std_demand"])
        echelon_df.loc[i,"total_stock"] = echelon_df.loc[i,"safety_stock"] + echelon_df.loc[i,"DC_Monthly_Demand"]
        echelon_df.loc[i,"key"] = echelon_df.loc[i,"DC"].astype(str) + "_" + \
                        echelon_df.loc[i,"Year"].astype(str) + "_" + \
                        echelon_df.loc[i,"Month"].astype(str)
    return echelon_df

