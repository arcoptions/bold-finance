import streamlit as st
import pandas as pd
import uuid
from datetime import date
from core.ui import inject_custom_css, render_sidebar_logo
from core.database import push_to_table, fetch_table, update_expense_status
from core.constants import EMPLOYEES

st.set_page_config(page_title="Expense Log", layout="wide")
inject_custom_css()
render_sidebar_logo()

st.title("Expense Management & Linking")
st.markdown("Record proactive context for transactions to assist with end-of-month reconciliation.")

tab1, tab2 = st.tabs(["Log New Expense", "Settle Reimbursements"])

with tab1:
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
    recent_df = fetch_table("Expense_Log")
    if not recent_df.empty and 'Status' in recent_df.columns:
        pending_df = recent_df[recent_df['Status'] == 'Pending']
        if not pending_df.empty:
            st.dataframe(pending_df.sort_values(by="Date", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No pending expenses found.")
    else:
        st.info("Log your first expense to see the history here.")

with tab2:
    col_title, col_btn = st.columns([4, 1])
    col_title.subheader("Link Reimbursements to Bank Transactions")
    
    if col_btn.button("Refresh Data", type="secondary"):
        st.rerun()
        
    expenses_df = fetch_table("Expense_Log")
    
    if not expenses_df.empty and 'Status' in expenses_df.columns:
        pending_mask = expenses_df['Status'] == 'Pending'
        if pending_mask.any():
            pending_df = expenses_df[pending_mask]
            
            st.markdown("Select expenses to settle:")
            pending_df.insert(0, "Select", False)
            
            selected_df = st.data_editor(
                pending_df, 
                hide_index=True, 
                disabled=["Expense_ID", "Date", "Entity", "Person", "Amount", "Description"],
                use_container_width=True
            )
            
            st.markdown("---")
            bank_ref = st.text_input("Enter Bank Reference Number from Master Ledger to link:")
            
            if st.button("Mark as Settled", type="primary"):
                selected_ids = selected_df[selected_df['Select'] == True]['Expense_ID'].astype(str).tolist()
                
                if not selected_ids:
                    st.warning("Please select at least one expense.")
                elif not bank_ref:
                    st.warning("Please provide a Bank Reference Number.")
                else:
                    with st.spinner("Updating database..."):
                        update_expense_status(selected_ids, bank_ref)
                    st.success(f"Linked {len(selected_ids)} expenses to reference {bank_ref}.")
                    st.rerun()
        else:
            st.info("No pending expenses to settle at this time.")
    else:
        st.info("Expense log is empty.")
