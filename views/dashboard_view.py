import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.database import fetch_table

def render_dashboard_view():
    st.markdown("<br>", unsafe_allow_html=True)
    df = fetch_table("Transactions_Master")

    if df.empty:
        st.info("The Master Ledger is empty. Process a statement to view analytics.")
        return

    # --- BULLETPROOF DATA CLEANING ---
    # 1. Force convert financial columns to strings, strip commas and spaces, then force to float.
    for col in ['Deposits', 'Withdrawals', 'Running Balance']:
        if col in df.columns:
            # Handle pandas float/string mix perfectly
            df[col] = df[col].astype(str).str.replace(',', '', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    
    # 2. Parse Dates safely and drop rows with bad dates
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
    df = df.dropna(subset=['Transaction Date'])
    df['Month'] = df['Transaction Date'].dt.to_period('M').astype(str)
    
    # Fill empty categories so they don't break the charts
    if 'Remarks' in df.columns:
        df['Remarks'] = df['Remarks'].replace('', 'Uncategorized').fillna('Uncategorized')
    if 'Person' in df.columns:
        df['Person'] = df['Person'].replace('', 'Unknown').fillna('Unknown')

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
    tot_dep = float(filtered_df['Deposits'].sum())
    tot_wth = float(filtered_df['Withdrawals'].sum())
    net_cf = tot_dep - tot_wth

    # --- TRUE CLOSING BALANCE LOGIC ---
    time_filtered_df = df.copy()
    if month_filter != "All Time":
        time_filtered_df = time_filtered_df[time_filtered_df['Month'] == month_filter]
        
    if not time_filtered_df.empty and 'Running Balance' in time_filtered_df.columns:
        sorted_time_df = time_filtered_df.reset_index().sort_values(['Transaction Date', 'index'])
        closing_bal = float(sorted_time_df.iloc[-1]['Running Balance'])
    else:
        closing_bal = 0.0

    # --- RENDER METRICS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Revenue", f"₹ {tot_dep:,.0f}")
    m2.metric("Total Expenses", f"₹ {tot_wth:,.0f}")
    m3.metric("Net Cash Flow", f"₹ {net_cf:,.0f}")
    m4.metric("Closing Bank Balance", f"₹ {closing_bal:,.0f}" if closing_bal else "N/A")

    st.markdown("---")

    # --- ROW 1: TREND ANALYSIS (RESTORED) ---
    st.subheader("Monthly Revenue vs. Expense Trend")
    if not filtered_df.empty:
        # Group by month
        monthly_agg = filtered_df.groupby('Month')[['Deposits', 'Withdrawals']].sum().reset_index()
        monthly_agg = monthly_agg.sort_values('Month')
        
        # Build a robust Grouped Bar Chart using Graph Objects instead of Express
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=monthly_agg['Month'], y=monthly_agg['Deposits'],
            name='Revenue (Deposits)', marker_color='#10B981'
        ))
        fig_trend.add_trace(go.Bar(
            x=monthly_agg['Month'], y=monthly_agg['Withdrawals'],
            name='Expenses (Withdrawals)', marker_color='#EF4444'
        ))
        
        fig_trend.update_layout(
            barmode='group',
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_title="", 
            yaxis_title="Amount (₹)"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")

    # --- ROW 2: CATEGORY & VENDOR DRILL-DOWN ---
    c1, c2 = st.columns(2)
    expenses_df = filtered_df[filtered_df['Withdrawals'] > 0]

    with c1:
        st.subheader("Expense Distribution")
        if not expenses_df.empty and 'Remarks' in expenses_df.columns:
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
        if not expenses_df.empty and 'Person' in expenses_df.columns:
            # Get top 5 payees by amount
            top_vendors = expenses_df.groupby('Person')['Withdrawals'].sum().reset_index().sort_values('Withdrawals', ascending=True).tail(5)
            # Remove the 'Unknown' generic tag from visualization if it dominates
            top_vendors = top_vendors[top_vendors['Person'] != 'Unknown']
            
            if not top_vendors.empty:
                fig_bar = px.bar(
                    top_vendors, x='Withdrawals', y='Person', orientation='h',
                    color_discrete_sequence=['#3B82F6']
                )
                fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title="Amount Spent (₹)", yaxis_title="")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No mapped vendor data available to display.")
        else:
            st.info("No vendor data available.")
