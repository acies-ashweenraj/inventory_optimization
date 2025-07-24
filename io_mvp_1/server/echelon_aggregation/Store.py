import pandas as pd
from server.operations import operations
from server.echelon_aggregation import common_aggregation

def store_data(df):
    echelon_df=common_aggregation.aggreagation_func(df,"Store")
    return echelon_df

