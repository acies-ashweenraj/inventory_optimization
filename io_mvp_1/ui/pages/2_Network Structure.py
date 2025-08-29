
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# ------------------- PATH CONFIG -------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / ".." / ".." / "server" / "data"

LEADTIME_FILE = DATA_DIR / "Leadtime_MultiSKU.xlsx"
COST_FILE = DATA_DIR / "Node_Costs.xlsx"

# ------------------- VISUAL CONSTANTS -------------------
ECHELON_COLORS = {
    "DC": "#6B5B95",          # Purple
    "Warehouse": "#88B04B",   # Green
    "Store": "#FF6F61"        # Pink
}

# ------------------- DATA LOADER -------------------
def load_network_data():
    try:
        network_links_df = pd.read_excel(LEADTIME_FILE)
        location_master_df = pd.read_excel(COST_FILE)
    except Exception as e:
        st.error(f"Error loading Excel files: {e}")
        return None, None

    # --- Standardize Columns ---
    network_links_df = network_links_df.rename(columns={
        "Source Code": "From_Location_ID",
        "Target Code": "To_Location_ID",
        "Lead Time": "Transport_Time_Days"
    })
    if "Transport_Cost" not in network_links_df.columns:
        network_links_df["Transport_Cost"] = np.random.randint(200, 800, size=len(network_links_df))

    location_master_df = location_master_df.rename(columns={"Node": "Location_ID"})

    if "Location_Name" not in location_master_df.columns:
        location_master_df["Location_Name"] = location_master_df["Location_ID"].astype(str).str.extract(r'_(.*)')[0]

    if "Echelon_Type" not in location_master_df.columns:
        location_master_df["Echelon_Type"] = location_master_df["Location_ID"].apply(
            lambda x: "Store" if "Store" in x else ("DC" if "DC" in x else "Warehouse")
        )

    if "Latitude" not in location_master_df.columns or "Longitude" not in location_master_df.columns:
        np.random.seed(42)
        location_master_df["Latitude"] = np.random.uniform(8, 28, size=len(location_master_df)).round(4)
        location_master_df["Longitude"] = np.random.uniform(70, 90, size=len(location_master_df)).round(4)

    if "Country" not in location_master_df.columns:
        location_master_df["Country"] = "India"

    return location_master_df, network_links_df

# ------------------- ECHELON ORDER & ICONS -------------------
def get_echelon_order():
    return ["Factory", "DC", "Warehouse", "Store"]

def get_echelon_icon(echelon_name):
    echelon_icon_map = {
        "Factory": "🏭",
        "DC": "🏬",
        "Warehouse": "🏚️",
        "Store": "🏪"
    }
    return echelon_icon_map.get(echelon_name, "📍")

# ------------------- FLOW LAYOUT -------------------
def build_flow_layout(location_master_df):
    echelon_tiers = get_echelon_order()
    node_layout = {}
    spacing_x = 450
    spacing_y = 200

    for tier_idx, tier_name in enumerate(echelon_tiers):
        tier_nodes = location_master_df[location_master_df['Echelon_Type'].str.lower() == tier_name.lower()]
        for node_idx, (_, node_row) in enumerate(tier_nodes.iterrows()):
            numeric_label = node_row['Location_ID'].split('_')[-1]
            node_layout[node_row['Location_ID']] = {
                'x': node_idx * spacing_x,
                'y': tier_idx * spacing_y,
                'label': f"{get_echelon_icon(node_row['Echelon_Type'])} {numeric_label}",
                'echelon': node_row['Echelon_Type'],
                'country': node_row.get('Country', '')
            }
    return node_layout

# ------------------- FLOWCHART -------------------
def build_flowchart_figure(node_layout, network_links_df):
    fig = go.Figure()

    # Add nodes
    for location_id, node_info in node_layout.items():
        fig.add_trace(go.Scatter(
            x=[node_info['x']], y=[-node_info['y']],
            mode="markers+text",
            marker=dict(size=18, color=ECHELON_COLORS.get(node_info['echelon'], "lightblue")),
            text=[node_info['label']],
            textposition="top center",
            hoverinfo="text",
            hovertext=(f"Location ID: {location_id}<br>"
                       f"Label: {node_info['label']}<br>"
                       f"Echelon: {node_info['echelon']}<br>"
                       f"Country: {node_info['country']}")
        ))

    # Add connections
    for _, row in network_links_df.iterrows():
        from_id = row['From_Location_ID']
        to_id = row['To_Location_ID']
        if from_id in node_layout and to_id in node_layout:
            from_x, from_y = node_layout[from_id]['x'], -node_layout[from_id]['y']
            to_x, to_y = node_layout[to_id]['x'], -node_layout[to_id]['y']

            fig.add_annotation(
                x=to_x, y=to_y,
                ax=from_x, ay=from_y,
                xref="x", yref="y",
                axref="x", ayref="y",
                showarrow=True,
                arrowhead=3,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="gray",
                opacity=0.8
            )

    # Legend
    legend_x = max([v['x'] for v in node_layout.values()] + [0]) + 200
    legend_y_start = 0
    spacing = 20
    for i, (echelon_name, color) in enumerate(ECHELON_COLORS.items()):
        fig.add_trace(go.Scatter(
            x=[legend_x], y=[legend_y_start - i * spacing],
            mode="markers+text",
            marker=dict(size=15, color=color),
            text=[echelon_name],
            textposition="middle right",
            hoverinfo="skip",
            showlegend=False
        ))

    fig.update_layout(
        showlegend=False,
        height=650,
        width=1200,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )

    return fig

