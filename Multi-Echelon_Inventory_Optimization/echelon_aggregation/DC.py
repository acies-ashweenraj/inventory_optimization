import pandas as pd
from operations import operations
from Preassumptions import CODE_MAP,HOLDING_COST,LEAD_TIME,ORDERING_COST,Z_SCORE


def dc_data(df):
    forecasted_df=df
    for i in range(len(forecasted_df)):
        # daily_demand = forecasted_df.loc[i, 'Store_Monthly_Demand']
        # if pd.isna(daily_demand) or daily_demand == 0:
        #     continue  # skip this row

        ordering_cost = ORDERING_COST[CODE_MAP[forecasted_df.loc[i,"DC"]]]
        holding_cost = HOLDING_COST[CODE_MAP[forecasted_df.loc[i,"DC"]]]
        lead_time = LEAD_TIME[CODE_MAP[forecasted_df.loc[i,"DC"]]]

        forecasted_df.loc[i,"monthly_eoq"]=operations.eoq_manual(ordering_cost,holding_cost,forecasted_df.loc[i,"DC_Monthly_Demand"])

        forecasted_df.loc[i,'cycle_time']=operations.cycle_time(forecasted_df.loc[i,'monthly_eoq'],forecasted_df.loc[i,'DC_Monthly_Demand'])
        forecasted_df.loc[i,"cycle_time_in_days"]=operations.cycle_time_month_to_days(forecasted_df.loc[i,"cycle_time"])
        forecasted_df.loc[i,"cycle_time_in_hr"]=operations.cycle_time_days_to_hrs(forecasted_df.loc[i,"cycle_time_in_days"])
        forecasted_df.loc[i,"full_cycles_in_lead_time"]=operations.full_cycle_in_lead_time(lead_time,forecasted_df.loc[i,"cycle_time"])
    
        forecasted_df.loc[i,"effective_lead_time"]=operations.effective_lead_time(lead_time,forecasted_df.loc[i,"full_cycles_in_lead_time"],forecasted_df.loc[i,"cycle_time"])
        forecasted_df.loc[i,"reorder_point"]=operations.reorder_point(forecasted_df.loc[i,"DC_Monthly_Demand"],forecasted_df.loc[i,"effective_lead_time"])
        forecasted_df.loc[i,"safety_stock"] = operations.safety_stock(Z_SCORE,lead_time,forecasted_df.loc[i,"std_demand"])
        forecasted_df.loc[i,"total_stock"] = forecasted_df.loc[i,"safety_stock"] + forecasted_df.loc[i,"DC_Monthly_Demand"]
        forecasted_df["key"] = forecasted_df["DC"].astype(str) + "_" + \
                        forecasted_df["Year"].astype(str) + "_" + \
                        forecasted_df["Month"].astype(str)
    return forecasted_df

# def store_data(df_filepath,ordering_cost,holding_cost,lead_time):
