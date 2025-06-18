from data_processing.Input_Data import load_file_as_dataframe
from config import input_path
from app_function_call import aggregate,calculate_metrics,distribute,schedule,download
from cost_comparison import eoq_cost,non_eoq_cost



df = load_file_as_dataframe(input_path, date_col="Time.[Week]")

store_df,warehouse_df,dc_df=aggregate(df)

store_demand_df,warehouse_demand_df,dc_demand_df=calculate_metrics(store_df,warehouse_df,dc_df)

warehouse_store_distribution,dc_warehouse_distribution=distribute(dc_demand_df,warehouse_demand_df,store_demand_df)

store_schedule_df,warehouse_schedule_df=schedule(store_demand_df,warehouse_demand_df)


eoq_cost_df = eoq_cost.eoq_cost_function(store_schedule_df,store_demand_df)
non_eoq_cost_df = non_eoq_cost.non_eoq_cost_function(warehouse_store_distribution)


download(store_df,warehouse_df,dc_df,store_demand_df,warehouse_demand_df,dc_demand_df,warehouse_store_distribution,dc_warehouse_distribution,store_schedule_df,warehouse_schedule_df,eoq_cost_df,non_eoq_cost_df)