# ------------------- MAIN DASHBOARD -------------------
def show_network_structure():
    st.title("Supply Chain Network Structure")

    location_master_df, network_links_df = load_network_data()
    if location_master_df is None or network_links_df is None:
        st.warning("Please check your Excel files in the data folder.")
        return

    st.markdown("<div class='filter-box'>", unsafe_allow_html=True)

    # Initialize session state filters
    for filter_col in ['Country', 'Echelon_Type', 'Location_ID']:
        key = f"selected_{filter_col.lower()}"
        if key not in st.session_state:
            st.session_state[key] = location_master_df[filter_col].unique().tolist()

    col_country, col_echelon, col_location = st.columns(3)

    # Country Filter
    with col_country:
        with st.expander("Country Filter", expanded=False):
            for country in sorted(location_master_df['Country'].unique()):
                if st.checkbox(country, value=country in st.session_state.selected_country, key=f"country_{country}"):
                    if country not in st.session_state.selected_country:
                        st.session_state.selected_country.append(country)
                else:
                    if country in st.session_state.selected_country:
                        st.session_state.selected_country.remove(country)

    # Echelon Filter
    with col_echelon:
        with st.expander("Echelon Type Filter", expanded=False):
            for echelon in sorted(location_master_df['Echelon_Type'].unique()):
                if st.checkbox(echelon, value=echelon in st.session_state.selected_echelon_type, key=f"echelon_{echelon}"):
                    if echelon not in st.session_state.selected_echelon_type:
                        st.session_state.selected_echelon_type.append(echelon)
                else:
                    if echelon in st.session_state.selected_echelon_type:
                        st.session_state.selected_echelon_type.remove(echelon)

    # Location Filter
    with col_location:
        with st.expander("Location ID Filter", expanded=False):
            for loc_id in sorted(location_master_df['Location_ID'].unique()):
                if st.checkbox(str(loc_id), value=loc_id in st.session_state.selected_location_id, key=f"loc_{loc_id}"):
                    if loc_id not in st.session_state.selected_location_id:
                        st.session_state.selected_location_id.append(loc_id)
                else:
                    if loc_id in st.session_state.selected_location_id:
                        st.session_state.selected_location_id.remove(loc_id)

    st.markdown("</div>", unsafe_allow_html=True)

    # Apply Filters
    filtered_locations_df = location_master_df[
        location_master_df['Country'].isin(st.session_state.selected_country) &
        location_master_df['Echelon_Type'].isin(st.session_state.selected_echelon_type) &
        location_master_df['Location_ID'].isin(st.session_state.selected_location_id)
    ]

    valid_location_ids = filtered_locations_df['Location_ID'].unique()
    filtered_links_df = network_links_df[
        (network_links_df['From_Location_ID'].isin(valid_location_ids)) &
        (network_links_df['To_Location_ID'].isin(valid_location_ids))
    ]

    # Flowchart View
    st.subheader("Flowchart View by Echelon Tier")
    node_layout = build_flow_layout(filtered_locations_df)
    flowchart_fig = build_flowchart_figure(node_layout, filtered_links_df)
    st.plotly_chart(flowchart_fig, use_container_width=True)

    # Geographical Map View
    st.subheader("Geographical Location Map")
    st.caption("Interactive globe — drag to rotate, zoom to explore.")
    map_projection_choice = st.radio("Select Map View Type", options=["3D Globe", "2D Map"], horizontal=True)
    projection_type = "orthographic" if "3D" in map_projection_choice else "equirectangular"

    map_fig = px.scatter_geo(
        filtered_locations_df,
        lat="Latitude",
        lon="Longitude",
        text="Location_Name",
        color="Echelon_Type",
        hover_name="Location_Name",
        hover_data={
            "Location_ID": True,
            "Echelon_Type": True,
            "Country": True,
            "Latitude": False,
            "Longitude": False
        },
        projection=projection_type,
        template="none"
    )

    map_fig.update_traces(
        marker=dict(size=10),
        textfont=dict(color='black', size=12),
        textposition='top center'
    )

    map_fig.update_layout(
        height=600,
        margin=dict(l=0, r=0, t=30, b=0),
        geo=dict(
            showland=True,
            landcolor="rgb(218, 194,160)",
            showocean=True,
            oceancolor="rgb(85,160,246)",
            showcoastlines=True,
            coastlinecolor="gray",
            showframe=False,
            bgcolor="rgba(0,0,0,0)"
        )
    )

    st.plotly_chart(map_fig, use_container_width=True)

# ------------------- RUN APP -------------------
if __name__ == "__main__":
    show_network_structure()
