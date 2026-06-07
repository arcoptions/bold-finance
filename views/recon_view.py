import streamlit as st
from core.database import fetch_table, push_to_table, remove_duplicates
from core.reconciliation import clean_bank_statement, apply_smart_matching

def render_recon_view():
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
