import pandas as pd
from operations import operations
from echelon_aggregation import common_aggregation


def warehouse_data(df):
    echelon_df=common_aggregation.aggreagation_func(df,"Warehouse")
    return echelon_df
