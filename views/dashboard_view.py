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

    dep_col = get_col(['Deposits', 'Deposit', 'Credit'])
    wth_col = get_col(['Withdrawals', 'Withdrawal', 'Debit'])
    date_col = get_col(['Transaction Date', 'Date', 'Value Date'])
    bal_col = get_col(['Running Balance', 'Balance', 'Running_Balance'])

    if not dep_col or not wth_col:
        st.error("Could not locate financial columns. Please check your Google Sheet headers.")
        st.write("Found columns:", list(df.columns))
        return

    # --- DATA CLEANING ---
    for col in [dep_col, wth_col, bal_col]:
        if col:
            # Aggressively extract only numbers to prevent string calculation crashes
            df[col] = df[col].astype(str).str.replace(r'[^\d\.-]', '', regex=True)
            df[col] = df[col].replace('', '0')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # Safely parse dates, capturing unreadable dates into 'Unknown Date' instead of dropping them
    if date_col:
        df['Parsed_Date'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        df['Month'] = df['Parsed_Date'].dt.to_period('M').astype(str)
        df['Month'] = df['Month'].replace('NaT', 'Unknown Date')
    else:
        df['Month'] = 'Unknown Date'

    rmk_col = get_col(['Remarks', 'Category'])
    per_col = get_col(['Person', 'Client', 'Vendor'])
    ent_col = get_col(['Entity', 'Company'])

    if rmk_col: df[rmk_col] = df[rmk_col].fillna('Uncategorized').replace('', 'Uncategorized')
    if per_col: df[per_col] = df[per_col].fillna('Unknown').replace('', 'Unknown')

    # --- TOP FILTERS ---
    col1, col2 = st.columns(2)
    with col1:
        if ent_col:
            entities = ["All"] + list(df[ent_col].dropna().unique())
        else:
            entities = ["All"]
        entity_filter = st.selectbox("Entity View", entities)
        
    with col2:
        months = sorted([m for m in df['Month'].unique() if m != 'Unknown Date'], reverse=True)
        if 'Unknown Date' in df['Month'].values:
            months.append('Unknown Date')
        month_filter = st.selectbox("Period", ["All Time"] + months)

    # Apply Filters
    filtered_df = df.copy()
    if entity_filter != "All" and ent_col:
        filtered_df = filtered_df[filtered_df[ent_col] == entity_filter]
    if month_filter != "All Time":
        filtered_df = filtered_df[filtered_df['Month'] == month_filter]

    # --- METRICS CALCULATION ---
    tot_dep = float(filtered_df[dep_col].sum())
    tot_wth = float(filtered_df[wth_col].sum())
    net_cf = tot_dep - tot_wth

    closing_bal = 0.0
    if bal_col and not filtered_df.empty:
        if 'Parsed_Date' in filtered_df.columns:
            sorted_df = filtered_df.sort_values(by=['Parsed_Date'])
            closing_bal = float(sorted_df.iloc[-1][bal_col])
        else:
            closing_bal = float(filtered_df.iloc[-1][bal_col])

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
