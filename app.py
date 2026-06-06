import streamlit as st
from core.ui import inject_custom_css, render_sidebar_logo

st.set_page_config(page_title="Financial ERP", layout="wide")
inject_custom_css()
render_sidebar_logo()

st.title("Financial Operating System")
st.markdown("---")
st.markdown("""
Select a module from the sidebar to begin:

* **Dashboard:** View interactive Plotly charts, P&L, and cash flow.
* **Reconciliation:** Upload statements and smart-match transactions.
* **Expense Log:** Proactively record expenses and link them to bank reimbursements.
""")
