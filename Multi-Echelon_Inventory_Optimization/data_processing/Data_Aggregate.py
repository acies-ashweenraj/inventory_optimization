import pandas as pd

def aggregate_store_monthly(df_main, date_col='TimeWeek', value_col='Actual'):
    df = df_main.copy()
    df['Year'] = df[date_col].dt.year
    df['Month'] = df[date_col].dt.month
    store_monthly = df.groupby(['Store', 'Year', 'Month'])[value_col].sum().reset_index()
    store_warehouse_ref = df[['Store', 'Warehouse']].drop_duplicates()

    # Perform aggregation
    store_monthly = df.groupby(['Store', 'Year', 'Month'])[value_col].sum().reset_index()
    # print(store_monthly.head())
    # Group and apply rolling average
    rolling_result = (
    df
    .groupby(['Store'])  # Rolling is usually across time per store
    .apply(lambda g: g.sort_values(['Year', 'Month']).set_index(['Year', 'Month'])[[value_col]]
                .rolling(window=3, min_periods=1)
                .mean()
                .reset_index())
                .reset_index(drop=True))
    df['std_demand'] = rolling_result[value_col]
    store_monthly.rename(columns={value_col: 'Store_Monthly_Demand'}, inplace=True)
    store_monthly["std_demand"]=df["std_demand"]

    # Merge warehouse information back into aggregated data
    store_monthly = store_monthly.merge(store_warehouse_ref, on='Store', how='left')

    print(f"Store-level monthly aggregation: {store_monthly.shape}")
    return store_monthly

def aggregate_warehouse_monthly(df_main, date_col='TimeWeek', value_col='Actual'):
    df = df_main.copy()
    df['Year'] = df[date_col].dt.year
    df['Month'] = df[date_col].dt.month
    warehouse_monthly = df.groupby(['Warehouse', 'Year', 'Month'])[value_col].sum().reset_index()
    warehouse_monthly.rename(columns={value_col: 'Warehouse_Monthly_Demand'}, inplace=True)
    print(f"Warehouse-level monthly aggregation: {warehouse_monthly.shape}")
    return warehouse_monthly

def aggregate_dc_monthly(df_main, date_col='TimeWeek', value_col='Actual'):
    df = df_main.copy()
    df['Year'] = df[date_col].dt.year
    df['Month'] = df[date_col].dt.month
    dc_monthly = df.groupby(['DC', 'Year', 'Month'])[value_col].sum().reset_index()
    dc_monthly.rename(columns={value_col: 'DC_Monthly_Demand'}, inplace=True)
    print(f"DC-level monthly aggregation: {dc_monthly.shape}")
    return dc_monthly
