import pandas as pd
from operations import operations


def dc_distribution(dc_df,warehouse_df):
    # we are merging a couple of columns from dc_df and merging it with warehouse_df
    warehouse_df=warehouse_df.merge(dc_df[["key","DC_Monthly_Demand","total_stock"]],on="key",how="left")
    for i in range(len(warehouse_df)):
        warehouse_df.loc[i,"demand_split"]=warehouse_df.loc[i,"Warehouse_Monthly_Demand"]/warehouse_df.loc[i,"DC_Monthly_Demand"]
        warehouse_df.loc[i,"warehouse_total_stock"]=warehouse_df.loc[i,"demand_split"]*warehouse_df.loc[i,"total_stock"]
    return warehouse_df