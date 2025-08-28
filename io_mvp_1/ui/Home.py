import streamlit as st
from pathlib import Path
st.set_page_config(layout="wide", page_title="Inventory Assistant")
base_dir = Path(__file__).resolve().parent

# Logo path (same folder as Home.py)
logo_path = base_dir / "acies_global_logo.jpeg"

col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("## Inventory Analytics & Assistant")
with col2:
    # st.image(r"C:\Users\Mythreye\Desktop\Meio_mvp1\inventory_optimization\io_mvp_1\ui\acies_global_logo.jpeg", width=80)
    st.image(str(logo_path), width=80)  
st.markdown("---")


st.markdown("""
### Welcome to the Inventory Optimization Platform

This application enables you to transform your inventory operations through intelligent planning, analysis, and replenishment strategies.

**Key Capabilities:**

**Upload and Analyze:** Import your inventory, demand forecast, product master, and network structure to begin a unified analysis.

**Identify Imbalances:** Automatically detect overstocked or understocked SKUs using root cause diagnostics.

**Segment SKUs:** Perform ABC-XYZ classification to understand SKU importance and variability for strategic stocking.

**Track Key Metrics:** Monitor cycle stock, reorder points, safety stock levels, lead times, and inactivity patterns.

**AI-Powered Insights:** Leverage GenAI to interpret inventory health, recommend actions, and support better decisions.

**Optimize Distribution:** Determine how to allocate and distribute inventory across nodes with calculated order quantities and schedules.

To get started, use the sidebar:
**Upload Data → View Dashboard → Get Recommendations**
""")