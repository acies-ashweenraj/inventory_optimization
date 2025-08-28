from server.data_processing.Input_Data import load_file_as_dataframe
from server.app_function_call import aggregate,calculate_metrics,distribute,schedule,download,cost
from .config import demand_path


def run_meio_pipeline():

    df = load_file_as_dataframe(demand_path)

    store_df,warehouse_df,dc_df=aggregate(df)
    
    store_demand_df,warehouse_demand_df,dc_demand_df=calculate_metrics(store_df,warehouse_df,dc_df)

    warehouse_store_distribution,dc_warehouse_distribution=distribute(dc_demand_df,warehouse_demand_df,store_demand_df)

    store_schedule_df,warehouse_schedule_df=schedule(warehouse_store_distribution,dc_warehouse_distribution)

    cost()

    download(store_df,warehouse_df,dc_df,store_demand_df,warehouse_demand_df,dc_demand_df,warehouse_store_distribution,dc_warehouse_distribution,store_schedule_df,warehouse_schedule_df)