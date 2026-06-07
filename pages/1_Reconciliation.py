import streamlit as st
import pandas as pd
from core.database import fetch_table, push_to_table
from core.reconciliation import clean_bank_statement, apply_smart_matching
from core.ui import inject_custom_css, render_sidebar_logo

st.set_page_config(page_title="Reconciliation", layout="wide")
inject_custom_css()
render_sidebar_logo()

st.title("Statement Reconciliation")

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
        
        tab1, tab2 = st.tabs(["Needs Review", "Auto-Reconciled"])
        
        mask_review = processed_df['Match_Confidence'] == 'Needs Review'
        
        with tab1:
            if mask_review.any():
                st.markdown("Please categorize the following unrecognized transactions:")
                review_df = processed_df[mask_review].copy()
                edited_df = st.data_editor(
                    review_df[['Transaction Date', 'Description', 'Withdrawals', 'Deposits', 'Entity', 'Person', 'Remarks']],
                    use_container_width=True,
                    disabled=["Transaction Date", "Description", "Withdrawals", "Deposits"]
                )
                processed_df.loc[mask_review, ['Entity', 'Person', 'Remarks']] = edited_df[['Entity', 'Person', 'Remarks']]
            else:
                st.success("No manual review required.")
                
        with tab2:
            st.dataframe(processed_df[~mask_review], use_container_width=True)

        st.markdown("---")
        if st.button("Commit to Master Ledger", type="primary"):
            final_df = processed_df.drop(columns=['Match_Confidence'])
            push_to_table(final_df, "Transactions_Master")
            st.success("Transactions successfully merged to Master Ledger.")
