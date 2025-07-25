import streamlit as st
import pandas as pd
import os
import io

st.set_page_config(page_title="Distribution & Schedule Results", layout="wide")

# Paths to distribution and scheduling results
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DATA_PATH = os.path.join(BASE_PATH, "output_data")

DISTRIBUTION_FILES = {
    "DC → Warehouse Distribution": os.path.join(OUTPUT_DATA_PATH, "distribution", "dc_warehouse_distribution_df.xlsx"),
    "Warehouse → Store Distribution": os.path.join(OUTPUT_DATA_PATH, "distribution", "warehouse_store_distribution_df.xlsx")
}

SCHEDULING_FILES = {
    "Store Order Schedule": os.path.join(OUTPUT_DATA_PATH, "schedule_data", "stores_order_schedule.xlsx"),
    "Warehouse Order Schedule": os.path.join(OUTPUT_DATA_PATH, "schedule_data", "warehouses_order_schedule.xlsx")
}

def load_excel(path):
    try:
        return pd.read_excel(path, engine="openpyxl")
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return None

def display_section(title, files_dict):
    st.header(title)
    selected = st.selectbox(f"Select {title.lower()} file:", list(files_dict.keys()), key=title)

    file_path = files_dict[selected]
    if not os.path.exists(file_path):
        st.error(f"⚠️ File not found: {file_path}")
        return

    df = load_excel(file_path)
    if df is not None:
        st.dataframe(df, use_container_width=True)

        # Save to BytesIO for download
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)

        st.download_button(
            label="Download Excel",
            data=buffer,
            file_name=os.path.basename(file_path),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

def results_page():
    st.title("MEIO Results – Distribution & Scheduling")

    # Display Distribution Section
    display_section("Distribution Results", DISTRIBUTION_FILES)

    st.markdown("---")

    # Display Scheduling Section
    display_section("Scheduling Results", SCHEDULING_FILES)

if __name__ == "__main__":
    results_page()
