from server.data_processing.Input_Data import load_pickle_as_dataframe
from server.app_function_call import aggregate,calculate_metrics,distribute,schedule,download,cost
from server.cost_comparison import eoq_cost,non_eoq_cost

def run_meio_pipeline():

    df = load_pickle_as_dataframe("C:/Users/Saambavi/Desktop/inventory model/io_mvp_1/shared_data/demand_forecast.pkl")
    store_df,warehouse_df,dc_df=aggregate(df)

    store_demand_df,warehouse_demand_df,dc_demand_df=calculate_metrics(store_df,warehouse_df,dc_df)

    warehouse_store_distribution,dc_warehouse_distribution=distribute(dc_demand_df,warehouse_demand_df,store_demand_df)

    store_schedule_df,warehouse_schedule_df=schedule(store_demand_df,warehouse_demand_df)

    eoq_cost_df,non_eoq_cost_df,cost_merged_df = cost(store_schedule_df,store_demand_df,warehouse_store_distribution)


    download(store_df,warehouse_df,dc_df,store_demand_df,warehouse_demand_df,dc_demand_df,warehouse_store_distribution,dc_warehouse_distribution,store_schedule_df,warehouse_schedule_df,eoq_cost_df,non_eoq_cost_df,cost_merged_df)

