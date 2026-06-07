import pandas as pd
import numpy as np

def clean_bank_statement(uploaded_file):
    # 1. Safely read either CSV or Excel
    try:
        df_raw = pd.read_excel(uploaded_file, sheet_name=0, header=None)
    except Exception:
        uploaded_file.seek(0)
        df_raw = pd.read_csv(uploaded_file, header=None)
        
    # 2. Dynamically find the real header row (Bypass bank logos/address)
    header_idx = 0
    for i, row in df_raw.iterrows():
        row_str = " ".join(str(x).lower() for x in row.values)
        if ('description' in row_str or 'particulars' in row_str) and ('date' in row_str or 'txn' in row_str):
            header_idx = i
            break

    # Rebuild DataFrame
    df = pd.DataFrame(df_raw.values[header_idx+1:], columns=df_raw.iloc[header_idx])
    df.columns = df.columns.astype(str).str.strip()
    
    # Drop completely unnamed/empty garbage columns
    df = df.loc[:, ~df.columns.str.contains('^nan|^Unnamed', case=False, na=False)]

    # 3. DYNAMIC COLUMN MAPPING (This prevents KeyErrors and missing data)
    col_map = {}
    for col in df.columns:
        c_lower = col.lower()
        if 'date' in c_lower and 'value' not in c_lower:
            col_map[col] = 'Transaction Date'
        elif 'desc' in c_lower or 'narration' in c_lower or 'particulars' in c_lower:
            col_map[col] = 'Description'
        elif 'withdraw' in c_lower or 'debit' in c_lower:
            col_map[col] = 'Withdrawals'
        elif 'deposit' in c_lower or 'credit' in c_lower:
            col_map[col] = 'Deposits'
        elif 'ref' in c_lower or 'cheq' in c_lower:
            col_map[col] = 'Cheque No/Reference No'

    df = df.rename(columns=col_map)
    
    # Failsafe check
    if 'Description' not in df.columns:
        return pd.DataFrame()

    df = df.dropna(subset=['Description'])
    
    # 4. STRICT FINANCIAL FILTERING (Removes Footers/Disclaimers)
    # Strip commas and ₹ symbols, force to pure numbers
    df['Withdrawals'] = pd.to_numeric(df.get('Withdrawals', pd.Series(dtype=float)).astype(str).str.replace(r'[^\d\.]', '', regex=True), errors='coerce').fillna(0)
    df['Deposits'] = pd.to_numeric(df.get('Deposits', pd.Series(dtype=float)).astype(str).str.replace(r'[^\d\.]', '', regex=True), errors='coerce').fillna(0)
    
    # Only keep genuine monetary transactions
    df = df[(df['Withdrawals'] > 0) | (df['Deposits'] > 0)]
    
    if 'Cheque No/Reference No' in df.columns:
        df['Cheque No/Reference No'] = df['Cheque No/Reference No'].astype(str).str.strip()
    else:
        df['Cheque No/Reference No'] = ""

    # Add required application columns
    for col in ['Entity', 'Person', 'Remarks']:
        df[col] = None
            
    return df.reset_index(drop=True)

def apply_smart_matching(new_df, historical_df):
    new_df['Match_Confidence'] = 'Needs Review'
    
    # Build historical dictionary from the Master Ledger
    historical_dict = {}
    if not historical_df.empty and 'Description' in historical_df.columns:
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
        
        if desc in historical_dict:
            new_df.at[idx, 'Entity'] = historical_dict[desc]['Entity']
            new_df.at[idx, 'Person'] = historical_dict[desc]['Person']
            new_df.at[idx, 'Remarks'] = historical_dict[desc]['Remarks']
            new_df.at[idx, 'Match_Confidence'] = 'Auto-Reconciled'
            continue
            
    return new_df
