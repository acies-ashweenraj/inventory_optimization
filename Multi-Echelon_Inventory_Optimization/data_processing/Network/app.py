import streamlit as st
import pandas as pd
import json
import base64
import io

# Set page configuration
st.set_page_config(layout="wide", page_title="Supply Chain Visualizer")

# --- Sample Data ---
def get_sample_nodes_data():
    return pd.DataFrame({
        'Node ID': ['N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7'],
        'Name': ['Factory A', 'Distribution Center B', 'Store C', 'Warehouse D', 'Factory E', 'Store F', 'Distribution Center G'],
        'Type': ['Factory', 'Distribution Center', 'Store', 'Warehouse', 'Factory', 'Store', 'Distribution Center'],
        'Latitude': [34.0522, 39.0459, 30.2672, 33.7490, 40.7128, 36.1627, 39.7392],
        'Longitude': [-118.2437, -77.4587, -97.7431, -84.3880, -74.0060, -115.1398, -104.9903],
        'Echelon': ['Production', 'Regional Distribution', 'Retail', 'Storage', 'Production', 'Retail', 'Regional Distribution'],
        'Country': ['USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA'],
        'Region': ['West', 'East', 'South', 'South East', 'East', 'West', 'Mountain West']
    })

def get_sample_links_data():
    return pd.DataFrame({
        'Source': ['N1', 'N1', 'N2', 'N2', 'N4', 'N5', 'N5', 'N7'],
        'Target': ['N2', 'N4', 'N3', 'N7', 'N3', 'N2', 'N6', 'N3'],
        'Transport Cost': [100, 150, 50, 75, 60, 110, 80, 90],
        'SKU ID': ['SKU001', 'SKU002', 'SKU001', 'SKU003', 'SKU002', 'SKU001', 'SKU003', 'SKU003']
    })

def get_sample_inventory_data():
    return pd.DataFrame({
        'Date': ['2023-01-01', '2023-01-01', '2023-01-01', '2023-01-01', '2023-01-02', '2023-01-02', '2023-01-02', '2023-01-02'],
        'SKU ID': ['SKU001', 'SKU002', 'SKU003', 'SKU001', 'SKU001', 'SKU002', 'SKU003', 'SKU001'],
        'Location ID': ['N2', 'N4', 'N7', 'N3', 'N2', 'N4', 'N7', 'N3'],
        'Available Quantity': [500, 300, 700, 200, 480, 290, 680, 190],
        'In Transit Quantity': [50, 20, 30, 10, 60, 25, 35, 12],
        'Backorder Quantity': [5, 2, 7, 1, 6, 3, 8, 2]
    })

# --- Helper Functions for Data Processing ---
def process_nodes_data(df, column_mapping):
    mandatory_fields = {'Node ID': 'Node ID', 'Name': 'Name', 'Type': 'Type', 'Latitude': 'Latitude', 'Longitude': 'Longitude'}
    mapped_df = pd.DataFrame()
    errors = []
    skipped_rows = 0

    # Rename columns based on mapping
    for app_field, excel_col in column_mapping.items():
        if excel_col and excel_col in df.columns:
            mapped_df[app_field] = df[excel_col]
        elif app_field in mandatory_fields:
            errors.append(f"Mandatory field '{app_field}' is not mapped or column '{excel_col}' not found.")
            return None, errors, 0

    # Validate mandatory fields
    initial_rows = len(mapped_df)
    for field in mandatory_fields:
        if field not in mapped_df.columns:
            errors.append(f"Missing mandatory column: {field}")
            return None, errors, 0
        mapped_df = mapped_df.dropna(subset=[field])

    skipped_rows = initial_rows - len(mapped_df)

    # Convert Latitude and Longitude to numeric
    for col in ['Latitude', 'Longitude']:
        if col in mapped_df.columns:
            mapped_df[col] = pd.to_numeric(mapped_df[col], errors='coerce')
            mapped_df = mapped_df.dropna(subset=[col])
            if initial_rows - len(mapped_df) > skipped_rows:
                skipped_rows = initial_rows - len(mapped_df)
                errors.append(f"Skipped rows due to non-numeric values in '{col}'.")

    # Ensure Echelon, Country, Region exist, add empty if not
    for col in ['Echelon', 'Country', 'Region']:
        if col not in mapped_df.columns:
            mapped_df[col] = ''

    return mapped_df, errors, skipped_rows

