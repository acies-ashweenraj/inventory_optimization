import pandas as pd
from operations import operations


def store_data(df_filepath,ordering_cost,holding_cost,lead_time):
    forecasted_df=pd.read_csv(df_filepath)
    for i in range(len(forecasted_df)):
        daily_demand = forecasted_df.loc[i, 'daily_demand']
        if pd.isna(daily_demand) or daily_demand == 0:
            continue  # skip this row

        ordering_cost = operations.get_ordering_cost(forecasted_df.loc[i,"Store"])
        holding_cost = operations.get_holding_cost(forecasted_df.loc[i,"Store"])
        lead_time = operations.get_lead_time(forecasted_df.loc[i,"Warehouse"],forecasted_df.loc[i,"Store"])
        
        # forecasted_df.loc[i,"daily_eoq"],forecasted_df.loc[i,"eoq_cost"]=operations.eoq(ordering_cost,holding_cost,forecasted_df.loc[i,"Demand Plan"])
        forecasted_df.loc[i,"daily_eoq"]=operations.EOQ(ordering_cost,holding_cost,forecasted_df.loc[i,"Demand Plan"])

        forecasted_df.loc[i,'cycle_time']=operations.cycle_time(forecasted_df.loc[i,'daily_eoq'],forecasted_df.loc[i,'daily_demand'])
        forecasted_df.loc[i,"cycle_time_in_days"]=operations.cycle_time_month_to_days(forecasted_df.loc[i,"cycle_time"])
        forecasted_df.loc[i,"cycle_time_in_hr"]=operations.cycle_time_days_to_hrs(forecasted_df.loc[i,"cycle_time_in_days"])
        forecasted_df.loc[i,"full_cycles_in_lead_time"]=operations.full_cycle_in_lead_time(lead_time,forecasted_df.loc[i,"cycle_time"])
    
        forecasted_df.loc[i,"effective_lead_time"]=operations.effective_lead_time(lead_time,forecasted_df.loc[i,"full_cycles_in_lead_time"],forecasted_df.loc[i,"cycle_time"])
        forecasted_df.loc[i,"reorder_point"]=operations.reorder_point(forecasted_df.loc[i,"daily_demand"],forecasted_df.loc[i,"effective_lead_time"])
    return forecasted_df