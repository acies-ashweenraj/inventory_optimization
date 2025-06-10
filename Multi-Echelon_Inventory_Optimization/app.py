import pandas as pd
from data_processing.Input_Data import load_file_as_dataframe
from data_processing.Data_Aggregate import aggregate_store_monthly
# from Store import store_data
from echelon_aggregation.Store import store_data

csv_path = r"C:\Users\RISHIKESH\Desktop\inventory_eda\inventory_optimization\Multi-Echelon_Inventory_Optimization\data\Sample_2.csv"


df = load_file_as_dataframe(csv_path, date_col="Time.[Week]")

store_df = aggregate_store_monthly(df, date_col='TimeWeek', value_col='Actual')
print(store_df.head())
store_df.to_excel("store_monthly_demand.xlsx", index=False, engine='openpyxl')
store_demand_df=store_data(store_df)
store_demand_df.to_excel("store_demand_df.xlsx",index=False,engine='openpyxl')
