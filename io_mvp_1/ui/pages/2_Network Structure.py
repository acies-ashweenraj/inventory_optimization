
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / ".." / ".." / "server" / "data"

lead_path = DATA_DIR / "Leadtime_MultiSKU.xlsx"
cost_path = DATA_DIR / "Node_Costs.xlsx"

ECHELON_COLORS = {
    "DC": "#6B5B95",          # Purple
    "Warehouse": "#88B04B",   # Green
    "Store": "#FF6F61"        # Pink
}


def load_network_data():
    try:
        network_df = pd.read_excel(lead_path)
        location_df = pd.read_excel(cost_path)
    except Exception as e:
        st.error(f"Error loading Excel files: {e}")
        return None, None

    # --- Standardize Columns ---
    network_df = network_df.rename(columns={
        "Source Code": "From_Location_ID",
        "Target Code": "To_Location_ID",
        "Lead Time": "Transport_Time_Days"
    })
    if "Transport_Cost" not in network_df.columns:
        network_df["Transport_Cost"] = np.random.randint(200, 800, size=len(network_df))

    location_df = location_df.rename(columns={"Node": "Location_ID"})

    if "Location_Name" not in location_df.columns:
        location_df["Location_Name"] = location_df["Location_ID"].astype(str).str.extract(r'_(.*)')[0]

    if "Echelon_Type" not in location_df.columns:
        location_df["Echelon_Type"] = location_df["Location_ID"].apply(
            lambda x: "Store" if "Store" in x else ("DC" if "DC" in x else "Warehouse")
        )

    if "Latitude" not in location_df.columns or "Longitude" not in location_df.columns:
        np.random.seed(42)
        location_df["Latitude"] = np.random.uniform(8, 28, size=len(location_df)).round(4)
        location_df["Longitude"] = np.random.uniform(70, 90, size=len(location_df)).round(4)

    if "Country" not in location_df.columns:
        location_df["Country"] = "India"

    return location_df, network_df


def get_echelon_order():
    return ["Factory", "DC", "Warehouse", "Store"]

def get_echelon_emoji(echelon):
    emoji_map = {
        "Factory": "🏭",
        "DC": "🏬",
        "Warehouse": "🏚️",
        "Store": "🏪"
    }
    return emoji_map.get(echelon, "📍")


def create_flow_layout(location_df):
    tiers = get_echelon_order()
    layout = {}
    spacing_x = 450
    spacing_y = 200
    for i, tier in enumerate(tiers):
        tier_nodes = location_df[location_df['Echelon_Type'].str.lower() == tier.lower()]
        for j, (_, row) in enumerate(tier_nodes.iterrows()):
            numeric_label = row['Location_ID'].split('_')[-1]
            layout[row['Location_ID']] = {
                'x': j * spacing_x,
                'y': i * spacing_y,
                'label': f"{get_echelon_emoji(row['Echelon_Type'])} {numeric_label}",
                'echelon': row['Echelon_Type'],
                'country': row.get('Country', '')
            }
    return layout


def create_flowchart_figure(layout, network_df):
    fig = go.Figure()

    # Add nodes
    for loc_id, info in layout.items():
        fig.add_trace(go.Scatter(
            x=[info['x']], y=[-info['y']],
            mode="markers+text",
            marker=dict(size=18, color=ECHELON_COLORS.get(info['echelon'], "lightblue")),
            text=[info['label']],
            textposition="top center",
            hoverinfo="text",
            hovertext=(f"Location ID: {loc_id}<br>"
                       f"Label: {info['label']}<br>"
                       f"Echelon: {info['echelon']}<br>"
                       f"Country: {info['country']}")
        ))

    # Add arrows for connections
    for _, row in network_df.iterrows():
        from_id = row['From_Location_ID']
        to_id = row['To_Location_ID']
        if from_id in layout and to_id in layout:
            from_x, from_y = layout[from_id]['x'], -layout[from_id]['y']
            to_x, to_y = layout[to_id]['x'], -layout[to_id]['y']

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

    # === Legend ===
    legend_x = max([v['x'] for v in layout.values()] + [0]) + 200
    legend_y_start = 0
    spacing = 20

    for i, (echelon, color) in enumerate(ECHELON_COLORS.items()):
        fig.add_trace(go.Scatter(
            x=[legend_x], y=[legend_y_start - i * spacing],
            mode="markers+text",
            marker=dict(size=15, color=color),
            text=[echelon],
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


def show_network_structure():
    st.title("Supply Chain Network Structure")

    location_df, network_df = load_network_data()
    if location_df is None or network_df is None:
        st.warning("Please check your Excel files in the data folder.")
        return

    # --- Filters with Select All ---
    st.subheader("Filters")

    col1, col2, col3 = st.columns(3)

    # Country Filter
    with col1:
        options = sorted(location_df['Country'].unique())
        selected = st.multiselect("Country", ["Select All"] + options, default=["Select All"])
        if "Select All" in selected:
            selected_countries = options
        else:
            selected_countries = selected

    # Echelon Filter
    with col2:
        options = sorted(location_df['Echelon_Type'].unique())
        selected = st.multiselect("Echelon Type", ["Select All"] + options, default=["Select All"])
        if "Select All" in selected:
            selected_echelons = options
        else:
            selected_echelons = selected

    # Location Filter
    with col3:
        options = sorted(location_df['Location_ID'].unique())
        selected = st.multiselect("Location ID", ["Select All"] + options, default=["Select All"])
        if "Select All" in selected:
            selected_locations = options
        else:
            selected_locations = selected

    # Filter Data
    filtered_df = location_df[
        location_df['Country'].isin(selected_countries) &
        location_df['Echelon_Type'].isin(selected_echelons) &
        location_df['Location_ID'].isin(selected_locations)
    ]

    valid_ids = filtered_df['Location_ID'].unique()
    filtered_network_df = network_df[
        (network_df['From_Location_ID'].isin(valid_ids)) &
        (network_df['To_Location_ID'].isin(valid_ids))
    ]

    # Flowchart
    st.subheader("Flowchart View by Echelon Tier")
    layout = create_flow_layout(filtered_df)
    fig_flow = create_flowchart_figure(layout, filtered_network_df)
    st.plotly_chart(fig_flow, use_container_width=True)

    # Map View
    st.subheader("Geographical Location Map")
    st.caption("Interactive globe — drag to rotate, zoom to explore.")
    map_projection = st.radio("Select Map View Type", options=["3D Globe", "2D Map"], horizontal=True)
    projection_type = "orthographic" if "3D" in map_projection else "equirectangular"

    fig_map = px.scatter_geo(
        filtered_df,
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

    fig_map.update_traces(
        marker=dict(size=10),
        textfont=dict(color='black', size=12),
        textposition='top center'
    )

    fig_map.update_layout(
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

    st.plotly_chart(fig_map, use_container_width=True)


if __name__ == "__main__":
    show_network_structure()
