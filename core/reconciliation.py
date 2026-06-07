import pandas as pd
import numpy as np

def clean_bank_statement(uploaded_file):
    # 1. Read raw without headers to dynamically find where the real data starts
    df_raw = pd.read_excel(uploaded_file, sheet_name=0, header=None)
    
    header_idx = 0
    # Search for the row that actually contains the word 'Description' and 'Date'
    for i, row in df_raw.iterrows():
        row_str = " ".join(str(x).lower() for x in row.values)
        if 'description' in row_str and 'date' in row_str:
            header_idx = i
            break

    # 2. Rebuild the DataFrame with the correct headers
    df = pd.DataFrame(df_raw.values[header_idx+1:], columns=df_raw.iloc[header_idx])
    df.columns = df.columns.astype(str).str.strip()
    
    # 3. Drop all empty or "Unnamed" garbage columns
    df = df.loc[:, ~df.columns.str.contains('^nan|^Unnamed', case=False, na=False)]
    
    if 'Description' not in df.columns:
        return pd.DataFrame() # Safety fallback

    df = df.dropna(subset=['Description'])
    
    # 4. CRITICAL: Remove all Bank Footers and Disclaimers
    # Genuine transactions must have a numeric value > 0 in either Deposits or Withdrawals
    # We force them to floats. Text disclaimers will become NaN/0 and be dropped.
    df['Withdrawals'] = pd.to_numeric(df.get('Withdrawals', pd.Series(dtype=float)).astype(str).str.replace(r'[^\d\.]', '', regex=True), errors='coerce').fillna(0)
    df['Deposits'] = pd.to_numeric(df.get('Deposits', pd.Series(dtype=float)).astype(str).str.replace(r'[^\d\.]', '', regex=True), errors='coerce').fillna(0)
    
    df = df[(df['Withdrawals'] > 0) | (df['Deposits'] > 0)]
    
    if 'Cheque No/Reference No' in df.columns:
        df['Cheque No/Reference No'] = df['Cheque No/Reference No'].astype(str).str.strip()

    # Ensure mapping columns exist
    for col in ['Entity', 'Person', 'Remarks']:
        if col not in df.columns:
            df[col] = None
            
    return df.reset_index(drop=True)

def apply_smart_matching(new_df, historical_df):
    new_df['Match_Confidence'] = 'Needs Review'
    
    # Build historical dictionary from the Master Ledger
    historical_dict = {}
    if not historical_df.empty and 'Description' in historical_df.columns:
        # We drop empty entities and keep the MOST RECENT mapping for a description
        hist_clean = historical_df.dropna(subset=['Description', 'Entity'])
        hist_clean = hist_clean[hist_clean['Entity'].astype(str).str.strip() != '']
        hist_clean = hist_clean.drop_duplicates(subset=['Description'], keep='last')
        
        for _, row in hist_clean.iterrows():
            historical_dict[str(row['Description']).strip().upper()] = {
                'Entity': row.get('Entity', ''),
                'Person': row.get('Person', ''),
                'Remarks': row.get('Remarks', '')
            }

    # Match current transactions against history
    for idx, row in new_df.iterrows():
        desc = str(row['Description']).strip().upper()
        
        # Exact 100% Historical Match
        if desc in historical_dict:
            new_df.at[idx, 'Entity'] = historical_dict[desc]['Entity']
            new_df.at[idx, 'Person'] = historical_dict[desc]['Person']
            new_df.at[idx, 'Remarks'] = historical_dict[desc]['Remarks']
            new_df.at[idx, 'Match_Confidence'] = 'Auto-Reconciled'
            continue
            
        # Hardcoded fallback rules (Optional, but helps catch basics if history is empty)
        if 'RAZORPAY' in desc:
            new_df.at[idx, 'Entity'] = 'Bold and Italic'
            new_df.at[idx, 'Remarks'] = 'Razorpay deposits'
            new_df.at[idx, 'Match_Confidence'] = 'Auto-Reconciled'
            
    return new_df
