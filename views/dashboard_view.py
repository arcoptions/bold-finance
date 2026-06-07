import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from core.database import fetch_table

def render_dashboard_view():
    # --- SYNC BUTTON ---
    if st.button("🔄 Sync Live Data"):
        st.cache_data.clear()
        st.rerun()

    df = fetch_table("Transactions_Master")

    if df.empty:
        st.info("No data found in Master Ledger.")
        return

    # --- DYNAMIC MAPPING ---
    def get_col(candidates):
        for col in df.columns:
            if any(c.lower() in col.lower() for c in candidates): return col
        return None

    dep_col = get_col(['Deposits', 'Credit'])
    wth_col = get_col(['Withdrawals', 'Debit'])
    bal_col = get_col(['Running Balance', 'Balance'])
    date_col = get_col(['Transaction Date', 'Date'])

    # --- DATA CLEANING (THE FIX) ---
    # Strip symbols/commas and cast to float
    for col in [dep_col, wth_col, bal_col]:
        if col:
            df[col] = df[col].astype(str).str.replace(r'[^\d\.-]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    
    if date_col:
        df['Date_Obj'] = pd.to_datetime(df[date_col], errors='coerce')
        df['Month'] = df['Date_Obj'].dt.to_period('M').astype(str)

    # --- FILTERS ---
    col1, col2 = st.columns(2)
    entity_val = col1.selectbox("Entity", ["All"] + list(df['Entity'].unique()) if 'Entity' in df.columns else ["All"])
    month_val = col2.selectbox("Period", ["All Time"] + sorted(list(df['Month'].unique()), reverse=True))

    filtered_df = df.copy()
    if entity_val != "All" and 'Entity' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Entity'] == entity_val]
    if month_val != "All Time":
        filtered_df = filtered_df[filtered_df['Month'] == month_val]

    # --- METRICS ---
    tot_dep = filtered_df[dep_col].sum() if dep_col else 0
    tot_wth = filtered_df[wth_col].sum() if wth_col else 0
    
    # Closing Bal: Get from the very last date in the sheet
    closing_bal = 0.0
    if bal_col and not filtered_df.empty:
        closing_bal = filtered_df.sort_values('Date_Obj').iloc[-1][bal_col]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Revenue", f"₹{tot_dep:,.0f}")
    m2.metric("Expenses", f"₹{tot_wth:,.0f}")
    m3.metric("Net Flow", f"₹{(tot_dep - tot_wth):,.0f}")
    m4.metric("Bank Balance", f"₹{closing_bal:,.0f}")

    # --- TREND CHART ---
    st.markdown("---")
    st.subheader("Monthly Revenue vs. Expenses")
    
    monthly = filtered_df.groupby('Month')[[dep_col, wth_col]].sum().reset_index().sort_values('Month')
    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly['Month'], y=monthly[dep_col], name="Revenue", marker_color="#10B981"))
    fig.add_trace(go.Bar(x=monthly['Month'], y=monthly[wth_col], name="Expenses", marker_color="#EF4444"))
    fig.update_layout(barmode='group', height=400, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
