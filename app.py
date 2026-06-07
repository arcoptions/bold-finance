import streamlit as st
from core.ui import inject_custom_css, render_header
from views.expense_view import render_expense_view
from views.recon_view import render_recon_view
from views.dashboard_view import render_dashboard_view

# 1. Page Configuration
st.set_page_config(page_title="B&I Financial ERP", layout="wide", initial_sidebar_state="collapsed")
inject_custom_css()
render_header()

# 2. Main Horizontal Navigation
tab_log, tab_recon, tab_dash = st.tabs(["Log Expense", "Reconciliation", "Dashboard"])

# 3. Route to Views
with tab_log:
    render_expense_view()

with tab_recon:
    render_recon_view()

with tab_dash:
    render_dashboard_view()
