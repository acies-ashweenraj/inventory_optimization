import pandas as pd

def aggregate_store_monthly(df_main, date_col='TimeWeek', value_col='Actual'):
    df = df_main.copy()
    df['Year'] = df[date_col].dt.year
    df['Month'] = df[date_col].dt.month
    store_monthly = df.groupby(['Store', 'Year', 'Month'])[value_col].sum().reset_index()
    store_warehouse_ref = df[['Store', 'Warehouse']].drop_duplicates()

    # Perform aggregation
    store_monthly = df.groupby(['Store', 'Year', 'Month'])[value_col].sum().reset_index()
    store_monthly.rename(columns={value_col: 'Store_Monthly_Demand'}, inplace=True)

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
