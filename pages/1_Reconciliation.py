import streamlit as st
import pandas as pd
from core.reconciliation import process_bank_statement, apply_mapping_rules
from core.constants import DEFAULT_MAPPING_RULES
from core.database import push_to_ledger

st.set_page_config(page_title="Reconciliation", layout="wide")
st.title("Bank Statement Reconciliation")

uploaded_file = st.file_uploader("Upload Bank Statement (.xls or .xlsx)", type=['xls', 'xlsx'])

if uploaded_file:
    with st.spinner("Processing document..."):
        raw_df = process_bank_statement(uploaded_file)
        mapped_df = apply_mapping_rules(raw_df, DEFAULT_MAPPING_RULES)
        
    unmapped_mask = mapped_df['Entity'].isna() | (mapped_df['Entity'] == '')
    
    st.subheader("Manual Review Required")
    if unmapped_mask.any():
        st.info("Assign the missing Entity and Person details below. This must be completed before merging.")
        unmapped_df = mapped_df[unmapped_mask].copy()
        
        edited_unmapped = st.data_editor(
            unmapped_df[['Transaction Date', 'Description', 'Withdrawals', 'Deposits', 'Entity', 'Person', 'Remarks']],
            column_config={
                "Entity": st.column_config.SelectboxColumn("Entity", options=["Socialight", "Bold and Italic", "Ignore/Personal"]),
                "Person": st.column_config.TextColumn("Person/Client"),
            },
            disabled=["Transaction Date", "Description", "Withdrawals", "Deposits"],
            use_container_width=True,
            key="manual_override"
        )
        
        mapped_df.loc[unmapped_mask, ['Entity', 'Person', 'Remarks']] = edited_unmapped[['Entity', 'Person', 'Remarks']]
    else:
        st.success("All transactions were successfully recognized by the system.")

    st.markdown("---")
    
    if st.button("Commit and Merge to Master Ledger", type="primary"):
        try:
            with st.spinner("Synchronizing with database..."):
                mapped_df['Transaction Date'] = mapped_df['Transaction Date'].astype(str)
                if 'Value Date' in mapped_df.columns:
                    mapped_df['Value Date'] = mapped_df['Value Date'].astype(str)
                    
                push_to_ledger(mapped_df)
            st.success("Ledger merged successfully.")
        except Exception as e:
            st.error(f"Failed to synchronize with database: {e}")
