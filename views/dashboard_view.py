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
            st.cache_data.clear() 
            st.rerun()            

    df = fetch_table("Transactions_Master")

    if df.empty:
        st.info("The Master Ledger is empty. Process a statement to view analytics.")
        return

    # --- DYNAMIC COLUMN MAPPING ---
    def get_col(possible_names):
        for name in possible_names:
            for col in df.columns:
                if name.lower() == col.lower().strip():
                    return col
        return None

# Strict mappings based on common Google Sheet variations
    dep_col = get_col(['Deposits', 'Credit'])
    wth_col = get_col(['Withdrawals', 'Debit'])
    date_col = get_col(['Transaction Date', 'Date'])
    bal_col = get_col(['Running Balance', 'Balance'])
    ent_col = get_col(['Entity'])
    rmk_col = get_col(['Remarks'])
    per_col = get_col(['Person'])

    # --- DATA CLEANING ---
    # Only process columns if they were successfully found
    for col in [dep_col, wth_col, bal_col]:
        if col:
            df[col] = df[col].astype(str).str.replace(r'[^\d\.-]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    
    if date_col:
        df['Parsed_Date'] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=['Parsed_Date'])
        df['Month'] = df['Parsed_Date'].dt.to_period('M').astype(str)
    
    # --- METRICS ---
    # Only calculate if columns exist
    tot_dep = float(df[dep_col].sum()) if dep_col else 0.0
    tot_wth = float(df[wth_col].sum()) if wth_col else 0.0
    net_cf = tot_dep - tot_wth

    # Display safely
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Revenue", f"₹ {tot_dep:,.0f}")
    m2.metric("Total Expenses", f"₹ {tot_wth:,.0f}")
    m3.metric("Net Cash Flow", f"₹ {net_cf:,.0f}")
    
    # Closing Balance
    if bal_col:
        m4.metric("Closing Balance", f"₹ {float(df.iloc[-1][bal_col]):,.0f}")
    
    st.markdown("---")

    # --- RENDER METRICS ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Revenue", f"₹ {tot_dep:,.0f}")
    m2.metric("Total Expenses", f"₹ {tot_wth:,.0f}")
    m3.metric("Net Cash Flow", f"₹ {net_cf:,.0f}")
    m4.metric("Closing Bank Balance", f"₹ {closing_bal:,.0f}" if closing_bal else "N/A")

    st.markdown("---")

    # --- ROW 1: TREND ANALYSIS ---
    st.subheader("Monthly Revenue vs. Expense Trend")
    if not filtered_df.empty and month_filter == "All Time":
        # Only plot actual months, ignore the 'Unknown Date' bucket
        monthly_agg = filtered_df[filtered_df['Month'] != 'Unknown Date'].groupby('Month')[[dep_col, wth_col]].sum().reset_index()
        monthly_agg = monthly_agg.sort_values('Month')
        
        if not monthly_agg.empty:
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Bar(
                x=monthly_agg['Month'], y=monthly_agg[dep_col],
                name='Revenue (Deposits)', marker_color='#10B981'
            ))
            fig_trend.add_trace(go.Bar(
                x=monthly_agg['Month'], y=monthly_agg[wth_col],
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
        else:
            st.info("No valid monthly data to plot.")
    elif month_filter != "All Time":
        st.info("Trend analysis is only visible in 'All Time' view.")

    st.markdown("---")

    # --- ROW 2: CATEGORY & VENDOR DRILL-DOWN ---
    c1, c2 = st.columns(2)
    expenses_df = filtered_df[filtered_df[wth_col] > 0]

    with c1:
        st.subheader("Expense Distribution")
        if not expenses_df.empty and rmk_col:
            exp_by_remark = expenses_df.groupby(rmk_col)[wth_col].sum().reset_index()
            fig_pie = px.pie(
                exp_by_remark, values=wth_col, names=rmk_col, hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expenses recorded for this period.")

    with c2:
        st.subheader("Top Payees / Vendors")
        if not expenses_df.empty and per_col:
            top_vendors = expenses_df.groupby(per_col)[wth_col].sum().reset_index().sort_values(wth_col, ascending=True).tail(5)
            top_vendors = top_vendors[top_vendors[per_col] != 'Unknown']
            
            if not top_vendors.empty:
                fig_bar = px.bar(
                    top_vendors, x=wth_col, y=per_col, orientation='h',
                    color_discrete_sequence=['#3B82F6']
                )
                fig_bar.update_layout(margin=dict(t=10, b=10, l=10, r=10), xaxis_title="Amount Spent (₹)", yaxis_title="")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No mapped vendor data available to display.")
        else:
            st.info("No vendor data available.")
