
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
st.title("Inventory Optimization Dashboard")

# --- Load Session Data ---
if "merged_df" not in st.session_state:
    st.warning("Please upload and submit your data in the Upload tab.")
    st.stop()

df = st.session_state["merged_df"].copy()
df.columns = df.columns.str.strip()

# --- Helper Function ---
def format_number_short(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f} M"
    elif n >= 1_000:
        return f"{n/1_000:.1f} K"
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

    if "Average Lead Time" not in df.columns:
        df["Average Lead Time"] = 7
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



    # --- KPI Metrics ---
    total_skus = df["SKU ID"].nunique()
    total_stock = int(df["Current Stock Quantity"].sum())
    total_value = df["Stock Value"].sum()

    # --- KPI Section ---
    st.markdown("### Key Inventory Metrics")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="**Total SKUs**", value=f"{total_skus:,}")
    with col2:
        st.metric(label="**Total Stock Quantity**", value=f"{format_number_short(total_stock)}")
    with col3:
        st.metric(label="**Inventory Value (₹)**", value=f"{format_number_short(total_value)}")

    # --- Inventory Health Section ---
    summary = df["Stock Status"].value_counts().to_dict()

    st.markdown("### Inventory Health Breakdown")
    with st.expander("Show Inventory Stock Health (Under / Over / Ideal)", expanded=True):
        col4, col5, col6 = st.columns(3)
        col4.metric("Understocked", f"🔻 {summary.get('Understocked', 0):,}")
        col5.metric("Overstocked", f"🔺 {summary.get('Overstocked', 0):,}")
        col6.metric("Ideal Stock", f"✅ {summary.get('Ideal', 0):,}")


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

   # --- Chart 1: Stock + Safety Stock vs Demand (with user input) ---
    st.subheader("Stock + Safety Stock vs Demand")

    # --- User Input: Service Level Percentage ---
    st.markdown("#### Enter Desired Service Level (%)")
    service_level_input = st.number_input("Enter a value between 50 and 99.99", min_value=50.0, max_value=99.99, value=95.0, step=0.1)

    # --- Convert Service Level to Z-score ---
    from scipy.stats import norm
    service_level_decimal = service_level_input / 100
    Z = round(norm.ppf(service_level_decimal), 2)

    st.markdown(f"**Z-score calculated for {service_level_input}% service level:** `{Z}`")

    # --- Safety Stock Calculation ---
    df_filtered["Daily Demand StdDev"] = df_filtered["Avg Daily Demand"] * 0.5  # Assume 50% coefficient of variation
    df_filtered["Safety Stock"] = Z * df_filtered["Daily Demand StdDev"] * np.sqrt(df_filtered["Average Lead Time"])

    # --- Total Coverage and Demand ---
    df_filtered["Total Coverage"] = df_filtered["Current Stock Quantity"] + df_filtered["Safety Stock"]
    df_filtered["Total Demand"] = df_filtered["Order Quantity sum"]

    # --- Select Top 15 SKUs by Demand ---
    top15 = df_filtered.sort_values("Total Demand", ascending=False).head(15)

    # --- Plotting ---
    from plotly.subplots import make_subplots

    fig_stock = make_subplots(specs=[[{"secondary_y": True}]])

    # Bar: Current Stock (primary axis)
    fig_stock.add_trace(go.Bar(
        x=top15["SKU ID"],
        y=top15["Current Stock Quantity"],
        name="Current Stock",
        marker_color="#4e79a7"
    ), secondary_y=False)

    # Bar: Safety Stock (secondary axis)
    fig_stock.add_trace(go.Bar(
        x=top15["SKU ID"],
        y=top15["Safety Stock"],
        name="Safety Stock",
        marker_color="#f28e2c",
        opacity=0.7
    ), secondary_y=True)

    # Line: Total Demand (primary axis)
    fig_stock.add_trace(go.Scatter(
        x=top15["SKU ID"],
        y=top15["Total Demand"],
        name="Total Demand",
        mode="lines+markers",
        line=dict(color="#e15759", width=3)
    ), secondary_y=False)

    # Layout
    fig_stock.update_layout(
        xaxis_title="Top SKUs",
        yaxis_title="Stock / Demand Quantity",
        title=f"Stock vs Demand with Safety Stock ({service_level_input:.1f}% Service Level)",
        height=450,
        barmode="group"  # group so bars don't stack
    )

    # Secondary axis title
    fig_stock.update_yaxes(title_text="Safety Stock (Secondary Axis)", secondary_y=True)

    st.plotly_chart(fig_stock, use_container_width=True)


    # --- Chart 2: RCA Scatter Plot ---
    st.subheader("Root Cause Analysis (Stock vs Demand)")
    fig_rca = px.scatter( df_filtered, x="Order Quantity sum", y="Current Stock Quantity", color="Stock Status", hover_data=["SKU ID", "Avg Daily Demand", "Safety Stock"], color_discrete_map={"Understocked": "red", "Overstocked": "blue", "Ideal": "green"}, labels={"Order Quantity sum": "Total Demand", "Current Stock Quantity": "Current Stock"}, title="SKU Inventory Positioning" ) 
    fig_rca.update_layout(height=450) 
    st.plotly_chart(fig_rca, use_container_width=True)
    # --- RCA Explanation Section ---
    st.subheader("RCA Explanation by SKU")
    sku_selected = st.selectbox("Select a SKU:", options=df_filtered["SKU ID"].unique())
    sku_row = df_filtered[df_filtered["SKU ID"] == sku_selected].iloc[0]

    # --- KPI CARDS ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Current Stock", f"{int(sku_row['Current Stock Quantity'])}")
    col2.metric("Total Demand (Year)", f"{int(sku_row['Order Quantity sum'])}")
    col3.metric("Safety Stock", f"{sku_row['Safety Stock']:.2f}")
    col4.metric("Lead Time (Days)", f"{sku_row['Average Lead Time']}")
    # --- Stock Status Gauge ---
 
    reorder_point = sku_row["Avg Daily Demand"] * sku_row["Average Lead Time"] + sku_row["Safety Stock"]
    demand = sku_row["Order Quantity sum"]


    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=sku_row["Current Stock Quantity"],
        delta={'reference': demand, 'increasing': {'color': "red"}},
        title={'text': f"Stock Level (SKU: {sku_selected})"},
        gauge={
            'axis': {'range': [0, max(demand*1.5, sku_row["Current Stock Quantity"])]},
            'bar': {'color': "blue"},
            'steps': [
                {'range': [0, reorder_point], 'color': "#FF9999"},      # Understock
                {'range': [reorder_point, demand], 'color': "#99CC99"}, # Optimal
                {'range': [demand, max(demand*1.5, sku_row["Current Stock Quantity"])], 'color': "#FFCC99"} # Overstock
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'value': sku_row["Current Stock Quantity"]
            }
        }
    ))
    fig_gauge.update_layout(
    margin=dict(l=50, r=180, t=80, b=50),
    height=300, 
    )
    fig_gauge.add_annotation(
        x=1.25, y=0.9, xref="paper", yref="paper", showarrow=False,
        text="<b>Legend:</b><br>"
            "<span style='color:#FF9999'>■</span> Understocked<br>"
            "<span style='color:#99CC99'>■</span> Optimal<br>"
            "<span style='color:#FFCC99'>■</span> Overstocked",
        align="left",
        bgcolor="white",  
        bordercolor="black",
        borderwidth=0.5
    )


    fig_gauge.update_layout(
        margin=dict(l=50, r=180, t=80, b=50) 
    )

    st.plotly_chart(fig_gauge, use_container_width=True)
    st.markdown(f"""
    **Legend:**
    - **Red:** Understocked (< {int(reorder_point)})
    - **Green:** Optimal ({int(reorder_point)} – {int(demand)})
    - **Orange:** Overstocked (> {int(demand)})
    """)
    # --- ROOT CAUSE & ACTION CARDS ---
    st.markdown("### Root Cause & Recommendation")

    cause_card, risk_card, action_card = st.columns(3)

    # 🔳 General pastel card template
    def pastel_card(title, text, bg_color, text_color):
        return f"""
            <div style="
                background-color:{bg_color};
                padding:15px;
                border-radius:10px;
                border:1px solid #ddd;
                min-height:140px;">
                <strong style="color:{text_color};">{title}</strong>
                <p style="color:{text_color}; margin-top:8px;">{text}</p>
            </div>
        """

    # 🎨 Colors (soft pastel tones)
    PASTEL_RED_BG = "#fdecea"
    PASTEL_RED_TEXT = "#7f1d1d"

    PASTEL_YELLOW_BG = "#fffbea"
    PASTEL_YELLOW_TEXT = "#92400e"

    PASTEL_GREEN_BG = "#ecfdf5"
    PASTEL_GREEN_TEXT = "#065f46"

    if sku_row["Stock Status"] == "Understocked":
        with cause_card:
            st.markdown(pastel_card("Cause", "Demand exceeds available stock.", PASTEL_RED_BG, PASTEL_RED_TEXT), unsafe_allow_html=True)
        with risk_card:
            st.markdown(pastel_card("Risk", "Possible stockouts, unmet customer demand.", PASTEL_YELLOW_BG, PASTEL_YELLOW_TEXT), unsafe_allow_html=True)
        with action_card:
            st.markdown(pastel_card("Action", "Increase orders, review supplier lead times.", PASTEL_GREEN_BG, PASTEL_GREEN_TEXT), unsafe_allow_html=True)

    elif sku_row["Stock Status"] == "Overstocked":
        with cause_card:
            st.markdown(pastel_card("Cause", "Stock level far exceeds demand.", PASTEL_RED_BG, PASTEL_RED_TEXT), unsafe_allow_html=True)
        with risk_card:
            st.markdown(pastel_card("Risk", "High holding cost, risk of obsolescence.", PASTEL_YELLOW_BG, PASTEL_YELLOW_TEXT), unsafe_allow_html=True)
        with action_card:
            st.markdown(pastel_card("Action", "Pause reorders, run clearance, review forecast.", PASTEL_GREEN_BG, PASTEL_GREEN_TEXT), unsafe_allow_html=True)

    else:  # Balanced
        with cause_card:
            st.markdown(pastel_card("Cause", "Stock aligned with demand.", PASTEL_GREEN_BG, PASTEL_GREEN_TEXT), unsafe_allow_html=True)
        with risk_card:
            st.markdown(pastel_card("Risk", "Minimal — inventory is balanced.", PASTEL_YELLOW_BG, PASTEL_YELLOW_TEXT), unsafe_allow_html=True)
        with action_card:
            st.markdown(pastel_card("Action", "Maintain current strategy, keep monitoring.", PASTEL_GREEN_BG, PASTEL_GREEN_TEXT), unsafe_allow_html=True)

   # --- Chart 3: Top SKUs by Custom Metric ---

    # --- Metric Options ---
    metric_options = {
        "Order Quantity": "Order Quantity sum",
        "Order Value (₹)": "Order Value",
        "Current Stock Quantity": "Current Stock Quantity",
        "Stock Value (₹)": "Stock Value",
        "Average Daily Demand": "Avg Daily Demand"
    }

    # --- Dropdown for Metric Selection ---
    selected_metric_label = st.selectbox("Select a metric to view top SKUs:", list(metric_options.keys()))
    selected_metric_col = metric_options[selected_metric_label]

    # --- Prepare Data ---
    if "Order Value" not in df_filtered.columns:
        df_filtered["Order Value"] = df_filtered["Order Quantity sum"] * df_filtered["Unit Price"]

    top_metric = df_filtered.sort_values(by=selected_metric_col, ascending=False).head(15)

    # --- Plotting ---
    fig_top_metric = px.bar(
        top_metric,
        x=selected_metric_col,
        y="SKU ID",
        orientation="h",
        color=selected_metric_col,
        color_continuous_scale="Viridis",
        labels={selected_metric_col: selected_metric_label},
        title=f"Top SKUs by {selected_metric_label}"
    )
    fig_top_metric.update_layout(height=450, yaxis_title="SKU ID", xaxis_title=selected_metric_label)
    st.plotly_chart(fig_top_metric, use_container_width=True)


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


    st.markdown("""
        <style>
            body {
                background-color: #0E1117;
                color: white;
            }
            .metric-box {
                background-color: white; /* bluish tone */
                color: black;
                padding: 20px;
                border-radius: 12px;
                border: 1px solid #444;
                text-align: center;
                box-shadow: 2px 2px 10px rgba(0,0,0,0);
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h3>SKU Segmentation & Inactivity Analysis</h3>", unsafe_allow_html=True)

    if 'merged_df' not in st.session_state:
        st.warning("Please upload and submit data in the Upload page first.")
        st.stop()

    df = st.session_state['merged_df'].copy()

    # Rename and fill missing columns
    if 'Average Lead Time' in df.columns:
        df.rename(columns={'Average Lead Time': 'Average Lead Time'}, inplace=True)
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

        df['Avg Daily Demand'] = df['Order Quantity sum'] / df['Average Lead Time'].replace(0, np.nan)
        df['Avg Daily Demand'] = df['Avg Daily Demand'].fillna(0)
        df['Reorder Point'] = df['Avg Daily Demand'] * df['Average Lead Time'] + df['Safety Stock']
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
        
        # --- Inactivity Table View ---
            # --- Inactivity Analysis Table with Time Granularity (No Range Slider) ---

            st.markdown("<h4 style='margin-top:40px;'>📋 Inactivity Analysis</h4>", unsafe_allow_html=True)

            # --- Time Granularity Selector ---
            granularity = st.selectbox("Select Time Granularity:", ["Days", "Weeks", "Months", "Years"])

            # --- Convert Days Since Last Movement into Selected Granularity ---
            def convert_granularity(days, granularity):
                if days < 0:
                    return "No Movement"
                if granularity == "Weeks":
                    return f"{int(days // 7)} weeks"
                elif granularity == "Months":
                    return f"{int(days // 30)} months"
                elif granularity == "Years":
                    return f"{int(days // 365)} years"
                else:
                    return f"{int(days)} days"

            filtered_df_inactivity["Inactivity Bucket"] = filtered_df_inactivity["Days Since Last Movement"].apply(
                lambda x: convert_granularity(x, granularity)
            )

            # --- Bucket Filter Dropdown ---
            bucket_options = sorted(filtered_df_inactivity["Inactivity Bucket"].unique())
            selected_buckets = st.multiselect("Filter by Inactivity Bucket:", ["All"] + bucket_options, default=["All"])

            if "All" in selected_buckets or not selected_buckets:
                df_inact_filtered = filtered_df_inactivity.copy()
            else:
                df_inact_filtered = filtered_df_inactivity[filtered_df_inactivity["Inactivity Bucket"].isin(selected_buckets)]

            # --- Columns to Display ---
            display_cols = [
                "SKU ID",
                "Category" if "Category" in df_inact_filtered.columns else None,
                "Current Stock Quantity",
                "Days Since Last Movement",
                "Inactivity Bucket",
                "Movement Category"
            ]
            if "ABC-XYZ Class" in df_inact_filtered.columns:
                display_cols.append("ABC-XYZ Class")

            # Clean column list
            display_cols = [col for col in display_cols if col]

            # --- Display Table ---
            st.dataframe(
                df_inact_filtered[display_cols].sort_values("Days Since Last Movement", ascending=False).reset_index(drop=True),
                use_container_width=True
            )




        # --------------------- Export Section -------------------
        st.markdown("<h3 style='color:white'>Export Metrics to Excel</h3>", unsafe_allow_html=True)

        # --- Display each option as a checkbox ---
        abc_selected = st.checkbox("ABC Inventory Classification")
        xyz_selected = st.checkbox("XYZ Classification")
        itr_selected = st.checkbox("Inventory Turnover Ratio")
        reorder_selected = st.checkbox("Reorder points")
        status_selected = st.checkbox("Stock Status Classification")

        if st.button("Export to Excel"):
            selected = any([abc_selected, xyz_selected, itr_selected, reorder_selected, status_selected])
            
            if not selected:
                st.warning("Please select at least one metric to export.")
            else:
                export_df = pd.DataFrame()
                export_df["SKU ID"] = df["SKU ID"]

                if abc_selected:
                    export_df["ABC Class"] = df["ABC Class"]
                if xyz_selected:
                    export_df["XYZ Class"] = df["XYZ Class"]
                if itr_selected:
                    export_df["Inventory Turnover Ratio"] = df["Inventory Turnover Ratio"]
                if reorder_selected:
                    export_df["Reorder Point"] = df["Reorder Point"]
                if status_selected:
                    export_df["Stock Status"] = df["Movement Category"]

                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    export_df.to_excel(writer, index=False, sheet_name="Metrics Export")

                st.download_button("Download Excel", data=buffer.getvalue(), file_name="inventory_metrics_export.xlsx")


    except Exception as e:
        st.error(f"Analysis Error: {e}")
