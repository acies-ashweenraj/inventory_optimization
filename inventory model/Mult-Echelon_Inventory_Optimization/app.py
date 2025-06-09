import pandas as pd
from Input_Data import load_file_as_dataframe 
from Data_Aggregate import aggregate_store_monthly, aggregate_warehouse_monthly, aggregate_dc_monthly

df = load_file_as_dataframe("data/Sample_2.csv", date_col="Time.[Week]")

store_df = aggregate_store_monthly(df, date_col='Time.[Week]', value_col='Actual')
warehouse_df = aggregate_warehouse_monthly(df, date_col='Time.[Week]', value_col='Actual')
dc_df = aggregate_dc_monthly(df, date_col='Time.[Week]', value_col='Actual')


store_df.head()