import streamlit as st
import pandas as pd
from core.database import fetch_table, push_to_table, remove_duplicates
from core.reconciliation import clean_bank_statement, apply_smart_matching

def render_recon_view():
    st.markdown("<br>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Bank Statement (.xls/.xlsx)", type=['xls', 'xlsx'])

    if uploaded_file:
        master_df = fetch_table("Transactions_Master")
        raw_df = clean_bank_statement(uploaded_file)
        
        if raw_df.empty:
            st.error("No valid transactions found. Make sure this is a standard YES Bank account statement.")
            return

        # 1. Deduplication (Ref No. Check)
        if not master_df.empty and 'Cheque No/Reference No' in master_df.columns and 'Cheque No/Reference No' in raw_df.columns:
            existing_refs = master_df['Cheque No/Reference No'].astype(str).tolist()
            # Ignore 'nan' or empty references during this fast-check
            valid_refs = [ref for ref in existing_refs if ref.strip() and ref.lower() != 'nan']
            raw_df = raw_df[~raw_df['Cheque No/Reference No'].astype(str).isin(valid_refs)]
            
        if raw_df.empty:
            st.success("🎉 All transactions in this file already exist in the Master Ledger.")
            return

        st.info(f"Processing {len(raw_df)} new genuine transactions...")
        
        # 2. Apply Smart Matching
        processed_df = apply_smart_matching(raw_df, master_df)
        
        # 3. Create Editable Tabs
        tab1, tab2 = st.tabs(["Needs Review ⚠️", "Auto-Reconciled ✅"])
        mask_review = processed_df['Match_Confidence'] == 'Needs Review'
        
        edit_cols = ['Transaction Date', 'Description', 'Withdrawals', 'Deposits', 'Entity', 'Person', 'Remarks']
        disabled_cols = ['Transaction Date', 'Description', 'Withdrawals', 'Deposits']
        
        with tab1:
            review_df = processed_df[mask_review]
            if not review_df.empty:
                st.markdown("**Please categorize these unmapped transactions:**")
                edited_review = st.data_editor(
                    review_df[edit_cols],
                    use_container_width=True,
                    disabled=disabled_cols,
                    key="editor_review"
                )
                processed_df.loc[mask_review, ['Entity', 'Person', 'Remarks']] = edited_review[['Entity', 'Person', 'Remarks']]
            else:
                st.success("No manual review required!")
                
        with tab2:
            auto_df = processed_df[~mask_review]
            if not auto_df.empty:
                st.markdown("**These matched historical records. Edit them below if needed:**")
                edited_auto = st.data_editor(
                    auto_df[edit_cols],
                    use_container_width=True,
                    disabled=disabled_cols,
                    key="editor_auto"
                )
                processed_df.loc[~mask_review, ['Entity', 'Person', 'Remarks']] = edited_auto[['Entity', 'Person', 'Remarks']]
            else:
                st.info("No transactions were auto-reconciled.")

        st.markdown("---")
        
        # 4. Commit to Database
        if st.button("Commit to Master Ledger", type="primary"):
            final_df = processed_df.drop(columns=['Match_Confidence'])
            
            with st.spinner("Checking for final duplicates and merging..."):
                clean_final_df = remove_duplicates(final_df, "Transactions_Master")
                
                if not clean_final_df.empty:
                    push_success = push_to_table(clean_final_df, "Transactions_Master")
                    if push_success:
                        st.success(f"✅ Successfully merged {len(clean_final_df)} new transactions to the Master Ledger.")
                    else:
                        st.error("Failed to sync with Google Sheets.")
                else:
                    st.warning("Merge Blocked: These specific transactions are already in the Master Ledger.")
