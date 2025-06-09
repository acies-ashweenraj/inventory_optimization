import pandas as pd
import os
from operations import operations



def weekly_data(df_filepath, ordering_cost, holding_cost, lead_time):
    forecasted_df = pd.read_csv(df_filepath)
    
    for i in range(len(forecasted_df)):
        demand = forecasted_df.loc[i, "Demand Plan"]
        weekly_eoq = operations.EOQ(ordering_cost, holding_cost, demand)
        forecasted_df.loc[i, "weekly_eoq"] = weekly_eoq
        
        cycle_time = operations.cycle_time(weekly_eoq, demand)
        forecasted_df.loc[i, 'cycle_time'] = cycle_time
        
        forecasted_df.loc[i, "cycle_time_in_hr"] = operations.cycle_time_in_hr(cycle_time)
        
        full_cycles = operations.full_cycle_in_lead_time(lead_time, cycle_time)
        forecasted_df.loc[i, "full_cycles_in_lead_time"] = full_cycles
        
        effective_lead_time = operations.effective_lead_time(lead_time, full_cycles, cycle_time)
        forecasted_df.loc[i, "effective_lead_time"] = effective_lead_time
        
        reorder_point = operations.reorder_point(demand, effective_lead_time)
        forecasted_df.loc[i, "reorder_point"] = reorder_point

    # Ensure directory exists before saving
    if not os.path.exists('data'):
        os.makedirs('data')

    forecasted_df.to_csv('data/weekly_final_data.csv', index=False)
    return forecasted_df




