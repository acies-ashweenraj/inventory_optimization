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
from config import input_path,monthly_demand_path,calculated_metrics_path,distribution_path,schedule_path,cost_path



def aggregate(df):
    store_df = aggregate_store_monthly(df, date_col='TimeWeek', value_col='Actual')
    warehouse_df = aggregate_warehouse_monthly(df, date_col='TimeWeek', value_col='Actual')
    dc_df = aggregate_dc_monthly(df, date_col='TimeWeek', value_col='Actual')

    return store_df,warehouse_df,dc_df

def calculate_metrics(store_df,warehouse_df,dc_df):
    store_demand_df=store_data(store_df)
    warehouse_demand_df=warehouse_data(warehouse_df)
    dc_demand_df=dc_data(dc_df)

    return store_demand_df,warehouse_demand_df,dc_demand_df

def distribute(dc_demand_df,warehouse_demand_df,store_demand_df):
    dc_warehouse_distribution=dc_distribution(dc_demand_df,warehouse_demand_df)
    warehouse_store_distribution=warehouse_distribution(dc_warehouse_distribution,store_demand_df)

    return warehouse_store_distribution,dc_warehouse_distribution

def schedule(store_demand_df,warehouse_demand_df):
    store_schedule.stores_schedule(store_demand_df)
    store_schedule_df=pd.DataFrame(STORE_SCHEDULE)

    warehouse_schedule.warehouses_schedule(warehouse_demand_df)
    warehouse_schedule_df=pd.DataFrame(WAREHOUSE_SCHEDULE)

    return store_schedule_df,warehouse_schedule_df

def download(store_df,warehouse_df,dc_df,store_demand_df,warehouse_demand_df,dc_demand_df,warehouse_store_distribution,dc_warehouse_distribution,store_schedule_df,warehouse_schedule_df,eoq_cost_df,non_eoq_cost_df):
    store_df.to_excel(f"{monthly_demand_path}/store_aggregated_monthly_demand.xlsx", index=False, engine='openpyxl')
    store_demand_df.to_excel(f"{calculated_metrics_path}/store_monthly_metrics.xlsx",index=False,engine='openpyxl')

    warehouse_df.to_excel(f"{monthly_demand_path}/warehouse_aggregated_monthly_demand.xlsx", index=False, engine='openpyxl')
    warehouse_demand_df.to_excel(f"{calculated_metrics_path}/warehouse_monthly_metrics.xlsx",index=False,engine='openpyxl')

    dc_df.to_excel(f"{monthly_demand_path}/dc_aggregated_monthly_demand.xlsx", index=False, engine='openpyxl')
    dc_demand_df.to_excel(f"{calculated_metrics_path}/dc_monthly_metrics.xlsx",index=False,engine='openpyxl')

    dc_warehouse_distribution.to_excel(f"{distribution_path}/dc_warehouse_distribution_df.xlsx",index=False,engine='openpyxl')
    warehouse_store_distribution.to_excel(f"{distribution_path}/warehouse_store_distribution_df.xlsx",index=False,engine='openpyxl')

    store_schedule_df.to_excel(f"{schedule_path}/stores_order_schedule.xlsx",index=False,engine="openpyxl")
    warehouse_schedule_df.to_excel(f"{schedule_path}/warehouses_order_schedule.xlsx",index=False,engine="openpyxl")

    eoq_cost_df.to_excel(f"{cost_path}/eoq_cost.xlsx",index=False,engine="openpyxl")
    non_eoq_cost_df.to_excel(f"{cost_path}/non_eoq_cost.xlsx",index=False,engine="openpyxl")