def process_links_data(df, column_mapping):
    mandatory_fields = {'Source': 'Source', 'Target': 'Target', 'Transport Cost': 'Transport Cost'}
    mapped_df = pd.DataFrame()
    errors = []
    skipped_rows = 0

    for app_field, excel_col in column_mapping.items():
        if excel_col and excel_col in df.columns:
            mapped_df[app_field] = df[excel_col]
        elif app_field in mandatory_fields:
            errors.append(f"Mandatory field '{app_field}' is not mapped or column '{excel_col}' not found.")
            return None, errors, 0

    initial_rows = len(mapped_df)
    for field in mandatory_fields:
        if field not in mapped_df.columns:
            errors.append(f"Missing mandatory column: {field}")
            return None, errors, 0
        mapped_df = mapped_df.dropna(subset=[field])

    skipped_rows = initial_rows - len(mapped_df)

    if 'Transport Cost' in mapped_df.columns:
        mapped_df['Transport Cost'] = pd.to_numeric(mapped_df['Transport Cost'], errors='coerce')
        mapped_df = mapped_df.dropna(subset=['Transport Cost'])
        if initial_rows - len(mapped_df) > skipped_rows:
            skipped_rows = initial_rows - len(mapped_df)
            errors.append("Skipped rows due to non-numeric values in 'Transport Cost'.")

    if 'SKU ID' not in mapped_df.columns:
        mapped_df['SKU ID'] = ''

    return mapped_df, errors, skipped_rows

def process_inventory_data(df, column_mapping):
    mandatory_fields = {'Date': 'Date', 'SKU ID': 'SKU ID', 'Location ID': 'Location ID', 'Available Quantity': 'Available Quantity'}
    mapped_df = pd.DataFrame()
    errors = []
    skipped_rows = 0

    for app_field, excel_col in column_mapping.items():
        if excel_col and excel_col in df.columns:
            mapped_df[app_field] = df[excel_col]
        elif app_field in mandatory_fields:
            errors.append(f"Mandatory field '{app_field}' is not mapped or column '{excel_col}' not found.")
            return None, errors, 0

    initial_rows = len(mapped_df)
    for field in mandatory_fields:
        if field not in mapped_df.columns:
            errors.append(f"Missing mandatory column: {field}")
            return None, errors, 0
        mapped_df = mapped_df.dropna(subset=[field])

    skipped_rows = initial_rows - len(mapped_df)

    # Convert quantities to numeric
    for col in ['Available Quantity', 'In Transit Quantity', 'Backorder Quantity']:
        if col in mapped_df.columns:
            mapped_df[col] = pd.to_numeric(mapped_df[col], errors='coerce').fillna(0) # Fill NaN with 0 for quantities
        else:
            mapped_df[col] = 0 # Add column if not present and fill with 0

    # Convert Date to datetime
    if 'Date' in mapped_df.columns:
        mapped_df['Date'] = pd.to_datetime(mapped_df['Date'], errors='coerce')
        mapped_df = mapped_df.dropna(subset=['Date'])
        if initial_rows - len(mapped_df) > skipped_rows:
            skipped_rows = initial_rows - len(mapped_df)
            errors.append("Skipped rows due to invalid date format in 'Date'.")
        mapped_df['Date'] = mapped_df['Date'].dt.strftime('%Y-%m-%d') # Format back to string for consistency

    return mapped_df, errors, skipped_rows

# --- Streamlit UI ---
st.title("Supply Chain Network Visualizer")

# Initialize session state for data
if 'nodes_df' not in st.session_state:
    st.session_state.nodes_df = pd.DataFrame()
if 'links_df' not in st.session_state:
    st.session_state.links_df = pd.DataFrame()
if 'inventory_df' not in st.session_state:
    st.session_state.inventory_df = pd.DataFrame()

# --- Data Ingestion Section ---
st.header("1. Data Ingestion")

