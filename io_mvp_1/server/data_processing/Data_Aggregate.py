import pandas as pd

def aggregate_store_monthly(df_main, date_col='Order Date', value_col='Actual', sku_col="ItemStat_Item"):
    df = df_main.copy()

    if date_col not in df.columns:
        raise KeyError(f"Expected date column '{date_col}' not found. Available columns: {df.columns.tolist()}")

    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df['Year'] = df[date_col].dt.year
    df['Month'] = df[date_col].dt.month

    store_monthly = df.groupby(['Store', 'Year', 'Month', sku_col])[value_col].sum().reset_index()
    store_warehouse_ref = df[['Store', 'Warehouse', 'DC']].drop_duplicates()

    rolling_result = (
        df.groupby(['Store'])
          .apply(lambda g: g.sort_values([date_col]).set_index([date_col])[[value_col]]
                  .rolling(window=3, min_periods=1).mean()
                  .reset_index())
          .reset_index(drop=True)
    )

    df['std_demand'] = rolling_result[value_col]
    store_monthly.rename(columns={value_col: 'Store_Monthly_Demand'}, inplace=True)
    store_monthly["std_demand"] = df["std_demand"]

    store_monthly = store_monthly.merge(store_warehouse_ref, on='Store', how='left')

    print(f"Store-level monthly aggregation: {store_monthly.shape}")
    return store_monthly


def aggregate_warehouse_monthly(df_main, date_col='Order Date', value_col='Actual', sku_col="ItemStat_Item"):
    df = df_main.copy()

    if date_col not in df.columns:
        raise KeyError(f"Expected date column '{date_col}' not found. Available columns: {df.columns.tolist()}")

    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df['Year'] = df[date_col].dt.year
    df['Month'] = df[date_col].dt.month

    warehouse_monthly = df.groupby(['Warehouse', 'Year', 'Month', sku_col])[value_col].sum().reset_index()
    warehouse_dc_ref = df[['DC', 'Warehouse']].drop_duplicates()

    rolling_result = (
        df.groupby(['Warehouse'])
          .apply(lambda g: g.sort_values([date_col]).set_index([date_col])[[value_col]]
                  .rolling(window=3, min_periods=1).mean()
                  .reset_index())
          .reset_index(drop=True)
    )

    df['std_demand'] = rolling_result[value_col]
    warehouse_monthly.rename(columns={value_col: 'Warehouse_Monthly_Demand'}, inplace=True)
    warehouse_monthly["std_demand"] = df["std_demand"]

    warehouse_monthly = warehouse_monthly.merge(warehouse_dc_ref, on='Warehouse', how='left')

    print(f"Warehouse-level monthly aggregation: {warehouse_monthly.shape}")
    return warehouse_monthly


def aggregate_dc_monthly(df_main, date_col='Order Date', value_col='Actual', sku_col="ItemStat_Item"):
    df = df_main.copy()

    if date_col not in df.columns:
        raise KeyError(f"Expected date column '{date_col}' not found. Available columns: {df.columns.tolist()}")

    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df['Year'] = df[date_col].dt.year
    df['Month'] = df[date_col].dt.month

    dc_monthly = df.groupby(['DC', 'Year', 'Month', sku_col])[value_col].sum().reset_index()

    rolling_result = (
        df.groupby(['DC'])
          .apply(lambda g: g.sort_values([date_col]).set_index([date_col])[[value_col]]
                  .rolling(window=3, min_periods=1).mean()
                  .reset_index())
          .reset_index(drop=True)
    )

    df['std_demand'] = rolling_result[value_col]
    dc_monthly.rename(columns={value_col: 'DC_Monthly_Demand'}, inplace=True)
    dc_monthly["std_demand"] = df["std_demand"]

    print(f"DC-level monthly aggregation: {dc_monthly.shape}")
    return dc_monthly
