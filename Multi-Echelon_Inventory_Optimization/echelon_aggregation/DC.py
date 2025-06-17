import pandas as pd
from operations import operations
from Preassumptions import CODE_MAP,HOLDING_COST,LEAD_TIME,ORDERING_COST,Z_SCORE
from echelon_aggregation import common_aggregation


def dc_data(df):
    echelon_df=common_aggregation.aggreagation_func(df,"DC")
    return echelon_df
