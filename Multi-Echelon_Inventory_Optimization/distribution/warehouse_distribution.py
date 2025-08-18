import pandas as pd
from operations import operations


def warehouse_distribution(warehouse_df,store_df):
    # we are merging a couple of columns from warehouse_df and merging it with store_df
    store_df=store_df.merge(warehouse_df[["key","Warehouse_Monthly_Demand","warehouse_total_stock"]],on="key",how="left")
    for i in range(len(store_df)):
        store_df.loc[i,"demand_split"]=store_df.loc[i,"Store_Monthly_Demand"]/store_df.loc[i,"Warehouse_Monthly_Demand"]
        store_df.loc[i,"store_total_stock"]=store_df.loc[i,"demand_split"]*store_df.loc[i,"warehouse_total_stock"]
    return store_df