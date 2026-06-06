import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.database import fetch_table
from core.ui import inject_custom_css, render_sidebar_logo

st.set_page_config(page_title="Dashboard", layout="wide")
inject_custom_css()
render_sidebar_logo()

st.title("Financial Dashboard")

df = fetch_table("Transactions_Master")

if df.empty:
    st.info("The Master Ledger is empty. Process a statement to view analytics.")
else:
    df['Deposits'] = pd.to_numeric(df['Deposits'], errors='coerce').fillna(0)
    df['Withdrawals'] = pd.to_numeric(df['Withdrawals'], errors='coerce').fillna(0)
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
    
    # Global Filters
    col1, col2 = st.columns(2)
    with col1:
        entity_filter = st.selectbox("Entity View", ["All", "Socialight", "Bold and Italic"])
    with col2:
        df['Month'] = df['Transaction Date'].dt.to_period('M').astype(str)
        month_filter = st.selectbox("Period", ["All Time"] + list(df['Month'].unique()))

    # Apply Filters
    filtered_df = df.copy()
    if entity_filter != "All":
        filtered_df = filtered_df[filtered_df['Entity'] == entity_filter]
    if month_filter != "All Time":
        filtered_df = filtered_df[filtered_df['Month'] == month_filter]

    # Metrics
    tot_dep = filtered_df['Deposits'].sum()
    tot_wth = filtered_df['Withdrawals'].sum()
    net_cf = tot_dep - tot_wth

    m1, m2, m3 = st.columns(3)
    m1.metric("Revenue (Deposits)", f"INR {tot_dep:,.2f}")
    m2.metric("Expenses (Withdrawals)", f"INR {tot_wth:,.2f}")
    m3.metric("Net Cash Flow", f"INR {net_cf:,.2f}")

    st.markdown("---")
    
    # Visualizations
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Expense Breakdown")
        expenses = filtered_df[filtered_df['Withdrawals'] > 0]
        if not expenses.empty:
            fig_pie = px.pie(expenses, values='Withdrawals', names='Remarks', hole=0.4)
            fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.write("No expenses recorded for this period.")

    with c2:
        st.subheader("Cash Flow Waterfall")
        # Simplified waterfall: Opening (0), Deposits, Withdrawals, Closing
        fig_waterfall = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "relative", "total"],
            x=["Opening", "Deposits", "Expenses", "Closing"],
            y=[0, tot_dep, -tot_wth, net_cf],
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))
        fig_waterfall.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_waterfall, use_container_width=True)
