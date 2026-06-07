import streamlit as st
from core.ui import inject_custom_css, render_header
from views.expense_view import render_expense_view
from views.recon_view import render_recon_view
from views.dashboard_view import render_dashboard_view
from views.invoice_view import render_invoice_view # Import the new view

# 1. Page Configuration
st.set_page_config(page_title="B&I Financial ERP", layout="wide", initial_sidebar_state="collapsed")
inject_custom_css()
render_header()

# 2. Main Horizontal Navigation
# Added 'Invoice' tab here
tab_log, tab_recon, tab_dash, tab_invoice = st.tabs(["Log Expense", "Reconciliation", "Dashboard", "Invoices"])

# 3. Route to Views
with tab_log:
    render_expense_view()

with tab_recon:
    render_recon_view()

with tab_dash:
    render_dashboard_view()

with tab_invoice:
    render_invoice_view() # Route to the new function
