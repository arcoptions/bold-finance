import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.database import fetch_table

def render_dashboard_view():
    # --- HEADER & MANUAL SYNC BUTTON ---
    col_title, col_btn = st.columns([4, 1])
    with col_btn:
        if st.button("Sync Live Data", use_container_width=True):
            st.cache_data.clear() 
            st.rerun()            

    df = fetch_table("Transactions_Master")

    if df.empty:
        st.info("The Master Ledger is empty. Process a statement to view analytics.")
        return

    # --- DYNAMIC COLUMN MAPPING ---
    def get_col(candidates):
        for col in df.columns:
            if any(c.lower() in col.lower() for c in candidates): return col
        return None

    dep_col = get_col(['Deposits', 'Credit'])
    wth_col = get_col(['Withdrawals', 'Debit'])
    bal_col = get_col(['Running Balance', 'Balance'])
    date_col = get_col(['Transaction Date', 'Date'])
    ent_col = get_col(['Entity'])
    rmk_col = get_col(['Remarks'])
    per_col = get_col(['Person'])

    # --- DATA CLEANING (Hardened) ---
    for col in [dep_col, wth_col, bal_col]:
        if col:
            df[col] = df[col].astype(str).str.replace(r'[^\d\.-]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    
    if date_col:
        df['Parsed_Date'] = pd.to_datetime(df[date_col], errors='coerce')
        df['Month'] = df['Parsed_Date'].dt.to_period('M').astype(str)

    # --- FILTERS ---
    c1, c2 = st.columns(2)
    entity_val = c1.selectbox("Entity View", ["All"] + list(df[ent_col].dropna().unique()) if ent_col else ["All"])
    month_val = c2.selectbox("Period", ["All Time"] + sorted([m for m in df['Month'].dropna().unique()], reverse=True))

    filtered_df = df.copy()
    if entity_val != "All" and ent_col:
        filtered_df = filtered_df[filtered_df[ent_col] == entity_val]
    if month_val != "All Time":
        filtered_df = filtered_df[filtered_df['Month'] == month_val]

    # --- METRICS ---
    tot_dep = float(filtered_df[dep_col].sum()) if dep_col else 0.0
    tot_wth = float(filtered_df[wth_col].sum()) if wth_col else 0.0
    
    closing_bal = 0.0
    opening_bal = 0.0
    if bal_col and not filtered_df.empty:
        sorted_df = filtered_df.sort_values('Parsed_Date')
        closing_bal = float(sorted_df.iloc[-1][bal_col])
        # Opening balance = Current Running Bal - Current Deposits + Current Withdrawals
        opening_bal = float(sorted_df.iloc[0][bal_col] - sorted_df.iloc[0][dep_col] + sorted_df.iloc[0][wth_col])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Revenue", f"₹{tot_dep:,.0f}")
    m2.metric("Expenses", f"₹{tot_wth:,.0f}")
    m3.metric("Net Flow", f"₹{(tot_dep - tot_wth):,.0f}")
    m4.metric("Closing Bal", f"₹{closing_bal:,.0f}")

    # --- CHARTS ---
    st.markdown("---")
    
    # ROW 1: Waterfall & Trend
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Cash Flow Waterfall")
        fig_waterfall = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "relative", "total"],
            x=["Opening", "Revenue", "Expenses", "Closing"],
            y=[opening_bal, tot_dep, -tot_wth, closing_bal],
            connector={"line": {"color": "rgb(63, 63, 63)"}}
        ))
        fig_waterfall.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig_waterfall, use_container_width=True)

    with col_b:
        st.subheader("Monthly Revenue vs. Expenses")
        if not filtered_df.empty and 'Month' in filtered_df.columns:
            monthly = filtered_df.groupby('Month')[[dep_col, wth_col]].sum().reset_index().sort_values('Month')
            fig = go.Figure()
            fig.add_trace(go.Bar(x=monthly['Month'], y=monthly[dep_col], name="Revenue", marker_color="#10B981"))
            fig.add_trace(go.Bar(x=monthly['Month'], y=monthly[wth_col], name="Expenses", marker_color="#EF4444"))
            fig.update_layout(barmode='group', margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

    # ROW 2: Distributions
    col_c, col_d = st.columns(2)
    expenses_df = filtered_df[filtered_df[wth_col] > 0]
    
    with col_c:
        st.subheader("Expense Distribution")
        if not expenses_df.empty and rmk_col:
            exp_data = expenses_df.groupby(rmk_col)[wth_col].sum().reset_index()
            fig_pie = px.pie(exp_data, values=wth_col, names=rmk_col, hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_layout(showlegend=False, margin=dict(t=10, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)

    with col_d:
        st.subheader("Top Payees")
        if not expenses_df.empty and per_col:
            top = expenses_df.groupby(per_col)[wth_col].sum().reset_index().sort_values(wth_col, ascending=True).tail(5)
            fig_bar = px.bar(top, x=wth_col, y=per_col, orientation='h', color_discrete_sequence=['#3B82F6'])
            fig_bar.update_layout(margin=dict(t=10, b=10))
            st.plotly_chart(fig_bar, use_container_width=True)
