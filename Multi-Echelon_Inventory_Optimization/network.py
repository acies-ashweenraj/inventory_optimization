import pandas as pd

# --- Load Data 

# --- Create Edge List (DC → WH → Store) ---
edges = []
for _, row in df[['DC', 'Warehouse', 'Store']].drop_duplicates().iterrows():
    dc = int(row['DC'])
    wh = int(row['Warehouse'])
    store = int(row['Store'])

    edges.append({'From': f'DC_{dc}', 'To': f'Warehouse_{wh}'})
    edges.append({'From': f'Warehouse_{wh}', 'To': f'Store_{store}'})

# --- Convert to DataFrame ---
edges_df = pd.DataFrame(edges).drop_duplicates()

# --- Export to Excel ---
edges_df.to_excel("supply_chain_edges.xlsx", index=False)