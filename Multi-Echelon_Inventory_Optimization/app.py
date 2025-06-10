import pandas as pd
from data_processing.Input_Data import load_file_as_dataframe
from data_processing.Data_Aggregate import aggregate_store_monthly, aggregate_warehouse_monthly, aggregate_dc_monthly
from echelon_aggregation.Store import store_data
from echelon_aggregation.Warehouse import warehouse_data
from echelon_aggregation.DC import dc_data
from distribution.dc_distribution import dc_distribution
from distribution.warehouse_distribution import warehouse_distribution

csv_path = r"C:\Users\DELL\Desktop\project-1 R&S\inventory_optimization\Multi-Echelon_Inventory_Optimization\data\Sample_2.csv"


df = load_file_as_dataframe(csv_path, date_col="Time.[Week]")

store_df = aggregate_store_monthly(df, date_col='TimeWeek', value_col='Actual')
warehouse_df = aggregate_warehouse_monthly(df, date_col='TimeWeek', value_col='Actual')
dc_df = aggregate_dc_monthly(df, date_col='TimeWeek', value_col='Actual')

print(store_df.head())
store_df.to_excel("store_monthly_demand.xlsx", index=False, engine='openpyxl')
store_demand_df=store_data(store_df)
store_demand_df.to_excel("store_demand_df.xlsx",index=False,engine='openpyxl')

warehouse_df.to_excel("warehouse_monthly_demand.xlsx", index=False, engine='openpyxl')
warehouse_demand_df=warehouse_data(warehouse_df)
warehouse_demand_df.to_excel("warehouse_demand_df.xlsx",index=False,engine='openpyxl')

dc_df.to_excel("dc_monthly_demand.xlsx", index=False, engine='openpyxl')
dc_demand_df=dc_data(dc_df)
dc_demand_df.to_excel("dc_demand_df.xlsx",index=False,engine='openpyxl')

print(dc_demand_df.head())
print(warehouse_demand_df.head())

dc_warehouse_distribution=dc_distribution(dc_demand_df,warehouse_demand_df)
# dc_warehouse_distribution.to_excel("dc_warehouse_distribution_df.xlsx",index=False,engine='openpyxl')

# warehouse_store_distribution=warehouse_distribution(warehouse_demand_df,store_demand_df)
# warehouse_store_distribution.to_excel("warehouse_store_distribution_df.xlsx",index=False,engine='openpyxl')