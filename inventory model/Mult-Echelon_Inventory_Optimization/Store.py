import pandas as pd
from operations import operations,get_ordering_cost,get_holding_cost, get_lead_time

def calculate_store_level_metrics(store_df):
    """
    Add EOQ and replenishment metrics to monthly store-level data.
    Assumes store_df has columns: Store, Year, Month, Store_Monthly_Demand
    """
    df = store_df.copy()

    results = []

    for _, row in df.iterrows():
        store = row['Store']
        demand = row['Store_Monthly_Demand']
        
        if pd.isna(demand) or demand == 0:
            continue

        ordering_cost = get_ordering_cost(store)
        holding_cost = get_holding_cost(store)
        lead_time = get_lead_time('Warehouse1', store)  # assuming one-to-one for now

        daily_demand = demand

        eoq = operations.EOQ(ordering_cost, holding_cost, demand)
        cycle_time = operations.cycle_time(eoq, demand)
        cycle_time_hr = operations.cycle_time_in_hr(cycle_time)
        full_cycles = operations.full_cycle_in_lead_time(lead_time, cycle_time)
        effective_lt = operations.effective_lead_time(lead_time, full_cycles, cycle_time)
        reorder_pt = operations.reorder_point(daily_demand, effective_lt)

        results.append({
            'Store': store,
            'Year': row['Year'],
            'Month': row['Month'],
            'Store_Monthly_Demand': demand,
            'Daily_Demand': daily_demand,
            'EOQ': eoq,
            'Cycle_Time': cycle_time,
            'Cycle_Time_Hr': cycle_time_hr,
            'Full_Cycles_LeadTime': full_cycles,
            'Effective_Lead_Time': effective_lt,
            'Reorder_Point': reorder_pt
        })

    final_df = pd.DataFrame(results)
    print(f"📦 EOQ & Replenishment metrics calculated for stores: {final_df.shape}")
    return final_df
