import streamlit as st
import pandas as pd
import uuid
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

from core.ui import inject_custom_css, render_header
from core.database import push_to_table, fetch_table, update_expense_status, remove_duplicates
from core.constants import EMPLOYEES
from core.reconciliation import clean_bank_statement, apply_smart_matching

# 1. Page Configuration
st.set_page_config(page_title="B&I Financial ERP", layout="wide", initial_sidebar_state="collapsed")
inject_custom_css()
render_header()

# 2. Main Horizontal Navigation
tab_log, tab_recon, tab_dash = st.tabs(["Log Expense", "Reconciliation", "Dashboard"])

# ==========================================
# MODULE 1: LOG EXPENSE
# ==========================================
with tab_log:
    # Since we can't nest tabs, we use a radio button to toggle views in this section
    mode = st.radio("Action", ["Log New Expense", "Settle Reimbursements"], horizontal=True, label_visibility="collapsed")
    
    if mode == "Log New Expense":
        st.markdown("<br>", unsafe_allow_html=True)
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
                    st.success("Expense logged successfully!")

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

    elif mode == "Settle Reimbursements":
        st.markdown("<br>", unsafe_allow_html=True)
        col_title, col_btn = st.columns([4, 1])
        col_title.subheader("Link Reimbursements to Bank Transactions")
        if col_btn.button("Refresh Data", type="secondary"):
            st.rerun()
            
        expenses_df = fetch_table("Expense_Log")
        
        if not expenses_df.empty and 'Status' in expenses_df.columns:
            pending_mask = expenses_df['Status'] == 'Pending'
            if pending_mask.any():
                pending_df = expenses_df[pending_mask].copy()
                
                # --- NEW FEATURE: Filter & Total ---
                c_filt, c_metric = st.columns([2, 1])
                selected_emp = c_filt.selectbox("Filter by Employee (Paid By)", ["All"] + EMPLOYEES)
                
                if selected_emp != "All":
                    pending_df = pending_df[pending_df['Person'] == selected_emp]
                
                # Calculate total unsettled for the filtered view
                pending_df['Amount'] = pd.to_numeric(pending_df['Amount'], errors='coerce').fillna(0)
                total_unsettled = pending_df['Amount'].sum()
                c_metric.metric(f"Total Unsettled ({selected_emp})", f"₹ {total_unsettled:,.2f}")
                
                if pending_df.empty:
                    st.info(f"No pending expenses for {selected_emp}.")
                else:
                    # --- NEW FEATURE: Select All ---
                    select_all = st.checkbox("Select All Filtered Expenses")
                    pending_df.insert(0, "Select", select_all)
                    
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

# ==========================================
# MODULE 2: RECONCILIATION
# ==========================================
with tab_recon:
    st.markdown("<br>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Bank Statement (.xls/.xlsx)", type=['xls', 'xlsx'])

    if uploaded_file:
        master_df = fetch_table("Transactions_Master")
        raw_df = clean_bank_statement(uploaded_file)
        
        if not master_df.empty and 'Cheque No/Reference No' in master_df.columns:
            existing_refs = master_df['Cheque No/Reference No'].astype(str).tolist()
            raw_df = raw_df[~raw_df['Cheque No/Reference No'].isin(existing_refs)]
            
        if raw_df.empty:
            st.warning("No new transactions found. All records in this file already exist in the Master Ledger.")
        else:
            st.info(f"Processing {len(raw_df)} new transactions.")
            processed_df = apply_smart_matching(raw_df, master_df)
            
            sub_tab1, sub_tab2 = st.tabs(["Needs Review", "Auto-Reconciled"])
            mask_review = processed_df['Match_Confidence'] == 'Needs Review'
            
            with sub_tab1:
                if mask_review.any():
                    st.markdown("Please categorize the following unrecognized transactions:")
                    review_df = processed_df[mask_review].copy()
                    edited_df = st.data_editor(
                        review_df[['Transaction Date', 'Description', 'Withdrawals', 'Deposits', 'Entity', 'Person', 'Remarks']],
                        column_config={"Entity": st.column_config.SelectboxColumn("Entity", options=["Socialight", "Bold and Italic", "Ignore/Personal"])},
                        use_container_width=True,
                        disabled=["Transaction Date", "Description", "Withdrawals", "Deposits"]
                    )
                    processed_df.loc[mask_review, ['Entity', 'Person', 'Remarks']] = edited_df[['Entity', 'Person', 'Remarks']]
                else:
                    st.success("No manual review required.")
                    
            with sub_tab2:
                st.dataframe(processed_df[~mask_review], use_container_width=True)

            st.markdown("---")
            if st.button("Commit to Master Ledger", type="primary"):
                final_df = processed_df.drop(columns=['Match_Confidence'])
                with st.spinner("Checking for duplicates and merging..."):
                    clean_final_df = remove_duplicates(final_df, "Transactions_Master")
                    if not clean_final_df.empty:
                        push_to_table(clean_final_df, "Transactions_Master")
                        st.success(f"Successfully merged {len(clean_final_df)} new transactions to the Master Ledger.")
                    else:
                        st.warning("Merge blocked: Data already exists in the Master Ledger.")

# ==========================================
# MODULE 3: DASHBOARD
# ==========================================
with tab_dash:
    st.markdown("<br>", unsafe_allow_html=True)
    df = fetch_table("Transactions_Master")

    if df.empty:
        st.info("The Master Ledger is empty. Process a statement to view analytics.")
    else:
        df['Deposits'] = pd.to_numeric(df['Deposits'], errors='coerce').fillna(0)
        df['Withdrawals'] = pd.to_numeric(df['Withdrawals'], errors='coerce').fillna(0)
        df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
        
        col1, col2 = st.columns(2)
        with col1:
            entity_filter = st.selectbox("Entity View", ["All", "Socialight", "Bold and Italic"])
        with col2:
            df['Month'] = df['Transaction Date'].dt.to_period('M').astype(str)
            month_filter = st.selectbox("Period", ["All Time"] + list(df['Month'].unique()))

        filtered_df = df.copy()
        if entity_filter != "All":
            filtered_df = filtered_df[filtered_df['Entity'] == entity_filter]
        if month_filter != "All Time":
            filtered_df = filtered_df[filtered_df['Month'] == month_filter]

        tot_dep = filtered_df['Deposits'].sum()
        tot_wth = filtered_df['Withdrawals'].sum()
        net_cf = tot_dep - tot_wth

        m1, m2, m3 = st.columns(3)
        m1.metric("Revenue (Deposits)", f"INR {tot_dep:,.2f}")
        m2.metric("Expenses (Withdrawals)", f"INR {tot_wth:,.2f}")
        m3.metric("Net Cash Flow", f"INR {net_cf:,.2f}")

        st.markdown("---")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Expense Breakdown")
            expenses = filtered_df[filtered_df['Withdrawals'] > 0]
            if not expenses.empty:
                fig_pie = px.pie(expenses, values='Withdrawals', names='Remarks', hole=0.4)
                fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.write("No expenses recorded for this period.")

        with c2:
            st.subheader("Cash Flow Waterfall")
            fig_waterfall = go.Figure(go.Waterfall(
                orientation="v",
                measure=["absolute", "relative", "relative", "total"],
                x=["Opening", "Deposits", "Expenses", "Closing"],
                y=[0, tot_dep, -tot_wth, net_cf],
                connector={"line": {"color": "rgb(63, 63, 63)"}}
            ))
            fig_waterfall.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_waterfall, use_container_width=True)
