import streamlit as st

st.set_page_config(page_title="Stoic Financial ERP", layout="wide")

# This fulfills Requirement 1: Logo placement
# Replace "logo.png" with the actual path to your logo asset in the repository
try:
    st.sidebar.image("logo.png", use_container_width=True)
except Exception:
    st.sidebar.markdown("### Stoic Social")

st.sidebar.title("Navigation")
st.sidebar.markdown("Select a module above.")

st.title("Stoic Financial ERP")
st.markdown("""
Welcome to the Financial Management Tool.

**System Modules:**
* **1. Reconciliation:** Upload monthly statements, review uncategorized items, and merge with the master ledger.
* **2. Dashboard:** Audit historical data, filter by month, and view total deposits/withdrawals.
* **3. Expense Log:** Proactively record context for upcoming expenses (Replacing WhatsApp logging).
""")
