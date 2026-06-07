import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.database import fetch_table

def render_dashboard_view():
    # --- HEADER & MANUAL SYNC BUTTON ---
    col_title, col_btn = st.columns([4, 1])
    with col_title:
        st.markdown("<br>", unsafe_allow_html=True)
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Sync Live Data", use_container_width=True):
            st.cache_data.clear() # Clears the Streamlit memory cache
            st.rerun()            # Refreshes the page immediately

    df = fetch_table("Transactions_Master")

    if df.empty:
        st.info("The Master Ledger is empty. Process a statement to view analytics.")
        return

    # --- BULLETPROOF DATA CLEANING ---
    # 1. Force convert financial columns to strings, strip EVERYTHING except digits, decimals, and minus signs
    for col in ['Deposits', 'Withdrawals', 'Running Balance']:
        if col in df.columns:
            # The Regex r'[^\d\.-]' targets anything that is NOT a number, dot, or minus sign and deletes it.
            # This fixes ₹ symbols, $, commas, non-breaking spaces, and random letters.
            df[col] = df[col].astype(str).str.replace(r'[^\d\.-]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    
    # 2. Parse Dates Safely
    if 'Transaction Date' in df.columns:
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
    else:
        st.error("Missing 'Transaction Date' column in Master Ledger.")
        return
        
    # Fallback to 'Value Date' if 'Transaction Date' is accidentally empty in some rows
    if 'Value Date' in df.columns:
        df['Value Date'] = pd.to_datetime(df['Value Date'], errors='coerce')
        df['Transaction Date'] = df['Transaction Date'].fillna(df['Value Date'])

    # Drop rows where we absolutely cannot figure out the date (Junk headers)
    df = df.dropna(subset=['Transaction Date'])
    if df.empty:
        st.warning("No valid dates found in the ledger. Please check your Transaction Date formatting.")
        return
        
    df['Month'] = df['Transaction Date'].dt.to_period('M').astype(str)
    
    # Fill empty categories so Plotly doesn't crash
    if 'Remarks' in df.columns:
        df['Remarks'] = df['Remarks'].replace('', 'Uncategorized').fillna('Uncategorized')
    if 'Person' in df.columns:
        df['Person'] = df['Person'].replace('', 'Unknown').fillna('Unknown')

    # --- TOP FILTERS ---
    col1, col2 = st.columns(2)
    with col1:
        if 'Entity' in df.columns:
            entities = ["All"] + list(df['Entity'].dropna().unique())
        else:
            entities = ["All"]
        entity_filter = st.selectbox("Entity View", entities)
        
    with col2:
        months = sorted(list(df['Month'].unique()), reverse=True)
        month_filter = st.selectbox("Period", ["All Time"] + months)

    # Apply Filters to Working Data
    filtered_df = df.copy()
    if entity_filter != "All" and 'Entity' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Entity'] == entity_filter]
    if month_filter != "All Time":
        filtered_df = filtered_df[filtered_df['Month'] == month_filter]

    # --- METRICS CALCULATION ---
    tot_dep = float(filtered_df['Deposits'].sum()) if 'Deposits' in filtered_df.columns else 0.0
    tot_wth = float(filtered_df['Withdrawals'].sum()) if 'Withdrawals' in filtered_df.columns else 0.0
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

    # --- ROW 1: TREND ANALYSIS ---
    st.subheader("Monthly Revenue vs. Expense Trend")
    if not filtered_df.empty:
        monthly_agg = filtered_df.groupby('Month')[['Deposits', 'Withdrawals']].sum().reset_index()
        monthly_agg = monthly_agg.sort_values('Month')
        
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
            top_vendors = expenses_df.groupby('Person')['Withdrawals'].sum().reset_index().sort_values('Withdrawals', ascending=True).tail(5)
            # Filter out the generic "Unknown" bucket if it exists
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
