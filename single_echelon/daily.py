import pandas as pd
from operations import operations


def daily_data(df_filepath,ordering_cost,holding_cost,lead_time):
    echelon_df=pd.read_csv(df_filepath)
    for i in range(len(echelon_df)):
        daily_demand = echelon_df.loc[i, 'daily_demand']
        if pd.isna(daily_demand) or daily_demand == 0:
            continue  # skip this row
        # echelon_df.loc[i,"daily_eoq"],echelon_df.loc[i,"eoq_cost"]=operations.eoq(ordering_cost,holding_cost,echelon_df.loc[i,"Demand Plan"])
        echelon_df.loc[i,"daily_eoq"]=operations.EOQ(ordering_cost,holding_cost,echelon_df.loc[i,"Demand Plan"])

        echelon_df.loc[i,'cycle_time']=operations.cycle_time(echelon_df.loc[i,'daily_eoq'],echelon_df.loc[i,'daily_demand'])

        echelon_df.loc[i,"cycle_time_in_hr"]=operations.cycle_time_in_hr(echelon_df.loc[i,"cycle_time"])
        echelon_df.loc[i,"full_cycles_in_lead_time"]=operations.full_cycle_in_lead_time(lead_time,echelon_df.loc[i,"cycle_time"])
    
        echelon_df.loc[i,"effective_lead_time"]=operations.effective_lead_time(lead_time,echelon_df.loc[i,"full_cycles_in_lead_time"],echelon_df.loc[i,"cycle_time"])
        echelon_df.loc[i,"reorder_point"]=operations.reorder_point(echelon_df.loc[i,"daily_demand"],echelon_df.loc[i,"effective_lead_time"])
    return echelon_df

def daily_to_weekly(df_filepath):
    echelon_df=pd.read_csv(df_filepath)
    row=0
    for i in range(len(echelon_df)):
        demand=echelon_df.loc[i,'Demand Plan']
        date=pd.to_datetime(echelon_df.loc[i,'Week'])
        for j in range(0,7):
            echelon_df.loc[row,'day']=date+pd.Timedelta(days=j)
            echelon_df.loc[row,'daily_demand']=demand/7
            row+=1
        # print(echelon_df.head(20))
    echelon_df.to_csv('data/daily_prepared_data.csv',index=False)
    # return echelon_df
    