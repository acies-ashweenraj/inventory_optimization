import pandas as pd
from data_processing.Input_Data import load_file_as_dataframe
from data_processing.Data_Aggregate import aggregate_store_monthly, aggregate_warehouse_monthly, aggregate_dc_monthly
from echelon_aggregation.Store import store_data
from echelon_aggregation.Warehouse import warehouse_data
from echelon_aggregation.DC import dc_data
from distribution.dc_distribution import dc_distribution
from distribution.warehouse_distribution import warehouse_distribution
from schedules import store_schedule
from schedules import warehouse_schedule
from Preassumptions import STORE_SCHEDULE,WAREHOUSE_SCHEDULE

csv_path = r"C:\Users\Mythreye\Desktop\multi-echelon\inventory_optimization\Multi-Echelon_Inventory_Optimization\data\Sample_2.csv"


df = load_file_as_dataframe(csv_path, date_col="Time.[Week]")


#
store_df = aggregate_store_monthly(df, date_col='TimeWeek', value_col='Actual')
store_df.to_excel("./Multi-Echelon_Inventory_Optimization/output_data/monthly_demand/store_aggregated_monthly_demand.xlsx", index=False, engine='openpyxl')

store_demand_df=store_data(store_df)
store_demand_df.to_excel("./Multi-Echelon_Inventory_Optimization/output_data/calculated_metrics/store_monthly_metrics.xlsx",index=False,engine='openpyxl')

warehouse_df = aggregate_warehouse_monthly(df, date_col='TimeWeek', value_col='Actual')
warehouse_df.to_excel("./Multi-Echelon_Inventory_Optimization/output_data/monthly_demand/warehouse_aggregated_monthly_demand.xlsx", index=False, engine='openpyxl')

warehouse_demand_df=warehouse_data(warehouse_df)
warehouse_demand_df.to_excel("./Multi-Echelon_Inventory_Optimization/output_data/calculated_metrics/warehouse_monthly_metrics.xlsx",index=False,engine='openpyxl')

dc_df = aggregate_dc_monthly(df, date_col='TimeWeek', value_col='Actual')
dc_df.to_excel("./Multi-Echelon_Inventory_Optimization/output_data/monthly_demand/dc_aggregated_monthly_demand.xlsx", index=False, engine='openpyxl')

dc_demand_df=dc_data(dc_df)
dc_demand_df.to_excel("./Multi-Echelon_Inventory_Optimization/output_data/calculated_metrics/dc_monthly_metrics.xlsx",index=False,engine='openpyxl')



dc_warehouse_distribution=dc_distribution(dc_demand_df,warehouse_demand_df)
dc_warehouse_distribution.to_excel("./Multi-Echelon_Inventory_Optimization/output_data/distribution/dc_warehouse_distribution_df.xlsx",index=False,engine='openpyxl')

warehouse_store_distribution=warehouse_distribution(dc_warehouse_distribution,store_demand_df)
warehouse_store_distribution.to_excel("./Multi-Echelon_Inventory_Optimization/output_data/distribution/warehouse_store_distribution_df.xlsx",index=False,engine='openpyxl')
#


store_schedule.stores_schedule(store_demand_df)
store_schedule_df=pd.DataFrame(STORE_SCHEDULE)
store_schedule_df.to_excel("./Multi-Echelon_Inventory_Optimization/output_data/schedule_data/stores_order_schedule.xlsx",index=False,engine="openpyxl")

warehouse_schedule.warehouses_schedule(warehouse_demand_df)
warehouse_schedule_df=pd.DataFrame(WAREHOUSE_SCHEDULE)
warehouse_schedule_df.to_excel("./Multi-Echelon_Inventory_Optimization/output_data/schedule_data/warehouses_order_schedule.xlsx",index=False,engine="openpyxl")


