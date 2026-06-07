import streamlit as st
import pandas as pd
import uuid
from datetime import date
from core.ui import setup_page
from core.database import push_to_table, fetch_table
from core.constants import EMPLOYEES

# 1. Setup the page config and logo
setup_page("Log Expense")

# 2. Main Page UI
st.title("Log Expense")
st.markdown("Record proactive context for transactions to assist with end-of-month reconciliation.")

# 3. The Expense Logging Form
with st.form("expense_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    exp_date = col1.date_input("Date incurred", date.today())
    person = col2.selectbox("Paid By", EMPLOYEES)
    
    entity = col1.selectbox("Entity", ["Socialight", "Bold and Italic"])
    amount = col2.number_input("Amount (INR)", min_value=0.0, step=100.0)
    
    desc = st.text_input("Transaction Description (Context)")
    
    submit_button = st.form_submit_button("Save Expense Log", type="primary", use_container_width=True)
    
    if submit_button:
        if not desc:
            st.error("Please provide a description.")
        else:
            new_record = pd.DataFrame([{
                "Expense_ID": str(uuid.uuid4())[:8],
                "Date": str(exp_date),
                "Entity": entity,
                "Person": person,
                "Amount": amount,
                "Description": desc,
                "Status": "Pending",
                "Bank_Reference": ""
            }])
            with st.spinner("Saving..."):
                push_to_table(new_record, "Expense_Log")
            st.toast("Expense logged successfully!")

st.markdown("---")
st.subheader("Recent Pending Expenses")

# 4. View recent expenses immediately below the form
recent_df = fetch_table("Expense_Log")
if not recent_df.empty and 'Status' in recent_df.columns:
    pending_df = recent_df[recent_df['Status'] == 'Pending']
    if not pending_df.empty:
        st.dataframe(pending_df.sort_values(by="Date", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("No pending expenses found.")
else:
    st.info("Log your first expense to see the history here.")
