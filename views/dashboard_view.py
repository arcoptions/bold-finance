import streamlit as st
import pandas as pd
import plotly.express as px
from core.database import fetch_table

def render_dashboard_view():
    st.markdown("<br>", unsafe_allow_html=True)
    df = fetch_table("Transactions_Master")

    if df.empty:
        st.info("The Master Ledger is empty. Process a statement to view analytics.")
        return

    # --- CRITICAL DATA CLEANING ---
    # 1. Remove commas and spaces from strings before converting to numbers
    for col in ['Deposits', 'Withdrawals', 'Running Balance']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '', regex=False).str.strip(), errors='coerce').fillna(0)
    
    # 2. Parse Dates safely
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
    df = df.dropna(subset=['Transaction Date'])
    df['Month'] = df['Transaction Date'].dt.to_period('M').astype(str)
    
    # Fill empty categories so they don't break the charts
    df['Remarks'] = df['Remarks'].replace('', 'Uncategorized')
    df['Person'] = df['Person'].replace('', 'Unknown')

    # --- TOP FILTERS ---
    col1, col2 = st.columns(2)
    with col1:
        entity_filter = st.selectbox("Entity View", ["All", "Socialight", "Bold and Italic"])
    with col2:
        months = sorted(list(df['Month'].unique()), reverse=True)
        month_filter = st.selectbox("Period", ["All Time"] + months)

    # Apply Filters to Working Data
    filtered_df = df.copy()
    if entity_filter != "All":
        filtered_df = filtered_df[filtered_df['Entity'] == entity_filter]
    if month_filter != "All Time":
        filtered_df = filtered_df[filtered_df['Month'] == month_filter]

    # --- METRICS CALCULATION ---
    tot_dep = filtered_df['Deposits'].sum()
    tot_wth = filtered_df['Withdrawals'].sum()
    net_cf = tot_dep - tot_wth

    # --- TRUE CLOSING BALANCE LOGIC ---
    # Closing balance relies on the timeline, not the Entity filter.
    time_filtered_df = df.copy()
    if month_filter != "All Time":
        time_filtered_df = time_filtered_df[time_filtered_df['Month'] == month_filter]
        
    if not time_filtered_df.empty and 'Running Balance' in time_filtered_df.columns:
        # Sort by date and original index to keep same-day transactions in exact bank order
        sorted_time_df = time_filtered_df.reset_index().sort_values(['Transaction Date', 'index'])
        closing_bal = sorted_time_df.iloc[-1]['Running Balance']
    else:
        closing_bal = 0

    # --- RENDER METRICS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Revenue", f"₹ {tot_dep:,.0f}")
    m2.metric("Total Expenses", f"₹ {tot_wth:,.0f}")
    m3.metric("Net Cash Flow", f"₹ {net_cf:,.0f}")
    m4.metric("Closing Bank Balance", f"₹ {closing_bal:,.0f}" if closing_bal else "N/A")

    st.markdown("---")

    # --- CHARTS ---
    c1, c2 = st.columns(2)
    expenses_df = filtered_df[filtered_df['Withdrawals'] > 0]

    with c1:
        st.subheader("Expense Distribution")
        if not expenses_df.empty:
            exp_by_remark = expenses_df.groupby('Remarks')['Withdrawals'].sum().reset_index()
            fig_pie = px.pie(
                exp_by_remark, values='Withdrawals', names='Remarks', hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expenses recorded for this period.")

    with c2:
        st.subheader("Top Payees / Vendors")
        if not expenses_df.empty:
            # Get top 5 payees by amount
            top_vendors = expenses_df.groupby('Person')['Withdrawals'].sum().reset_index().sort_values('Withdrawals', ascending=True).tail(5)
            # Remove the 'Unknown' generic tag from visualization if it dominates
            top_vendors = top_vendors[top_vendors['Person'] != 'Unknown']
            
            fig_bar = px.bar(
                top_vendors, x='Withdrawals', y='Person', orientation='h',
                color_discrete_sequence=['#3B82F6']
            )
            fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title="Amount Spent (₹)", yaxis_title="")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No vendor data available.")
