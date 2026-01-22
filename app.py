import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd
import altair as alt

# --- 1. PAGE CONFIGURATION (Must be the first command) ---
st.set_page_config(
    page_title="HealthSync Pro | Inventory Command",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. DATA LOADING & CACHING ---
# We cache the data loading to make the app feel faster when filtering
@st.cache_data
def load_data():
    session = get_active_session()
    # Fetch the table
    df_snow = session.table("HEALTH_INVENTORY_DB.PUBLIC.INVENTORY_HEALTH_METRICS")
    return df_snow.to_pandas()

try:
    df_raw = load_data()
except:
    st.error("⚠️ Could not connect to Snowflake. Make sure you are running this inside Snowflake!")
    st.stop()

# --- 3. SIDEBAR CONTROLS ---
with st.sidebar:
    st.title("🏥 HealthSync Pro")
    st.markdown("---")
    
    st.subheader("🔎 Filter View")
    
    # Filter 1: Location
    all_locations = sorted(df_raw['LOCATION_ID'].unique())
    selected_locations = st.multiselect("Select Locations", all_locations, default=all_locations)
    
    # Filter 2: Status
    all_statuses = sorted(df_raw['STATUS'].unique())
    selected_statuses = st.multiselect("Filter by Status", all_statuses, default=all_statuses)
    
    st.markdown("---")
    st.caption("Last Refreshed: Just now")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.experimental_rerun()

# --- 4. DATA FILTERING LOGIC ---
# Filter the dataframe based on sidebar inputs
df_filtered = df_raw[
    (df_raw['LOCATION_ID'].isin(selected_locations)) & 
    (df_raw['STATUS'].isin(selected_statuses))
]

# --- 5. TOP LEVEL METRICS (KPIs) ---
st.markdown("### 📊 Operational Overview")
col1, col2, col3, col4 = st.columns(4)

total_items = len(df_filtered)
critical_items = len(df_filtered[df_filtered['STATUS'] == 'CRITICAL (Stockout Risk)'])
warning_items = len(df_filtered[df_filtered['STATUS'] == 'WARNING (Reorder Soon)'])
avg_coverage = round(df_filtered['DAYS_REMAINING'].replace(999, 0).mean(), 1)

col1.metric("📦 Total SKUs Tracking", total_items)
col2.metric("🚨 Critical Alerts", critical_items, delta="-Action Needed" if critical_items > 0 else "All Good", delta_color="inverse")
col3.metric("⚠️ Reorder Warnings", warning_items, delta_color="off")
col4.metric("📅 Avg Stock Coverage", f"{avg_coverage} Days")

st.markdown("---")

# --- 6. MAIN TABS INTERFACE ---
tab_overview, tab_analysis, tab_action = st.tabs(["🌍 Global Heatmap", "📈 Risk Analysis", "📋 Procurement Desk"])

# === TAB 1: INTERACTIVE HEATMAP ===
with tab_overview:
    st.subheader("📍 Network-Wide Stock Health")
    
    if not df_filtered.empty:
        # Altair Heatmap with interactivity
        heatmap = alt.Chart(df_filtered).mark_rect().encode(
            x=alt.X('LOCATION_ID', title='Location', axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('ITEM_NAME', title='Item Name'),
            color=alt.Color('DAYS_REMAINING', scale=alt.Scale(scheme='redyellowgreen', domain=[0, 30]), title='Days Left'),
            tooltip=[
                alt.Tooltip('LOCATION_ID', title='Location'),
                alt.Tooltip('ITEM_NAME', title='Item'),
                alt.Tooltip('CURRENT_STOCK', title='Stock Level'),
                alt.Tooltip('DAYS_REMAINING', title='Days Left'),
                alt.Tooltip('STATUS', title='Status')
            ]
        ).properties(
            height=400,
            width='container'
        ).interactive() # Makes it zoomable/pannable
        
        st.altair_chart(heatmap, use_container_width=True)
    else:
        st.info("No data matches your filters.")

# === TAB 2: RISK ANALYSIS CHARTS ===
with tab_analysis:
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("**📉 Top 5 Items at Risk (Lowest Days Remaining)**")
        risk_df = df_filtered.sort_values('DAYS_REMAINING').head(5)
        
        bar_chart = alt.Chart(risk_df).mark_bar().encode(
            x=alt.X('DAYS_REMAINING', title='Days Remaining'),
            y=alt.Y('ITEM_NAME', sort='x', title=''),
            color=alt.Color('STATUS', scale=alt.Scale(domain=['CRITICAL (Stockout Risk)', 'WARNING (Reorder Soon)', 'GOOD'], range=['#d62728', '#ff7f0e', '#2ca02c']))
        )
        st.altair_chart(bar_chart, use_container_width=True)
        
    with col_b:
        st.markdown("**🛒 Supply Velocity (Avg Daily Usage)**")
        # Scatter plot to show which items move fastest
        scatter = alt.Chart(df_filtered).mark_circle(size=100).encode(
            x=alt.X('AVG_DAILY_USAGE', title='Daily Usage Rate'),
            y=alt.Y('CURRENT_STOCK', title='Current Stock Level'),
            color='STATUS',
            tooltip=['ITEM_NAME', 'LOCATION_ID', 'AVG_DAILY_USAGE']
        ).interactive()
        st.altair_chart(scatter, use_container_width=True)

# === TAB 3: PROCUREMENT DESK (ACTIONABLE TABLE) ===
with tab_action:
    st.subheader("📝 Procurement Orders")
    
    # Filter for items that need action
    action_df = df_filtered[df_filtered['STATUS'] != 'GOOD'].copy()
    
    if not action_df.empty:
        # Configure columns for a "Premium" look
        st.dataframe(
            action_df[['LOCATION_ID', 'ITEM_NAME', 'CURRENT_STOCK', 'SUGGESTED_REORDER_QTY', 'STATUS', 'DAYS_REMAINING']],
            column_config={
                "CURRENT_STOCK": st.column_config.ProgressColumn(
                    "Stock Level",
                    help="Visual representation of current stock",
                    format="%d",
                    min_value=0,
                    max_value=1000, # Adjust based on your typical stock max
                ),
                "SUGGESTED_REORDER_QTY": st.column_config.NumberColumn(
                    "Reorder Qty",
                    format="%d units"
                ),
                "STATUS": st.column_config.TextColumn(
                    "Risk Status",
                )
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Download Button
        csv = action_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Approved PO List (CSV)",
            data=csv,
            file_name='procurement_orders.csv',
            mime='text/csv',
            type="primary" # Makes the button blue/prominent
        )
    else:
        st.success("✅ No critical items found. Inventory is healthy!")
