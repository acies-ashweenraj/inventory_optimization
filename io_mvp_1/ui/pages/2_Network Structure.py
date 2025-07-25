
# (This replaces the previous `network_structure_full.py` with wider flowchart)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import pickle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR = os.path.join(BASE_DIR, "..", "..", "shared_data")
os.makedirs(SHARED_DIR, exist_ok=True)

def load_network_data():
    try:
        with open(os.path.join(SHARED_DIR, "lead_time.pkl"), "rb") as f:
            network_df = pickle.load(f)
        with open(os.path.join(SHARED_DIR, "node_data.pkl"), "rb") as f:
            location_df = pickle.load(f)
    except Exception as e:
        st.error(f"Error loading pickles: {e}")
        return None, None

    network_df = network_df.rename(columns={
        "Source Code": "From_Location_ID",
        "Target Code": "To_Location_ID",
        "Lead Time": "Transport_Time_Days"
    })
    if "Transport_Cost" not in network_df.columns:
        network_df["Transport_Cost"] = np.random.randint(200, 800, size=len(network_df))

    location_df = location_df.rename(columns={"Node": "Location_ID"})

    if "Location_Name" not in location_df.columns:
        location_df["Location_Name"] = location_df["Location_ID"].str.replace("_", " ")

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
    spacing_x = 450  # WIDER spacing between nodes
    spacing_y = 200  # More space between tiers
    for i, tier in enumerate(tiers):
        tier_nodes = location_df[location_df['Echelon_Type'].str.lower() == tier.lower()]
        for j, (_, row) in enumerate(tier_nodes.iterrows()):
            layout[row['Location_ID']] = {
                'x': j * spacing_x,
                'y': i * spacing_y,
                'label': f"{get_echelon_emoji(row['Echelon_Type'])} {row['Location_Name']}",
                'echelon': row['Echelon_Type'],
                'country': row.get('Country', '')
            }
    return layout

def create_flowchart_figure(layout, network_df):
    fig = go.Figure()

    for loc_id, info in layout.items():
        fig.add_trace(go.Scatter(
            x=[info['x']], y=[-info['y']],
            mode="markers+text",
            marker=dict(size=18, color="lightblue"),
            text=[info['label']],
            textposition="top center",
            hoverinfo="text",
            hovertext=(f"Location ID: {loc_id}<br>"
                       f"Name: {info['label']}<br>"
                       f"Echelon: {info['echelon']}<br>"
                       f"Country: {info['country']}")
        ))

    for _, row in network_df.iterrows():
        from_id = row['From_Location_ID']
        to_id = row['To_Location_ID']
        if from_id in layout and to_id in layout:
            fig.add_trace(go.Scatter(
                x=[layout[from_id]['x'], layout[to_id]['x']],
                y=[-layout[from_id]['y'], -layout[to_id]['y']],
                mode="lines",
                line=dict(color="gray", width=2),
                hoverinfo="none"
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
    st.title("Network Structure")

    location_df, network_df = load_network_data()
    if location_df is None or network_df is None:
        st.warning("Please upload Location and Network data in the Upload Data section.")
        return

    available_echelons = sorted(location_df['Echelon_Type'].dropna().unique())
    selected_echelons = st.multiselect(
        "Filter by Echelon Type:",
        available_echelons,
        default=available_echelons
    )

    filtered_location_df = location_df[location_df['Echelon_Type'].isin(selected_echelons)].copy()
    valid_location_ids = filtered_location_df['Location_ID'].unique()
    filtered_network_df = network_df[
        (network_df['From_Location_ID'].isin(valid_location_ids)) &
        (network_df['To_Location_ID'].isin(valid_location_ids))
    ]

    st.subheader(" Flowchart View by Echelon Tier")
    layout = create_flow_layout(filtered_location_df)
    fig_flow = create_flowchart_figure(layout, filtered_network_df)
    st.plotly_chart(fig_flow, use_container_width=True)

    st.subheader(" Geographical Location Map")
    fig_map = px.scatter_geo(
        filtered_location_df,
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
        projection="orthographic",
        template="plotly_dark"
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