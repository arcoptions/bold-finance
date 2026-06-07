import streamlit as st
import pandas as pd
import plotly.express as px
from core.database import fetch_table

def render_dashboard_view():
    df = fetch_table("Transactions_Master")

    if df.empty:
        st.info("The Master Ledger is empty. Process a statement to view analytics.")
        return

    # Data Cleaning & Formatting
    df['Deposits'] = pd.to_numeric(df['Deposits'], errors='coerce').fillna(0)
    df['Withdrawals'] = pd.to_numeric(df['Withdrawals'], errors='coerce').fillna(0)
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

    # Apply Filters
    filtered_df = df.copy()
    if entity_filter != "All":
        filtered_df = filtered_df[filtered_df['Entity'] == entity_filter]
    if month_filter != "All Time":
        filtered_df = filtered_df[filtered_df['Month'] == month_filter]

    # --- KPI METRICS ---
    tot_dep = filtered_df['Deposits'].sum()
    tot_wth = filtered_df['Withdrawals'].sum()
    net_cf = tot_dep - tot_wth

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Revenue", f"₹ {tot_dep:,.0f}")
    m2.metric("Total Expenses", f"₹ {tot_wth:,.0f}")
    m3.metric("Net Cash Flow", f"₹ {net_cf:,.0f}")
    
    # Show Closing Balance if available
    if not filtered_df.empty and 'Running Balance' in filtered_df.columns:
        # Get the running balance of the most recent transaction in the filter
        last_bal = pd.to_numeric(filtered_df.sort_values('Transaction Date').iloc[-1]['Running Balance'], errors='coerce')
        m4.metric("Closing Bank Balance", f"₹ {last_bal:,.0f}" if pd.notnull(last_bal) else "N/A")
    else:
        m4.metric("Total Transactions", f"{len(filtered_df)}")

    st.markdown("---")

    # --- ROW 1: TREND ANALYSIS ---
    st.subheader("Monthly Revenue vs. Expense Trend")
    if not filtered_df.empty:
        # Group data by month and sum deposits/withdrawals
        monthly_agg = filtered_df.groupby('Month')[['Deposits', 'Withdrawals']].sum().reset_index()
        # Restructure data for Plotly grouped bar chart
        melted = monthly_agg.melt(id_vars='Month', value_vars=['Deposits', 'Withdrawals'], var_name='Type', value_name='Amount')
        
        fig_trend = px.bar(
            melted, x='Month', y='Amount', color='Type', barmode='group',
            color_discrete_map={'Deposits': '#10B981', 'Withdrawals': '#EF4444'}
        )
        fig_trend.update_layout(margin=dict(t=10, b=10, l=10, r=10), legend_title=None, xaxis_title="", yaxis_title="Amount (₹)")
        st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")

    # --- ROW 2: CATEGORY & VENDOR DRILL-DOWN ---
    c1, c2 = st.columns(2)
    expenses_df = filtered_df[filtered_df['Withdrawals'] > 0]
    revenue_df = filtered_df[filtered_df['Deposits'] > 0]

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
