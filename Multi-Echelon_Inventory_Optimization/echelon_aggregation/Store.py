import pandas as pd
from operations import operations
from Preassumptions import CODE_MAP,HOLDING_COST,LEAD_TIME,ORDERING_COST

def store_data(df):
    forecasted_df=df
    for i in range(len(forecasted_df)):
        # daily_demand = forecasted_df.loc[i, 'Store_Monthly_Demand']
        # if pd.isna(daily_demand) or daily_demand == 0:
        #     continue  # skip this row

        ordering_cost = ORDERING_COST[CODE_MAP[forecasted_df.loc[i,"Store"]]]
        holding_cost = HOLDING_COST[CODE_MAP[forecasted_df.loc[i,"Store"]]]
        lead_time = LEAD_TIME[CODE_MAP[forecasted_df.loc[i,"Store"]]]

        # ordering_cost = operations.get_ordering_cost(forecasted_df.loc[i,"Store"])
        # holding_cost = operations.get_holding_cost(forecasted_df.loc[i,"Store"])
        # lead_time = operations.get_lead_time(forecasted_df.loc[i,"Warehouse"],forecasted_df.loc[i,"Store"])
        
        key = next((k for k, v in CODE_MAP.items() if v == "DC"), None)
        forecasted_df.loc[i,"DC"]=key
        forecasted_df.loc[i,"monthly_eoq"]=operations.eoq_manual(ordering_cost,holding_cost,forecasted_df.loc[i,"Store_Monthly_Demand"])

        forecasted_df.loc[i,'cycle_time']=operations.cycle_time(forecasted_df.loc[i,'monthly_eoq'],forecasted_df.loc[i,'Store_Monthly_Demand'])
        forecasted_df.loc[i,"cycle_time_in_days"]=operations.cycle_time_month_to_days(forecasted_df.loc[i,"cycle_time"])
        forecasted_df.loc[i,"cycle_time_in_hr"]=operations.cycle_time_days_to_hrs(forecasted_df.loc[i,"cycle_time_in_days"])
        forecasted_df.loc[i,"full_cycles_in_lead_time"]=operations.full_cycle_in_lead_time(lead_time,forecasted_df.loc[i,"cycle_time"])
    
        forecasted_df.loc[i,"effective_lead_time"]=operations.effective_lead_time(lead_time,forecasted_df.loc[i,"full_cycles_in_lead_time"],forecasted_df.loc[i,"cycle_time"])
        forecasted_df.loc[i,"reorder_point"]=operations.reorder_point(forecasted_df.loc[i,"Store_Monthly_Demand"],forecasted_df.loc[i,"effective_lead_time"])
        forecasted_df.loc[i,"key"] = forecasted_df.loc[i,"DC"].astype(str) + "_" + \
                        forecasted_df.loc[i,"Year"].astype(str) + "_" + \
                        forecasted_df.loc[i,"Month"].astype(str)
    return forecasted_df
