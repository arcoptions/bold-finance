import streamlit as st

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("Financial Dashboard")

st.markdown("This module will pull data from the Transactions_Master tab to display metrics.")

# Placeholder for future database fetching logic
# master_data = fetch_from_ledger("Transactions_Master")

col1, col2, col3 = st.columns(3)
col1.metric("Total Deposits (Current Month)", "Loading...")
col2.metric("Total Withdrawals (Current Month)", "Loading...")
col3.metric("Net Operating Cash Flow", "Loading...")

st.info("Charting and aggregation logic will automatically populate here once the master ledger has active data.")
