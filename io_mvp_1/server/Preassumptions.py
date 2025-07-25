
import pandas as pd
# from server.data_processing.Input_Data import load_pickle_as_dataframe
from server.data_processing.Input_Data import load_file_as_dataframe

from .config import cost_path,lead_path


cost_df =  load_file_as_dataframe(cost_path)

lead_time_df  = load_file_as_dataframe(lead_path)

     # Source Code, Target Code, Lead Time


ORDERING_COST = {}
for _, row in cost_df.iterrows():
    node = row['Node']
    node_type, node_code = node.split('_')
    if node_type == 'DC':
        key = f'DC_{node_code}'
    elif node_type == 'Warehouse':
        key = f'Warehouse_{node_code}'
    elif node_type == 'Store':
        key = f'Store_{node_code}'
    ORDERING_COST[key] = row['Ordering_Cost']

HOLDING_COST = {}
for _, row in cost_df.iterrows():
    node = row['Node']
    node_type, node_code = node.split('_')
    if node_type == 'DC':
        key = f'DC_{node_code}'
    elif node_type == 'Warehouse':
        key = f'Warehouse_{node_code}'
    elif node_type == 'Store':
        key = f'Store_{node_code}'
    HOLDING_COST[key] = row['Holding_Cost']

LEAD_TIME1 = {}
for _, row in lead_time_df.iterrows():
    from_code = row['Source_Code'].split('_')
    to_code = row['Target_Code'].split('_')

    from_key = f"{from_code[0]}_{from_code[1]}"
    to_key = f"{to_code[0]}_{to_code[1]}"
    LEAD_TIME1[(from_key, to_key)] = row['Lead_Time']



Z_SCORE = 1.65

STORE_SCHEDULE=[]

WAREHOUSE_SCHEDULE=[]


