import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import BytesIO
from dotenv import load_dotenv
import os

# --- Page Setup ---
st.set_page_config(page_title="Unified Inventory Dashboard", layout="wide")
st.title("📦 Inventory Optimization Dashboard")

# --- Load Session Data ---
if "merged_df" not in st.session_state:
    st.warning("Please upload and submit your data in the Upload tab.")
    st.stop()

df = st.session_state["merged_df"].copy()
df.columns = df.columns.str.strip()

# --- Helper Function ---
def format_number_short(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.1f}K"
    else:
        return str(int(n))

# --- TAB LAYOUT ---
tabs = st.tabs(["Inventory Health & RCA", " GenAI Chatbot", " Segmentation & Metrics"])

# ----------------------------- TAB 1: Inventory Analysis -----------------------------
with tabs[0]:
    st.subheader("Inventory Health & RCA Analysis")

    if "merged_df" not in st.session_state:
        st.warning("Please upload and submit your data in the Upload tab.")
        st.stop()

    df = st.session_state["merged_df"].copy()
    df.columns = df.columns.str.strip()

    # --- Basic Column Validations ---
    required_cols = ['SKU ID', 'Current Stock Quantity', 'Unit Price']
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing column: {col}")
            st.stop()

    # --- Generate Missing Columns ---
    if "Order Quantity sum" not in df.columns:
        df["Order Quantity sum"] = df["Current Stock Quantity"] * 0.7 + np.random.normal(0, 0.2, len(df)) * df["Current Stock Quantity"]
        df["Order Quantity sum"] = df["Order Quantity sum"].clip(lower=0).round()

    if "Average Lead Time (days)" not in df.columns:
        df["Average Lead Time (days)"] = 7
    if "Maximum Lead Time (days)" not in df.columns:
        df["Maximum Lead Time (days)"] = 10
    if "Safety Stock" not in df.columns:
        df["Safety Stock"] = df["Current Stock Quantity"] * 0.1

    # --- Derived Columns ---
    df["Stock Value"] = df["Current Stock Quantity"] * df["Unit Price"]
    df["Avg Daily Demand"] = df["Order Quantity sum"] / 365

    # --- Stock Health Classification ---
    def classify(row):
        demand = row["Order Quantity sum"]
        stock = row["Current Stock Quantity"]
        gap = 0.1 * demand
        if demand == 0:
            return "Overstocked" if stock > 0 else "Ideal"
        if abs(stock - demand) <= gap:
            return "Ideal"
        elif stock > demand:
            return "Overstocked"
        else:
            return "Understocked"

    df["Stock Status"] = df.apply(classify, axis=1)
    def format_number_short(n):
        if n >= 1_000_000:
            return f"{n/1_000_000:.2f}M"
        elif n >= 1_000:
            return f"{n/1_000:.2f}K"
        else:
            return str(int(n))


    # --- KPI Metrics ---
    total_skus = df["SKU ID"].nunique()
    total_stock = int(df["Current Stock Quantity"].sum())
    total_value = df["Stock Value"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total SKUs", total_skus)
    col2.metric("Total Stock Quantity", total_stock)
    col3.metric("Inventory Value (₹)", f"{format_number_short(total_value)}")

    # --- Smooth Expand Transition for Inventory Health ---
    summary = df["Stock Status"].value_counts().to_dict()

    with st.expander("Show Inventory Stock Health (Under / Over / Ideal)"):
        col4, col5, col6 = st.columns(3)
        col4.metric("Understocked", summary.get("Understocked", 0))
        col5.metric("Overstocked", summary.get("Overstocked", 0))
        col6.metric("Ideal Stock", summary.get("Ideal", 0))

    # --- Filter Section with "ALL" Option ---
    st.markdown("### Filter by Stock Health")

    stock_status_options = ["ALL"] + df["Stock Status"].unique().tolist()
    selected_status = st.multiselect(
        "Select Stock Status",
        options=stock_status_options,
        default=["ALL"]
    )

    # Ensure "ALL" is exclusive
    if "ALL" in selected_status and len(selected_status) > 1:
        selected_status = [s for s in selected_status if s != "ALL"]

    # Filter the dataframe
    if "ALL" in selected_status:
        df_filtered = df.copy()
    else:
        df_filtered = df[df["Stock Status"].isin(selected_status)]

    st.markdown("---")

    # --- Chart 1: Stock vs Safety Stock ---
    st.subheader("Stock vs Safety Stock (Top SKUs at Risk)")
    top15 = df_filtered.sort_values("Current Stock Quantity", ascending=False).head(15)
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(x=top15["SKU ID"], y=top15["Current Stock Quantity"], name="Current Stock", marker_color="#4e79a7"))
    fig1.add_trace(go.Scatter(x=top15["SKU ID"], y=top15["Safety Stock"], name="Safety Stock", mode="lines+markers", line=dict(color="#e15759", width=2)))
    fig1.update_layout(barmode='group', xaxis_title="Top SKUs", yaxis_title="Quantity", height=400)
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")

    # --- Chart 2: RCA Scatter Plot ---
    st.subheader("Root Cause Analysis (Stock vs Demand)")
    fig_rca = px.scatter(
        df_filtered,
        x="Order Quantity sum",
        y="Current Stock Quantity",
        color="Stock Status",
        hover_data=["SKU ID", "Avg Daily Demand", "Safety Stock"],
        color_discrete_map={"Understocked": "red", "Overstocked": "blue", "Ideal": "green"},
        labels={"Order Quantity sum": "Total Demand", "Current Stock Quantity": "Current Stock"},
        title="SKU Inventory Positioning"
    )
    fig_rca.update_layout(height=450)
    st.plotly_chart(fig_rca, use_container_width=True)

    # --- RCA Explanation for a Selected SKU ---
    st.subheader("RCA Explanation by SKU")
    sku_selected = st.selectbox("Select a SKU:", options=df_filtered["SKU ID"].unique())
    sku_row = df_filtered[df_filtered["SKU ID"] == sku_selected].iloc[0]

    st.write(f"**SKU ID:** `{sku_selected}`")
    st.write(f"**Stock Status:** `{sku_row['Stock Status']}`")
    st.write(f"**Current Stock:** {sku_row['Current Stock Quantity']:.0f}")
    st.write(f"**Total Demand (Year):** {sku_row['Order Quantity sum']:.0f}")
    st.write(f"**Average Daily Demand:** {sku_row['Avg Daily Demand']:.2f}")
    st.write(f"**Safety Stock:** {sku_row['Safety Stock']:.2f}")
    st.write(f"**Lead Time:** {sku_row['Average Lead Time (days)']} days")

    # --- RCA Narrative ---
    st.markdown("### Root Cause & Recommendation")
    if sku_row["Stock Status"] == "Understocked":
        st.error("This SKU has **Low DOS**. You're at risk of stockouts.")
        st.markdown("""
        - **Cause**: Demand is exceeding your current inventory.
        - **Recommended Stock**: Add buffer above lead time demand.
        - **Action**: Increase order frequency or safety stock.
        - **Hint**: Check supplier delays or inaccurate forecasts.
        """)
    elif sku_row["Stock Status"] == "Overstocked":
        st.info("This SKU has **High DOS**. You may have tied up too much capital.")
        st.markdown("""
        - **Cause**: Current stock significantly exceeds demand.
        - **Risk**: Higher holding cost, obsolescence.
        - **Action**: Pause reorders, clear slow-movers.
        - **Hint**: Check outdated demand forecast.
        """)
    else:
        st.success("This SKU has **Adequate DOS**.")
        st.markdown("""
        - You’ve balanced stock and demand efficiently.
        - Keep monitoring lead time and demand trends.
        """)

    st.markdown("---")

    # --- Chart 3: Top SKUs by Order Value ---
    st.subheader("Top SKUs by Order Value")
    df_filtered["Order Value"] = df_filtered["Order Quantity sum"] * df_filtered["Unit Price"]
    top_value = df_filtered.sort_values(by="Order Value", ascending=False).head(15)
    fig3 = px.bar(top_value, x="Order Value", y="SKU ID", orientation="h", color="Order Value", color_continuous_scale="Viridis")
    fig3.update_layout(height=450, yaxis_title="SKU ID", xaxis_title="Order Value (₹)")
    st.plotly_chart(fig3, use_container_width=True)

