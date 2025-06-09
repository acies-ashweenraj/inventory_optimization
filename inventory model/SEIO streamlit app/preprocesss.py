import streamlit as st
import pandas as pd
from operations import operations

# Instantiate operations class once
ops = operations()

def daily_to_weekly(df):
    daily_rows = []
    for i in range(len(df)):
        demand = df.loc[i, 'Demand Plan']
        date = pd.to_datetime(df.loc[i, 'Week'])
        for j in range(7):
            daily_rows.append({
                'day': date + pd.Timedelta(days=j),
                'daily_demand': demand / 7
            })
    daily_df = pd.DataFrame(daily_rows)
    return daily_df

def daily_data(df, ordering_cost, holding_cost, lead_time):
    df = df.copy()
    for i in range(len(df)):
        daily_demand = df.loc[i, 'daily_demand']
        if pd.isna(daily_demand) or daily_demand == 0:
            continue

        df.loc[i, "daily_eoq"], _ = ops.EOQ(ordering_cost, holding_cost, daily_demand)
        df.loc[i, 'cycle_time'] = ops.cycle_time(df.loc[i, 'daily_eoq'], daily_demand)
        df.loc[i, "cycle_time_in_hr"] = ops.cycle_time_in_hr(df.loc[i, "cycle_time"])
        df.loc[i, "full_cycles_in_lead_time"] = ops.full_cycle_in_lead_time(lead_time, df.loc[i, "cycle_time"])
        df.loc[i, "effective_lead_time"] = ops.effective_lead_time(
            lead_time, df.loc[i, "full_cycles_in_lead_time"], df.loc[i, "cycle_time"]
        )
        df.loc[i, "reorder_point"] = ops.reorder_point(daily_demand, df.loc[i, "effective_lead_time"])
    return df

# -------------------------
# Streamlit UI
# -------------------------

st.title("EOQ Inventory Calculator.")

st.sidebar.header("Parameters")
ordering_cost = st.sidebar.number_input("Ordering Cost", min_value=0.01, value=100.0, step=1.0)
holding_cost = st.sidebar.number_input("Holding Cost", min_value=0.01, value=5.0, step=0.1)
lead_time = st.sidebar.number_input("Lead Time (days)", min_value=1, value=5, step=1)

uploaded_file = st.file_uploader("Upload Weekly Demand CSV (must have 'Week' and 'Demand Plan' columns)", type=["csv"])

if uploaded_file:
    weekly_df = pd.read_csv(uploaded_file)

    # Validate columns
    if not {'Week', 'Demand Plan'}.issubset(weekly_df.columns):
        st.error("CSV must contain 'Week' and 'Demand Plan' columns.")
    else:
        st.info("Converting weekly demand to daily demand...")
        daily_df = daily_to_weekly(weekly_df)

        st.info("Calculating EOQ and inventory metrics...")
        result_df = daily_data(daily_df, ordering_cost, holding_cost, lead_time)

        st.success("Calculation complete!")
        st.dataframe(result_df)

        csv = result_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Result CSV", csv, "daily_inventory_output.csv", "text/csv")
