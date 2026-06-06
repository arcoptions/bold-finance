import streamlit as st
import pandas as pd
import uuid
from datetime import date
from core.database import fetch_table, push_to_table, update_expense_status
from core.ui import inject_custom_css, render_sidebar_logo

st.set_page_config(page_title="Expense Log", layout="wide")
inject_custom_css()
render_sidebar_logo()

st.title("Expense Management & Linking")

tab1, tab2 = st.tabs(["Log New Expense", "Settle Reimbursements"])

with tab1:
    st.subheader("Log Proactive Expense")
    # clear_on_submit ensures the form resets after a successful log
    with st.form("expense_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        exp_date = col_a.date_input("Date incurred", date.today())
        person = col_b.text_input("Paid By (Employee/Team Member)")
        
        entity = col_a.selectbox("Entity", ["Socialight", "Bold and Italic"])
        amount = col_b.number_input("Amount (INR)", min_value=0.0, step=100.0)
        
        desc = st.text_input("Context / Vendor Details")
        
        if st.form_submit_button("Log Expense"):
            if not person or not desc:
                st.warning("Please fill out the 'Paid By' and 'Context' fields.")
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
                push_to_table(new_record, "Expense_Log")
                st.success("Expense logged to queue successfully!")

with tab2:
    col_title, col_btn = st.columns([4, 1])
    col_title.subheader("Link Reimbursements to Bank Transactions")
    
    # Adding a manual refresh button to ensure Google Sheets state is synced
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
                    st.rerun() # Automatically refresh UI to remove settled items from pending queue
        else:
            st.info("No pending expenses to settle at this time.")
    else:
        st.info("Expense log is empty.")