# ----------------------------- TAB 2: GenAI Chatbot -----------------------------
with tabs[1]:
    st.subheader("GenAI Inventory Assistant")

    df_sample = df.head(10).to_csv(index=False)
    load_dotenv()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    MODEL = "llama3-70b-8192"
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

    query = st.text_area("Ask your inventory question:")
    if query:
        with st.spinner("Thinking..."):
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            messages = [
                {"role": "system", "content": "You are a best inventory analyst. Use the given sample inventory data (in CSV) to answer the question."},
                {"role": "user", "content": f"Inventory Data Sample (CSV):\n{df_sample}\n\nQuestion: {query}"}
            ]
            payload = {
                "model": MODEL,
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 700
            }
            response = requests.post(GROQ_URL, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                answer = result["choices"][0]["message"]["content"]
                st.success("Answer:")
                st.markdown(answer)
            else:
                st.error(f"API Error: {response.status_code}")
                st.code(response.text)

# ----------------------------- TAB 3: Segmentation -----------------------------
with tabs[2]:
    st.subheader("SKU Segmentation & Inactivity")

    # Ensure required fields
    def format_number_short(n):
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        elif n >= 1_000:
            return f"{n/1_000:.1f}K"
        else:
            return str(int(n))

    st.markdown("""
        <style>
            body {
                background-color: #0E1117;
                color: white;
            }
            .metric-box {
                background-color: #1f1f1f;
                color: white;
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #444;
                text-align: center;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center;'>SKU Segmentation & Inactivity Analysis</h1>", unsafe_allow_html=True)

    if 'merged_df' not in st.session_state:
        st.warning("Please upload and submit data in the Upload page first.")
        st.stop()

    df = st.session_state['merged_df'].copy()

    # Rename and fill missing columns
    if 'Average Lead Time' in df.columns:
        df.rename(columns={'Average Lead Time': 'Average Lead Time (days)'}, inplace=True)
    if 'Safety Stock' not in df.columns:
        df['Safety Stock'] = 0

    if 'Last Order Date' in df.columns and 'First Order Date' in df.columns and 'Active Order Days' in df.columns:
        df['Median Days Between Orders'] = df['Active Order Days'] / df['Order Quantity sum'].replace(0, np.nan)
        df['Median Days Between Orders'] = df['Median Days Between Orders'].fillna(0)

    # Process dates and assign movement categories
    try:
        df['Last Order Date'] = pd.to_datetime(df['Last Order Date'], errors='coerce')
        latest_data_date = df['Last Order Date'].max()
        df['Days Since Last Movement'] = (latest_data_date - df['Last Order Date']).dt.days.fillna(-1)

        def classify_movement(row):
            if row['Order Quantity sum'] == 0:
                return 'Non-moving'
            elif pd.notnull(row['Median Days Between Orders']) and row['Median Days Between Orders'] < 30 and \
                row['Order Quantity sum'] >= df['Order Quantity sum'].quantile(0.75):
                return 'Fast-moving'
            else:
                return 'Slow-moving'

        df['Movement Category'] = df.apply(classify_movement, axis=1)

        df_inactivity = df[df['Days Since Last Movement'] <= 730]

        df['Avg Daily Demand'] = df['Order Quantity sum'] / df['Average Lead Time (days)'].replace(0, np.nan)
        df['Avg Daily Demand'] = df['Avg Daily Demand'].fillna(0)
        df['Reorder Point'] = df['Avg Daily Demand'] * df['Average Lead Time (days)'] + df['Safety Stock']
        df['Inventory Turnover Ratio'] = df['Order Quantity sum'] / df['Current Stock Quantity'].replace(0, np.nan)
        df['Inventory Turnover Ratio'] = df['Inventory Turnover Ratio'].fillna(0)

        # ABC-XYZ Classification
        df['Consumption Value'] = df['Order Quantity sum'] * df['Unit Price']
        df = df.sort_values('Consumption Value', ascending=False)
        df['Cumulative %'] = 100 * df['Consumption Value'].cumsum() / df['Consumption Value'].sum()
        df['ABC Class'] = df['Cumulative %'].apply(lambda x: 'A' if x <= 70 else ('B' if x <= 90 else 'C'))
        df['CV'] = df['Order Quantity std'] / df['Order Quantity mean'].replace(0, np.nan)
        df['CV'] = df['CV'].fillna(0)
        df['XYZ Class'] = df['CV'].apply(lambda x: 'X' if x <= 0.5 else ('Y' if x <= 1 else 'Z'))
        df['ABC-XYZ Class'] = df['ABC Class'] + '-' + df['XYZ Class']

        # -------------------- KPI and PIE CHART Section ----------------------
        status_counts = df['Movement Category'].value_counts().reset_index()
        status_counts.columns = ['Stock Status', 'Count']

        col1, col2, col3 = st.columns(3)
        col1.markdown(f"<div class='metric-box'><h3>{df['SKU ID'].nunique()}</h3><p>SKU Count</p></div>", unsafe_allow_html=True)
        inventory_value = df['Consumption Value'].sum()
        col2.markdown(f"<div class='metric-box'><h3>₹{format_number_short(inventory_value)}</h3><p>Total Inventory Value</p></div>", unsafe_allow_html=True)
        col3.markdown(f"<div class='metric-box'><h3>{df['Order Quantity mean'].mean():.2f}</h3><p>Average Order Quantity</p></div>", unsafe_allow_html=True)

        st.plotly_chart(px.pie(status_counts, names='Stock Status', values='Count', hole=0.5), use_container_width=True)

        # --------------------- Filters (AFTER KPI) -----------------------
        
        selected_status = st.selectbox("Filter by Movement Category:", ['All'] + list(status_counts['Stock Status']))

        filtered_df = df if selected_status == 'All' else df[df['Movement Category'] == selected_status]
        filtered_df_inactivity = df_inactivity if selected_status == 'All' else df_inactivity[df_inactivity['Movement Category'] == selected_status]

        # --------------------- Heatmap -------------------------
        st.markdown("<h3 style='color:black'>ABC-XYZ Heatmap</h3>", unsafe_allow_html=True)
        abc_xyz_df = filtered_df.groupby(['ABC Class', 'XYZ Class']).size().reset_index(name='Count')
        pivot_df = abc_xyz_df.pivot(index='XYZ Class', columns='ABC Class', values='Count').fillna(0).sort_index(ascending=False)
        fig_heatmap = go.Figure(go.Heatmap(
            z=pivot_df.values,
            x=list(pivot_df.columns),
            y=list(pivot_df.index),
            text=pivot_df.values,
            texttemplate="%{text}",
            colorscale='earth',
            colorbar=dict(title='No. of SKUs')
        ))
        st.plotly_chart(fig_heatmap, use_container_width=True)

        # ---------------------- Inactivity Buckets ---------------------
        st.markdown("<hr><h3 style='color:black'>Inactivity Buckets</h3><p style='color:white'>How long since SKUs were last ordered?</p>", unsafe_allow_html=True)
        bucket_view = st.selectbox("", ['Weeks', 'Months', 'Days'])

        def get_bucket_label(days):
            if days < 0:
                return 'No Movement'
            if bucket_view == 'Weeks':
                return f"{int(days // 7)}-{int(days // 7 + 1)} weeks"
            elif bucket_view == 'Months':
                return f"{int(days // 30)}-{int(days // 30 + 1)} months"
            else:
                return f"{int(days)}-{int(days + 1)} days"

        filtered_df_inactivity['Inactivity Bucket'] = filtered_df_inactivity['Days Since Last Movement'].apply(get_bucket_label)

        if selected_status == 'Non-moving':
            st.info("Non-moving SKUs have no recorded last order date, so they're not bucketed by inactivity.")
        else:
            inactive_summary = filtered_df_inactivity['Inactivity Bucket'].value_counts().reset_index()
            inactive_summary.columns = ['Inactivity Period', 'Inactive SKU Count']
            st.bar_chart(inactive_summary.set_index('Inactivity Period'))

        # --------------------- Export Section -------------------
        st.markdown("<h3 style='color:black'>Export Metrics to Excel</h3>", unsafe_allow_html=True)
        options = st.multiselect("Choose data to export:", [
            "ABC Inventory Classification",
            "XYZ Classification",
            "Inventory Turnover Ratio",
            "Reorder points",
            "Stock Status Classification"
        ])
        if st.button("Export to Excel"):
            export_df = pd.DataFrame()
            export_df["SKU ID"] = df["SKU ID"]
            if "ABC Inventory Classification" in options:
                export_df["ABC Class"] = df["ABC Class"]
            if "XYZ Classification" in options:
                export_df["XYZ Class"] = df["XYZ Class"]
            if "Inventory Turnover Ratio" in options:
                export_df["Inventory Turnover Ratio"] = df["Inventory Turnover Ratio"]
            if "Reorder points" in options:
                export_df["Reorder Point"] = df["Reorder Point"]
            if "Stock Status Classification" in options:
                export_df["Stock Status"] = df["Movement Category"]
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                export_df.to_excel(writer, index=False, sheet_name="Metrics Export")
            st.download_button("Download Excel", data=buffer.getvalue(), file_name="inventory_metrics_export.xlsx")

    except Exception as e:
        st.error(f"Analysis Error: {e}")
