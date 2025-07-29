from server.data_processing.Input_Data import load_file_as_dataframe
from server.app_function_call import aggregate,calculate_metrics,distribute,schedule,download,cost
from server.cost_comparison import eoq_cost,non_eoq_cost
from .config import demand_path
def clean_demand_forecast_df(df):
    issues = {}

    
    null_counts = df.isnull().sum()
    null_columns = null_counts[null_counts > 0]
    if not null_columns.empty:
        issues['null_values'] = null_columns.to_dict()
        for col in null_columns.index:
            if col.lower() in ['forecast', 'demand', 'sales', 'inventory', 'order_quantity']:
                df[col].fillna(0, inplace=True)
            elif pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(0, inplace=True)
            else:
                df[col].fillna("Unknown", inplace=True)

    
    negative_counts = {}
    for col in df.select_dtypes(include='number').columns:
        mask = df[col] < 0
        negative_count = mask.sum()
        if negative_count > 0:
            negative_counts[col] = int(negative_count)
            if col.lower() in ['forecast', 'demand', 'sales', 'inventory', 'order_quantity']:
                df.loc[mask, col] = 0  
    if negative_counts:
        issues['negative_values'] = negative_counts

    
    all_null_cols = df.columns[df.isnull().all()]
    if not all_null_cols.empty:
        issues['fully_null_columns'] = list(all_null_cols)
        df.drop(columns=all_null_cols, inplace=True)

    
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        issues['duplicate_rows'] = int(duplicate_count)
        df.drop_duplicates(inplace=True)

    
    if issues:
        print("✅ Demand Forecast Data Cleaned. Issues handled:")
        for issue, detail in issues.items():
            print(f"- {issue}: {detail}")
    else:
        print("✅ Demand Forecast Data is clean. No issues found.")

    return df

def run_meio_pipeline():

    df = load_file_as_dataframe(demand_path)
    df =  clean_demand_forecast_df(df)
    print(df.columns)
    store_df,warehouse_df,dc_df=aggregate(df)
    

    store_demand_df,warehouse_demand_df,dc_demand_df=calculate_metrics(store_df,warehouse_df,dc_df)

    warehouse_store_distribution,dc_warehouse_distribution=distribute(dc_demand_df,warehouse_demand_df,store_demand_df)

    store_schedule_df,warehouse_schedule_df=schedule(store_demand_df,warehouse_demand_df)

    eoq_cost_df,non_eoq_cost_df,cost_merged_df = cost(store_schedule_df,store_demand_df,warehouse_store_distribution)


    download(store_df,warehouse_df,dc_df,store_demand_df,warehouse_demand_df,dc_demand_df,warehouse_store_distribution,dc_warehouse_distribution,store_schedule_df,warehouse_schedule_df,eoq_cost_df,non_eoq_cost_df,cost_merged_df)

