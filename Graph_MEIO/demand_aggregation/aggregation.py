import pandas as pd
from config import aggregated_data_path


def aggregate_hierarchy_demand(network_df,forecasted_df):

    # --- Normalize input ---
    forecasted_df['store'] = forecasted_df['store'].str.strip().str.upper()
    forecasted_df['sku'] = forecasted_df['sku'].str.strip().str.upper()
    forecasted_df['week'] = pd.to_datetime(forecasted_df['week'])

    network_df['node_code'] = network_df['node_code'].astype(str).str.strip()
    network_df['node_name'] = network_df['node_name'].str.strip().str.upper()
    network_df['parent_code'] = network_df['parent_code'].astype(str).str.strip()

    # --- Build mapping dicts ---
    code_to_name = dict(zip(network_df['node_code'], network_df['node_name']))
    name_to_code = {v: k for k, v in code_to_name.items()}
    child_to_parent = dict(zip(network_df['node_code'], network_df['parent_code']))

    # --- Initialize demand with store-level data ---
    base_df = forecasted_df.rename(columns={'store': 'node'})[['node', 'sku', 'week', 'actual', 'forecast']].copy()
    base_df['node'] = base_df['node'].str.upper()

    all_demand = base_df.copy()

    # --- Propagate demand upward ---
    current_level = base_df.copy()
    max_levels = 10  # safety cap to avoid infinite loops

    for _ in range(max_levels):
        # Map node name to node code, then to parent code
        current_level['node_code'] = current_level['node'].map(name_to_code)
        current_level['parent_code'] = current_level['node_code'].map(child_to_parent)
        current_level['parent_name'] = current_level['parent_code'].map(code_to_name)

        # If all parent_name values are NaN, we're at the top
        if current_level['parent_name'].isna().all():
            break

        # Aggregate to parent level
        parent_demand = current_level.dropna(subset=['parent_name']).copy()
        grouped = parent_demand.groupby(['parent_name', 'sku', 'week'], as_index=False)[['actual', 'forecast']].sum()
        grouped = grouped.rename(columns={'parent_name': 'node'})

        # Append to all demand
        all_demand = pd.concat([all_demand, grouped], ignore_index=True)

        # Prepare for next level
        current_level = grouped.copy()

    # Final cleanup
    all_demand['node'] = all_demand['node'].str.strip().str.upper()
    all_demand = all_demand.groupby(['node', 'sku', 'week'], as_index=False)[['actual', 'forecast']].sum()

    all_demand.to_excel(f"{aggregated_data_path}/Aggregated_Data.xlsx", index=False, engine='openpyxl')
