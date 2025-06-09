def aggregate_store_monthly(df, date_col='Time.[Week]', value_col='Actual'):
    df = df.copy()
    df['Year'] = df[date_col].dt.year
    df['Month'] = df[date_col].dt.month

    store_monthly = df.groupby(['Store', 'Year', 'Month'])[value_col].sum().reset_index()
    store_monthly.rename(columns={value_col: 'Store_Monthly_Demand'}, inplace=True)
    print(f"Store-level monthly aggregation: {store_monthly.shape}")
    return store_monthly

def aggregate_warehouse_monthly(df, date_col='Date', value_col='Actual'):
    df = df.copy()
    df['Year'] = df[date_col].dt.year
    df['Month'] = df[date_col].dt.month

    warehouse_monthly = df.groupby(['Warehouse', 'Year', 'Month'])[value_col].sum().reset_index()
    warehouse_monthly.rename(columns={value_col: 'Warehouse_Monthly_Demand'}, inplace=True)
    print(f" Warehouse-level monthly aggregation: {warehouse_monthly.shape}")
    return warehouse_monthly

def aggregate_dc_monthly(df, date_col='Date', value_col='Actual'):
    df = df.copy()
    df['Year'] = df[date_col].dt.year
    df['Month'] = df[date_col].dt.month

    dc_monthly = df.groupby(['DC', 'Year', 'Month'])[value_col].sum().reset_index()
    dc_monthly.rename(columns={value_col: 'DC_Monthly_Demand'}, inplace=True)
    print(f" DC-level monthly aggregation: {dc_monthly.shape}")
    return dc_monthly
