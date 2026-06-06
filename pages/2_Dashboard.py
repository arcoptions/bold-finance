import streamlit as st
import pandas as pd
from core.database import fetch_from_ledger

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("Financial Dashboard")

with st.spinner("Fetching live data from Master Ledger..."):
    df = fetch_from_ledger()

if df.empty:
    st.info("The Master Ledger is currently empty. Please reconcile a bank statement first.")
else:
    # --- FILTERS ---
    st.markdown("### Filters")
    col1, col2 = st.columns(2)
    
    with col1:
        entities = ["All"] + list(df['Entity'].dropna().unique())
        selected_entity = st.selectbox("Filter by Entity", entities)
    
    with col2:
        # Extract unique months for filtering (Format: YYYY-MM)
        df['Month'] = df['Transaction Date'].dt.to_period('M').astype(str)
        months = ["All Time"] + list(df['Month'].dropna().unique())
        selected_month = st.selectbox("Filter by Month", months)

    # Apply Filters
    filtered_df = df.copy()
    if selected_entity != "All":
        filtered_df = filtered_df[filtered_df['Entity'] == selected_entity]
    if selected_month != "All Time":
        filtered_df = filtered_df[filtered_df['Month'] == selected_month]

    # --- KPI METRICS ---
    total_deposits = filtered_df['Deposits'].sum()
    total_withdrawals = filtered_df['Withdrawals'].sum()
    net_cashflow = total_deposits - total_withdrawals

    st.markdown("---")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Deposits", f"₹ {total_deposits:,.2f}")
    kpi2.metric("Total Withdrawals", f"₹ {total_withdrawals:,.2f}")
    kpi3.metric("Net Cash Flow", f"₹ {net_cashflow:,.2f}")

    # --- CHARTS ---
    st.markdown("---")
    st.subheader("Cash Flow Overview")
    
    # Group by month for charting
    if not filtered_df.empty:
        monthly_summary = filtered_df.groupby('Month')[['Deposits', 'Withdrawals']].sum().reset_index()
        st.bar_chart(data=monthly_summary, x='Month', y=['Deposits', 'Withdrawals'], use_container_width=True)
    
    # --- RAW DATA VIEW ---
    with st.expander("View Filtered Ledger Data"):
        st.dataframe(filtered_df.sort_values(by="Transaction Date", ascending=False), use_container_width=True)
