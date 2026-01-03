# Import necessary libraries
import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd
import altair as alt

# 1. Connect to Snowflake to get your data
session = get_active_session()

st.set_page_config(layout="wide") # Use the full screen width

st.title("🏥 Critical Supply Inventory")
st.write("Real-time stock monitoring for hospitals and NGOs.")

# 2. Load Data from your Dynamic Table
# We convert it to Pandas so Streamlit can use it easily
df_snow = session.table("HEALTH_INVENTORY_DB.PUBLIC.INVENTORY_HEALTH_METRICS")
df = df_snow.to_pandas()

# --- TOP METRICS SECTION ---
# We calculate three key numbers to show at the top
total_locations = df['LOCATION_ID'].nunique()
critical_count = len(df[df['STATUS'] == 'CRITICAL (Stockout Risk)'])
warning_count = len(df[df['STATUS'] == 'WARNING (Reorder Soon)'])

# Display them in 3 columns
col1, col2, col3 = st.columns(3)
col1.metric("🏥 Active Locations", total_locations)
col2.metric("🚨 Critical Stockouts", critical_count, delta_color="inverse")
col3.metric("⚠️ Warnings", warning_count, delta_color="off")

st.divider()

# --- HEATMAP SECTION ---
st.subheader("📍 Stock Health Heatmap")
st.info("Dark Red squares indicate items that are about to run out.")

# Create the Heatmap using Altair
heatmap = alt.Chart(df).mark_rect().encode(
    x=alt.X('LOCATION_ID', title='Location'),
    y=alt.Y('ITEM_NAME', title='Item'),
    # Color scale: Red (Low Days) to Green (High Days)
    color=alt.Color('DAYS_REMAINING', scale=alt.Scale(scheme='redyellowgreen', domain=[0, 30]), title='Days Left'),
    tooltip=['LOCATION_ID', 'ITEM_NAME', 'CURRENT_STOCK', 'STATUS', 'DAYS_REMAINING']
).properties(
    width='container', 
    height=400
)

st.altair_chart(heatmap, use_container_width=True)

# --- ACTION LIST SECTION ---
st.subheader("📋 Procurement Action List")
st.write("Prioritized list of items that need immediate reordering.")

# Filter: Show only CRITICAL or WARNING items
action_df = df[df['STATUS'] != 'GOOD'][['LOCATION_ID', 'ITEM_NAME', 'STATUS', 'CURRENT_STOCK', 'SUGGESTED_REORDER_QTY']]

# Display the table
st.dataframe(action_df, use_container_width=True)

# Add a download button for the procurement team
st.download_button(
    label="📥 Download Order List (CSV)",
    data=action_df.to_csv(index=False).encode('utf-8'),
    file_name='urgent_reorder_list.csv',
    mime='text/csv',
)