st.markdown("""
Upload your supply chain data for Nodes, Links, and Inventory using Excel files.
Use the "Load Sample Data" button for immediate use with predefined datasets.
Flexible column mapping allows you to select which Excel columns correspond to the application's required fields.
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Load Sample Data")
    if st.button("Load Sample Data"):
        st.session_state.nodes_df = get_sample_nodes_data()
        st.session_state.links_df = get_sample_links_data()
        st.session_state.inventory_df = get_sample_inventory_data()
        st.success("Sample data loaded successfully!")
        st.rerun()

with col2:
    st.subheader("Upload Your Data (Excel)")
    uploaded_nodes_file = st.file_uploader("Upload Nodes Data (Excel)", type=["xlsx"])
    uploaded_links_file = st.file_uploader("Upload Links Data (Excel)", type=["xlsx"])
    uploaded_inventory_file = st.file_uploader("Upload Inventory Data (Excel)", type=["xlsx"])

    if uploaded_nodes_file:
        df_nodes_raw = pd.read_excel(uploaded_nodes_file)
        st.write("Preview of uploaded Nodes data:")
        st.dataframe(df_nodes_raw.head())

        st.markdown("**Nodes Column Mapping:**")
        nodes_col_mapping = {}
        for app_field in ['Node ID', 'Name', 'Type', 'Latitude', 'Longitude', 'Echelon', 'Country', 'Region']:
            default_val = app_field if app_field in df_nodes_raw.columns else None
            nodes_col_mapping[app_field] = st.selectbox(
                f"Map '{app_field}' to Excel Column:",
                options=[None] + df_nodes_raw.columns.tolist(),
                key=f"nodes_{app_field}",
                index=df_nodes_raw.columns.tolist().index(default_val) + 1 if default_val else 0
            )
        if st.button("Process Nodes Data", key="process_nodes"):
            processed_df, errors, skipped = process_nodes_data(df_nodes_raw, nodes_col_mapping)
            if processed_df is not None and not processed_df.empty:
                st.session_state.nodes_df = processed_df
                st.success(f"Nodes data processed. {len(processed_df)} rows loaded.")
                if skipped > 0:
                    st.warning(f"{skipped} rows skipped due to missing/invalid mandatory fields.")
                for err in errors:
                    st.error(err)
                st.rerun()
            else:
                st.error("Failed to process Nodes data. Please check column mapping and data validity.")
                for err in errors:
                    st.error(err)
                if skipped > 0:
                    st.warning(f"{skipped} rows skipped due to missing/invalid mandatory fields.")

    if uploaded_links_file:
        df_links_raw = pd.read_excel(uploaded_links_file)
        st.write("Preview of uploaded Links data:")
        st.dataframe(df_links_raw.head())

        st.markdown("**Links Column Mapping:**")
        links_col_mapping = {}
        for app_field in ['Source', 'Target', 'Transport Cost', 'SKU ID']:
            default_val = app_field if app_field in df_links_raw.columns else None
            links_col_mapping[app_field] = st.selectbox(
                f"Map '{app_field}' to Excel Column:",
                options=[None] + df_links_raw.columns.tolist(),
                key=f"links_{app_field}",
                index=df_links_raw.columns.tolist().index(default_val) + 1 if default_val else 0
            )
        if st.button("Process Links Data", key="process_links"):
            processed_df, errors, skipped = process_links_data(df_links_raw, links_col_mapping)
            if processed_df is not None and not processed_df.empty:
                st.session_state.links_df = processed_df
                st.success(f"Links data processed. {len(processed_df)} rows loaded.")
                if skipped > 0:
                    st.warning(f"{skipped} rows skipped due to missing/invalid mandatory fields.")
                for err in errors:
                    st.error(err)
                st.rerun()
            else:
                st.error("Failed to process Links data. Please check column mapping and data validity.")
                for err in errors:
                    st.error(err)
                if skipped > 0:
                    st.warning(f"{skipped} rows skipped due to missing/invalid mandatory fields.")

    if uploaded_inventory_file:
        df_inventory_raw = pd.read_excel(uploaded_inventory_file)
        st.write("Preview of uploaded Inventory data:")
        st.dataframe(df_inventory_raw.head())

        st.markdown("**Inventory Column Mapping:**")
        inventory_col_mapping = {}
        for app_field in ['Date', 'SKU ID', 'Location ID', 'Available Quantity', 'In Transit Quantity', 'Backorder Quantity']:
            default_val = app_field if app_field in df_inventory_raw.columns else None
            inventory_col_mapping[app_field] = st.selectbox(
                f"Map '{app_field}' to Excel Column:",
                options=[None] + df_inventory_raw.columns.tolist(),
                key=f"inventory_{app_field}",
                index=df_inventory_raw.columns.tolist().index(default_val) + 1 if default_val else 0
            )
        if st.button("Process Inventory Data", key="process_inventory"):
            processed_df, errors, skipped = process_inventory_data(df_inventory_raw, inventory_col_mapping)
            if processed_df is not None and not processed_df.empty:
                st.session_state.inventory_df = processed_df
                st.success(f"Inventory data processed. {len(processed_df)} rows loaded.")
                if skipped > 0:
                    st.warning(f"{skipped} rows skipped due to missing/invalid mandatory fields.")
                for err in errors:
                    st.error(err)
                st.rerun()
            else:
                st.error("Failed to process Inventory data. Please check column mapping and data validity.")
                for err in errors:
                    st.error(err)
                if skipped > 0:
                    st.warning(f"{skipped} rows skipped due to missing/invalid mandatory fields.")

# Check if data is loaded before proceeding to visualizations
if st.session_state.nodes_df.empty or st.session_state.links_df.empty:
    st.warning("Please upload or load sample data for Nodes and Links to view visualizations.")
else:
    st.header("2. Core Visualizations & Filtering")

    # --- Filtering Options ---
    st.subheader("Filtering and Interactivity")
    col_filters_1, col_filters_2, col_filters_3 = st.columns(3)

    with col_filters_1:
        st.markdown("##### Node Filters")
        all_node_types = ['All'] + st.session_state.nodes_df['Type'].unique().tolist() if 'Type' in st.session_state.nodes_df.columns else ['All']
        selected_node_types = st.multiselect("Filter by Location Type:", all_node_types, default='All')
        if 'All' in selected_node_types:
            filtered_nodes_df = st.session_state.nodes_df
        else:
            filtered_nodes_df = st.session_state.nodes_df[st.session_state.nodes_df['Type'].isin(selected_node_types)]

        all_echelons = ['All'] + st.session_state.nodes_df['Echelon'].unique().tolist() if 'Echelon' in st.session_state.nodes_df.columns else ['All']
        selected_echelons = st.multiselect("Filter by Echelon:", all_echelons, default='All')
        if 'All' not in selected_echelons:
            filtered_nodes_df = filtered_nodes_df[filtered_nodes_df['Echelon'].isin(selected_echelons)]

    with col_filters_2:
        st.markdown("##### Geographical Filters")
        all_countries = ['All'] + st.session_state.nodes_df['Country'].unique().tolist() if 'Country' in st.session_state.nodes_df.columns else ['All']
        selected_countries = st.multiselect("Filter by Country:", all_countries, default='All')
        if 'All' not in selected_countries:
            filtered_nodes_df = filtered_nodes_df[filtered_nodes_df['Country'].isin(selected_countries)]

        all_regions = ['All'] + st.session_state.nodes_df['Region'].unique().tolist() if 'Region' in st.session_state.nodes_df.columns else ['All']
        selected_regions = st.multiselect("Filter by Region:", all_regions, default='All')
        if 'All' not in selected_regions:
            filtered_nodes_df = filtered_nodes_df[filtered_nodes_df['Region'].isin(selected_regions)]

    with col_filters_3:
        st.markdown("##### Data Filters")
        all_skus = ['All'] + st.session_state.links_df['SKU ID'].unique().tolist() if 'SKU ID' in st.session_state.links_df.columns else ['All']
        selected_sku = st.selectbox("Filter by SKU ID (Highlights Path):", all_skus)

        if not st.session_state.inventory_df.empty:
            all_dates = sorted(st.session_state.inventory_df['Date'].unique().tolist())
            selected_date = st.selectbox("Filter Inventory by Date:", ['Latest'] + all_dates)
            if selected_date == 'Latest' and all_dates:
                current_inventory_df = st.session_state.inventory_df[st.session_state.inventory_df['Date'] == all_dates[-1]]
            elif selected_date != 'Latest' and all_dates:
                current_inventory_df = st.session_state.inventory_df[st.session_state.inventory_df['Date'] == selected_date]
            else:
                current_inventory_df = pd.DataFrame() # Empty if no inventory data or dates
        else:
            current_inventory_df = pd.DataFrame()
            st.info("No inventory data available for date filtering.")


    # Apply node filters to links
    filtered_node_ids = filtered_nodes_df['Node ID'].tolist()
    filtered_links_df = st.session_state.links_df[
        (st.session_state.links_df['Source'].isin(filtered_node_ids)) &
        (st.session_state.links_df['Target'].isin(filtered_node_ids))
    ]

    # Apply SKU filter to links for highlighting
    if selected_sku != 'All':
        highlight_links_df = filtered_links_df[filtered_links_df['SKU ID'] == selected_sku]
        highlight_node_ids = set(highlight_links_df['Source'].tolist() + highlight_links_df['Target'].tolist())
        highlight_nodes_df = filtered_nodes_df[filtered_nodes_df['Node ID'].isin(highlight_node_ids)]
    else:
        highlight_links_df = pd.DataFrame() # No specific highlight
        highlight_nodes_df = pd.DataFrame() # No specific highlight

    # --- Prepare data for JavaScript ---
    graph_nodes = filtered_nodes_df.to_dict(orient='records')
    graph_links = filtered_links_df.to_dict(orient='records')

    # Add highlight status to nodes and links
    for node in graph_nodes:
        node['highlight'] = True if selected_sku == 'All' or node['Node ID'] in highlight_node_ids else False
    for link in graph_links:
        link['highlight'] = True if selected_sku == 'All' or link['SKU ID'] == selected_sku else False

    graph_data = {
        'nodes': graph_nodes,
        'links': graph_links,
        'selectedSku': selected_sku,
        'nodeTypes': st.session_state.nodes_df['Type'].unique().tolist() if 'Type' in st.session_state.nodes_df.columns else []
    }

    # Encode data as JSON for JavaScript
    graph_data_json = json.dumps(graph_data)

    # --- HTML/JS for Visualizations ---
    html_code = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Supply Chain Visualizations</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/cytoscape/dist/cytoscape.min.js"></script>
        <script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
        <script src="https://unpkg.com/cytoscape-dagre@2.3.0/cytoscape-dagre.js"></script>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <script src="https://d3js.org/topojson.v3.min.js"></script>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            body {{font-family: 'Inter', sans-serif; margin: 0; padding: 0; overflow-x: hidden;}}
            .container {{display: flex; flex-direction: column; gap: 1rem; padding: 1rem;}}
            .visualization-card {{
                background-color: #ffffff;
                border-radius: 0.75rem; /* rounded-xl */
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* shadow-lg */
                padding: 1rem;
                height: 500px; /* Fixed height for consistency */
                width: 100%;
                overflow: hidden;
            }}
            #cy, #map {{width: 100%; height: 100%;}}

            /* Cytoscape Styles */
            #cy {{
                background-color: #f9fafb; /* bg-gray-50 */
            }}
            .cy-node {{
                font-size: 10px;
                text-valign: center;
                text-halign: center;
                color: #374151; /* text-gray-700 */
                text-wrap: wrap;
                text-max-width: 80px;
                padding: 5px;
                border-width: 1px;
                border-color: #d1d5db; /* border-gray-300 */
                background-color: #f3f4f6; /* bg-gray-100 */
                shape: round-rectangle;
            }}
            .cy-node[type="Factory"] {{background-color: #ef4444; color: white;}} /* red-500 */
            .cy-node[type="Distribution Center"] {{background-color: #3b82f6; color: white;}} /* blue-500 */
            .cy-node[type="Store"] {{background-color: #22c55e; color: white;}} /* green-500 */
            .cy-node[type="Warehouse"] {{background-color: #f59e0b; color: white;}} /* amber-500 */

            .cy-edge {{
                width: 2;
                line-color: #9ca3af; /* gray-400 */
                target-arrow-shape: triangle;
                target-arrow-color: #9ca3af;
                curve-style: bezier;
                font-size: 8px;
                color: #4b5563; /* text-gray-600 */
                text-background-opacity: 1;
                text-background-color: #ffffff;
                text-background-padding: 3px;
                text-border-width: 1px;
                text-border-color: #e5e7eb;
                text-border-opacity: 1;
            }}
            .cy-edge.highlighted {{
                line-color: #10b981; /* emerald-500 */
                target-arrow-color: #10b981;
                width: 4;
                z-index: 999;
            }}
            .cy-node.highlighted {{
                border-color: #10b981; /* emerald-500 */
                border-width: 3px;
                z-index: 999;
                box-shadow: 0 0 10px rgba(16, 185, 129, 0.7);
            }}
            .cy-node.faded, .cy-edge.faded {{
                opacity: 0.2;
            }}

            /* Tooltip Styles */
            .tooltip {{
                position: absolute;
                background-color: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
                pointer-events: none;
                z-index: 1000;
                opacity: 0;
                transition: opacity 0.2s;
            }}
            .tooltip.active {{opacity: 1;}}

            /* D3 Map Styles */
            #map-container {{
                background-color: #f9fafb; /* bg-gray-50 */
                border-radius: 0.75rem;
                overflow: hidden;
                position: relative;
            }}
            .map-node {{
                fill: #3b82f6; /* blue-500 */
                stroke: #ffffff;
                stroke-width: 1.5px;
                cursor: pointer;
            }}
            .map-node[data-type="Factory"] {{fill: #ef4444;}} /* red-500 */
            .map-node[data-type="Distribution Center"] {{fill: #3b82f6;}} /* blue-500 */
            .map-node[data-type="Store"] {{fill: #22c55e;}} /* green-500 */
            .map-node[data-type="Warehouse"] {{fill: #f59e0b;}} /* amber-500 */

            .map-link {{
                stroke: #9ca3af; /* gray-400 */
                stroke-width: 2px;
                fill: none;
            }}
            .map-node.highlighted {{
                fill: #10b981; /* emerald-500 */
                stroke: #10b981;
                stroke-width: 4px;
                filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.7));
            }}
            .map-link.highlighted {{
                stroke: #10b981; /* emerald-500 */
                stroke-width: 4px;
            }}
            .map-node.faded, .map-link.faded {{
                opacity: 0.2;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h3 class="text-xl font-semibold text-gray-800 mb-4">Supply Chain Network Graph (Cytoscape.js)</h3>
            <div class="visualization-card">
                <div id="cy"></div>
            </div>

            <h3 class="text-xl font-semibold text-gray-800 mb-4 mt-8">Global Location Map (D3.js)</h3>
            <div class="visualization-card" id="map-container">
                <svg id="map"></svg>
                <div id="map-tooltip" class="tooltip"></div>
            </div>
        </div>

        <script>
            // Register Dagre layout for Cytoscape.js
            cytoscape.use(cytoscapeDagre);

            const graphData = {graph_data_json};
            const nodes = graphData.nodes;
            const links = graphData.links;
            const selectedSku = graphData.selectedSku;
            const nodeTypes = graphData.nodeTypes;

            // --- Cytoscape.js Network Graph ---
            const cy = cytoscape({{
                container: document.getElementById('cy'),
                elements: [], // Will be populated dynamically
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'content': 'data(Name)',
                            'font-size': '10px',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'color': '#374151',
                            'text-wrap': 'wrap',
                            'text-max-width': '80px',
                            'padding': '5px',
                            'border-width': '1px',
                            'border-color': '#d1d5db',
                            'background-color': '#f3f4f6',
                            'shape': 'round-rectangle',
                            'width': '60px',
                            'height': '30px',
                            'text-overflow-wrap': 'whitespace'
                        }}
                    }},
                    {{
                        selector: 'node[type="Factory"]',
                        style: {{ 'background-color': '#ef4444', 'color': 'white' }}
                    }},
                    {{
                        selector: 'node[type="Distribution Center"]',
                        style: {{ 'background-color': '#3b82f6', 'color': 'white' }}
                    }},
                    {{
                        selector: 'node[type="Store"]',
                        style: {{ 'background-color': '#22c55e', 'color': 'white' }}
                    }},
                    {{
                        selector: 'node[type="Warehouse"]',
                        style: {{ 'background-color': '#f59e0b', 'color': 'white' }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 2,
                            'line-color': '#9ca3af',
                            'target-arrow-shape': 'triangle',
                            'target-arrow-color': '#9ca3af',
                            'curve-style': 'bezier',
                            'label': 'data(Transport Cost)',
                            'font-size': '8px',
                            'color': '#4b5563',
                            'text-background-opacity': 1,
                            'text-background-color': '#ffffff',
                            'text-background-padding': 3,
                            'text-border-width': 1,
                            'text-border-color': '#e5e7eb',
                            'text-border-opacity': 1
                        }}
                    }},
                    {{
                        selector: '.highlighted',
                        style: {{
                            'line-color': '#10b981',
                            'target-arrow-color': '#10b981',
                            'width': 4,
                            'border-color': '#10b981',
                            'border-width': 3,
                            'z-index': 999,
                            'shadow-blur': 10,
                            'shadow-color': 'rgba(16, 185, 129, 0.7)'
                        }}
                    }},
                    {{
                        selector: '.faded',
                        style: {{ 'opacity': 0.2 }}
                    }}
                ],
                layout: {{
                    'name': 'dagre',
                    rankDir: 'TB', // Top-to-bottom
                    nodeDimensionsIncludeLabels: true,
                    padding: 30,
                    ranker: 'network-simplex', // or 'longest-path'
                    // Dagre does not directly support 'echelon' for ranking,
                    // but we can pre-sort nodes or assign ranks if needed.
                    // For now, it will try to infer hierarchy from graph structure.
                }}
            }});

            function updateCytoscapeGraph() {{
                cy.elements().remove(); // Clear existing elements

                const cyNodes = nodes.map(node => ({{
                    data: {{ id: node['Node ID'], Name: node['Name'], Type: node['Type'], ...node }},
                    classes: (selectedSku !== 'All' && !node.highlight) ? 'faded' : ''
                }}));

                const cyEdges = links.map(link => ({{
                    data: {{
                        id: `edge-${link['Source']}-${link['Target']}-${link['SKU ID'] or ''}`,
                        source: link['Source'],
                        target: link['Target'],
                        'Transport Cost': link['Transport Cost'],
                        'SKU ID': link['SKU ID'],
                        ...link
                    }},
                    classes: (selectedSku !== 'All' && !link.highlight) ? 'faded' : ''
                }}));

                cy.add(cyNodes);
                cy.add(cyEdges);

                // Apply highlight classes after adding elements
                if (selectedSku !== 'All') {{
                    cy.nodes().forEach(node => {{
                        if (node.data('highlight')) {{
                            node.addClass('highlighted');
                            node.removeClass('faded');
                        }} else {{
                            node.addClass('faded');
                            node.removeClass('highlighted');
                        }}
                    }});
                    cy.edges().forEach(edge => {{
                        if (edge.data('highlight')) {{
                            edge.addClass('highlighted');
                            edge.removeClass('faded');
                        }} else {{
                            edge.addClass('faded');
                            edge.removeClass('highlighted');
                        }}
                    }});
                }} else {{
                    cy.elements().removeClass('faded highlighted');
                }}

                cy.layout({{
                    name: 'dagre',
                    rankDir: 'TB',
                    nodeDimensionsIncludeLabels: true,
                    padding: 30,
                    ranker: 'network-simplex',
                }}).run();

                // Tooltips
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                document.body.appendChild(tooltip);

                
                cy.on('mouseover', 'node', function(event) {{
                    const node = event.target;
                    const data = node.data();
                    tooltip.innerHTML = `
                        <strong>Node ID:</strong> ${data['Node ID']}<br>
                        <strong>Name:</strong> ${data['Name']}<br>
                        <strong>Type:</strong> ${data['Type']}<br>
                        <strong>Echelon:</strong> ${data['Echelon']}<br>
                        <strong>Country:</strong> ${data['Country']}<br>
                        <strong>Region:</strong> ${data['Region']}<br>
                        <strong>Lat, Lon:</strong> ${data['Latitude']?.toFixed(2)}, ${data['Longitude']?.toFixed(2)}
                    `;
                    tooltip.classList.add('active');
                }});

                cy.on('mouseout', 'node', function() {{
                    tooltip.classList.remove('active');
                }});

                cy.on('mousemove', 'node', function(event) {{
                    tooltip.style.left = (event.renderedPosition.x + 15) + 'px';
                    tooltip.style.top = (event.renderedPosition.y + 15) + 'px';
                }});

                cy.on('mouseover', 'edge', function(event) {{
                    const edge = event.target;
                    const data = edge.data();
                    tooltip.innerHTML = `
                        <strong>Source:</strong> ${data['Source']}<br>
                        <strong>Target:</strong> ${data['Target']}<br>
                        <strong>Transport Cost:</strong> $${data['Transport Cost']}<br>
                        <strong>SKU ID:</strong> ${data['SKU ID'] or 'N/A'}
                    `;
                    tooltip.classList.add('active');
                }});

                cy.on('mouseout', 'edge', function() {{
                    tooltip.classList.remove('active');
                }});

                cy.on('mousemove', 'edge', function(event) {{
                    tooltip.style.left = (event.renderedPosition.x + 15) + 'px';
                    tooltip.style.top = (event.renderedPosition.y + 15) + 'px';
                }});

                // Responsive resize
                window.addEventListener('resize', () => {{
                    cy.resize();
                    cy.fit(); // Fit graph to container on resize
                }});
                cy.fit(); // Initial fit
            }}

            // --- D3.js Global Location Map ---
            const svg = d3.select("#map");
            const width = document.getElementById('map-container').clientWidth;
            const height = document.getElementById('map-container').clientHeight;

            svg.attr("width", width)
               .attr("height", height);

            const projection = d3.geoMercator()
                .scale(width / (2 * Math.PI))
                .translate([width / 2, height / 1.5]);

            const path = d3.geoPath().projection(projection);

            const mapTooltip = d3.select("#map-tooltip");

            function updateD3Map() {{
                svg.selectAll("*").remove(); // Clear existing map elements

                // Draw world map
                d3.json("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json").then(world => {{
                    svg.append("g")
                        .attr("class", "countries")
                        .selectAll("path")
                        .data(topojson.feature(world, world.objects.countries).features)
                        .enter().append("path")
                        .attr("fill", "#e0e7ff") /* indigo-100 */
                        .attr("stroke", "#9ca3af") /* gray-400 */
                        .attr("stroke-width", 0.5)
                        .attr("d", path);

                    // Draw links
                    svg.append("g")
                        .attr("class", "map-links")
                        .selectAll("line")
                        .data(links)
                        .enter().append("line")
                        .attr("x1", d => projection([d3.select(cy.getElementById(d.Source).data()).data.Longitude, d3.select(cy.getElementById(d.Source).data()).data.Latitude])[0])
                        .attr("y1", d => projection([d3.select(cy.getElementById(d.Source).data()).data.Longitude, d3.select(cy.getElementById(d.Source).data()).data.Latitude])[1])
                        .attr("x2", d => projection([d3.select(cy.getElementById(d.Target).data()).data.Longitude, d3.select(cy.getElementById(d.Target).data()).data.Latitude])[0])
                        .attr("y2", d => projection([d3.select(cy.getElementById(d.Target).data()).data.Longitude, d3.select(cy.getElementById(d.Target).data()).data.Latitude])[1])
                        .attr("class", d => d.highlight ? "map-link highlighted" : (selectedSku !== 'All' ? "map-link faded" : "map-link"))
                        .on("mouseover", function(event, d) {{
                            mapTooltip.html(`
                                <strong>Source:</strong> ${d.Source}<br>
                                <strong>Target:</strong> ${d.Target}<br>
                                <strong>Transport Cost:</strong> $${d['Transport Cost']}<br>
                                <strong>SKU ID:</strong> ${d['SKU ID'] or 'N/A'}
                            `)
                            .style("left", (event.pageX + 10) + "px")
                            .style("top", (event.pageY - 28) + "px")
                            .transition()
                            .duration(200)
                            .style("opacity", .9);
                        }})
                        .on("mouseout", function(d) {{
                            mapTooltip.transition()
                                .duration(500)
                                .style("opacity", 0);
                        }});

                    // Draw nodes
                    svg.append("g")
                        .attr("class", "map-nodes")
                        .selectAll("circle")
                        .data(nodes)
                        .enter().append("circle")
                        .attr("cx", d => projection([d.Longitude, d.Latitude])[0])
                        .attr("cy", d => projection([d.Latitude, d.Longitude])[1]) // Corrected for D3 map
                        .attr("r", 5)
                        .attr("data-type", d => d.Type) // For type-based styling
                        .attr("class", d => d.highlight ? "map-node highlighted" : (selectedSku !== 'All' ? "map-node faded" : "map-node"))
                        .on("mouseover", function(event, d) {{
                            mapTooltip.html(`
                                <strong>Node ID:</strong> ${d['Node ID']}<br>
                                <strong>Name:</strong> ${d['Name']}<br>
                                <strong>Type:</strong> ${d['Type']}<br>
                                <strong>Lat, Lon:</strong> ${d.Latitude.toFixed(2)}, ${d.Longitude.toFixed(2)}
                            `)
                            .style("left", (event.pageX + 10) + "px")
                            .style("top", (event.pageY - 28) + "px")
                            .transition()
                            .duration(200)
                            .style("opacity", .9);
                        }})
                        .on("mouseout", function(d) {{
                            mapTooltip.transition()
                                .duration(500)
                                .style("opacity", 0);
                        }});
                }});
            }}

            // Initial render and update on data change
            updateCytoscapeGraph();
            updateD3Map();

            // Responsive map resize
            window.addEventListener('resize', () => {{
                const newWidth = document.getElementById('map-container').clientWidth;
                const newHeight = document.getElementById('map-container').clientHeight;
                svg.attr("width", newWidth)
                   .attr("height", newHeight);
                projection.scale(newWidth / (2 * Math.PI))
                          .translate([newWidth / 2, newHeight / 1.5]);
                updateD3Map(); // Redraw map elements
            }});

        </script>
    </body>
    </html>
    """
    from streamlit.components.v1 import html
    html(html_code, height=1200, scrolling=True)

    # --- Inventory Snapshot Table ---
    st.header("3. Inventory Snapshot Table")
    st.markdown("A clear, tabular representation of your inventory data.")

    if not current_inventory_df.empty:
        st.dataframe(current_inventory_df.set_index('Location ID'))
    else:
        st.info("No inventory data available for the selected date or no inventory data uploaded.")

    st.markdown("---")
    st.markdown("""
    **User Experience & Design:**
    This application boasts a clean, modern design achieved using Tailwind CSS.
    Its fully responsive layout ensures optimal viewing and interaction across various device sizes (desktop, tablet, mobile).
    Both the Cytoscape.js and D3.js visualizations dynamically resize to adapt to screen changes.
    The user-friendly interface is characterized by clear section headers, intuitive controls, and informative feedback messages.
    """)
