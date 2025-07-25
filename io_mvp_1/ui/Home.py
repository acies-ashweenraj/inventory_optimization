import streamlit as st

st.set_page_config(layout="wide", page_title="Inventory Assistant")

# Title and logo side-by-side
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("##  Inventory Analytics & Assistant")
with col2:
    st.image("acies_global_logo.jpeg", width=80)  # Make sure this file is in the same folder

st.markdown("---")

# App Description
st.markdown("""


Welcome to the Inventory Optimization 
This helps you:

-- Upload and Analyze: Import your current inventory data, network structure, and MEIO inputs for detailed analysis.

-- Identify Imbalances: Automatically detect overstocked and understocked SKUs using root cause analysis.

-- Segment SKUs: Understand product behavior through ABC-XYZ segmentation for better inventory decisions.

-- Track Key Metrics: Monitor inventory turnover, reorder points, safety stock levels, and inactivity trends.

-- Leverage GenAI: Use AI-driven insights to interpret inventory health and support data-driven decisions.

-- Optimize Distribution: Discover how to distribute inventory across the network and schedule replenishments efficiently.

Use the sidebar to begin: Upload Data → View Dashboard → Get Recommendations


""")
