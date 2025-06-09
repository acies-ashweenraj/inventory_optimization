import pandas as pd
from operations import operations


def daily_data(df_filepath,ordering_cost,holding_cost,lead_time):
    forecasted_df=pd.read_csv(df_filepath)
    for i in range(len(forecasted_df)):
        daily_demand = forecasted_df.loc[i, 'daily_demand']
        if pd.isna(daily_demand) or daily_demand == 0:
            continue  # skip this row
        # forecasted_df.loc[i,"daily_eoq"],forecasted_df.loc[i,"eoq_cost"]=operations.eoq(ordering_cost,holding_cost,forecasted_df.loc[i,"Demand Plan"])
        forecasted_df.loc[i,"daily_eoq"]=operations.EOQ(ordering_cost,holding_cost,forecasted_df.loc[i,"Demand Plan"])

        forecasted_df.loc[i,'cycle_time']=operations.cycle_time(forecasted_df.loc[i,'daily_eoq'],forecasted_df.loc[i,'daily_demand'])

        forecasted_df.loc[i,"cycle_time_in_hr"]=operations.cycle_time_in_hr(forecasted_df.loc[i,"cycle_time"])
        forecasted_df.loc[i,"full_cycles_in_lead_time"]=operations.full_cycle_in_lead_time(lead_time,forecasted_df.loc[i,"cycle_time"])
    
        forecasted_df.loc[i,"effective_lead_time"]=operations.effective_lead_time(lead_time,forecasted_df.loc[i,"full_cycles_in_lead_time"],forecasted_df.loc[i,"cycle_time"])
        forecasted_df.loc[i,"reorder_point"]=operations.reorder_point(forecasted_df.loc[i,"daily_demand"],forecasted_df.loc[i,"effective_lead_time"])
    return forecasted_df

def daily_to_weekly(df_filepath):
    forecasted_df=pd.read_csv(df_filepath)
    row=0
    for i in range(len(forecasted_df)):
        demand=forecasted_df.loc[i,'Demand Plan']
        date=pd.to_datetime(forecasted_df.loc[i,'Week'])
        for j in range(0,7):
            forecasted_df.loc[row,'day']=date+pd.Timedelta(days=j)
            forecasted_df.loc[row,'daily_demand']=demand/7
            row+=1
        # print(forecasted_df.head(20))
    forecasted_df.to_csv('data/daily_prepared_data.csv',index=False)
    # return forecasted_df
    