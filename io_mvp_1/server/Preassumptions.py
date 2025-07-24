
import pandas as pd

cost_df = pd.read_excel(r"io_mvp_1\server\data\Node_Costs.xlsx")
lead_time_df = pd.read_excel(r"io_mvp_1\server\data\Leadtime_MultiSKU.xlsx")     # Source Code, Target Code, Lead Time


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
    ORDERING_COST[key] = row['Ordering Cost']

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
    HOLDING_COST[key] = row['Holding Cost']

LEAD_TIME1 = {}
for _, row in lead_time_df.iterrows():
    from_code = row['Source Code'].split('_')
    to_code = row['Target Code'].split('_')

    from_key = f"{from_code[0]}_{from_code[1]}"
    to_key = f"{to_code[0]}_{to_code[1]}"
    LEAD_TIME1[(from_key, to_key)] = row['Lead Time']



Z_SCORE = 1.65

STORE_SCHEDULE=[]

WAREHOUSE_SCHEDULE=[]


