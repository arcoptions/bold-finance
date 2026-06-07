import streamlit as st
import pandas as pd
from core.database import fetch_table, push_to_table, remove_duplicates
from core.reconciliation import clean_bank_statement, apply_smart_matching

def render_recon_view():
    st.markdown("<br>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Bank Statement (.xls/.xlsx/.csv)", type=['xls', 'xlsx', 'csv'])

    if uploaded_file:
        # Validate File Extension
        if not uploaded_file.name.endswith(('.xls', '.xlsx', '.csv')):
            st.error("Unsupported file type. Please upload a .xls, .xlsx, or .csv file.")
            return
        master_df = fetch_table("Transactions_Master")
        raw_df = clean_bank_statement(uploaded_file)
        
        if raw_df.empty:
            st.error("No valid transactions found. Make sure this is a standard bank account statement.")
            return

        # --- UPLOAD SUMMARY (Verification Layer) ---
        st.markdown("### 📄 Upload Summary (Raw Data)")
        tot_dep = raw_df['Deposits'].sum()
        tot_wth = raw_df['Withdrawals'].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Found in File", f"{len(raw_df)}")
        m2.metric("Total Deposits (Cr)", f"₹ {tot_dep:,.2f}")
        m3.metric("Total Withdrawals (Dr)", f"₹ {tot_wth:,.2f}")
        st.markdown("---")

        # 1. Deduplication (Ref No. Check)
        if not master_df.empty and 'Cheque No/Reference No' in master_df.columns and 'Cheque No/Reference No' in raw_df.columns:
            existing_refs = master_df['Cheque No/Reference No'].astype(str).tolist()
            # Ignore empty/nan references to prevent accidental mass deletion
            valid_refs = [ref for ref in existing_refs if ref.strip() and ref.lower() not in ('nan', 'none')]
            new_df = raw_df[~raw_df['Cheque No/Reference No'].astype(str).isin(valid_refs)].copy()
        else:
            new_df = raw_df.copy()
            
        if new_df.empty:
            st.success("🎉 All transactions in this file already exist in the Master Ledger.")
            st.info("You can view the raw extracted data in the 'All Uploaded Data' tab.")
        else:
            st.info(f"Processing {len(new_df)} new genuine transactions...")
        
        # 2. Apply Smart Matching
        processed_df = apply_smart_matching(new_df, master_df)
        
        # 3. Clean UI Data Types (Fixes the "unsupported data type" warning)
        processed_df = processed_df.astype(str)
        processed_df['Withdrawals'] = pd.to_numeric(processed_df['Withdrawals'], errors='coerce').fillna(0)
        processed_df['Deposits'] = pd.to_numeric(processed_df['Deposits'], errors='coerce').fillna(0)

        # 4. UI Display 
        tab1, tab2, tab3 = st.tabs(["Needs Review ⚠️", "Auto-Reconciled ✅", "All Uploaded Data 📋"])
        mask_review = processed_df['Match_Confidence'] == 'Needs Review'
        
        edit_cols = ['Transaction Date', 'Description', 'Withdrawals', 'Deposits', 'Cheque No/Reference No', 'Entity', 'Person', 'Remarks']
        disabled_cols = ['Transaction Date', 'Description', 'Withdrawals', 'Deposits', 'Cheque No/Reference No']
        
        with tab1:
            review_df = processed_df[mask_review]
            if not review_df.empty:
                st.markdown(f"**Please categorize these {len(review_df)} unmapped transactions:**")
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
                st.markdown(f"**{len(auto_df)} transactions matched historical records. Edit them below if needed:**")
                edited_auto = st.data_editor(
                    auto_df[edit_cols],
                    use_container_width=True,
                    disabled=disabled_cols,
                    key="editor_auto"
                )
                processed_df.loc[~mask_review, ['Entity', 'Person', 'Remarks']] = edited_auto[['Entity', 'Person', 'Remarks']]
            else:
                st.info("No transactions were auto-reconciled.")

        with tab3:
            st.markdown("**Raw Extracted Transactions (Before deduplication & matching):**")
            # Convert raw_df to string to prevent Streamlit rendering errors
            st.dataframe(raw_df.astype(str), use_container_width=True, hide_index=True)

        st.markdown("---")
        
        # 5. Commit to Database
        if st.button("Commit to Master Ledger", type="primary"):
            final_df = processed_df.drop(columns=['Match_Confidence'])
            
            with st.spinner("Checking for final duplicates and merging..."):
                clean_final_df = remove_duplicates(final_df, "Transactions_Master")
                
                if not clean_final_df.empty:
                    push_success = push_to_table(clean_final_df, "Transactions_Master")
                    if push_success:
                        st.success(f"✅ Successfully merged {len(clean_final_df)} new transactions to the Master Ledger.")
                    else:
                        st.error("Failed to sync with Google Sheets. Please try again.")
                else:
                    st.warning("Merge Blocked: These specific transactions are already in the Master Ledger.")
