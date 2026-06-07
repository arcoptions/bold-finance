import pandas as pd

def clean_bank_statement(uploaded_file):
    # 1. Define the exact columns your bank provides
    expected_cols = [
        'Transaction Date', 'Value Date', 'Cheque No/Reference No', 
        'Description', 'Withdrawals', 'Deposits', 'Running Balance'
    ]
    
    # 2. Read the file, ignoring all 'Unnamed' or extra columns
    df = pd.read_excel(uploaded_file, sheet_name='Account Statement')
    
    # Clean up column names to avoid trailing spaces (a common bank export bug)
    df.columns = df.columns.str.strip()
    
    # Keep only the columns we expect
    df = df[[c for c in expected_cols if c in df.columns]]
    
    # 3. CRITICAL: Remove non-transaction rows (The bank footers/disclaimers)
    # This keeps only rows where 'Description' is not null
    df = df.dropna(subset=['Description'])
    
    # Remove rows where the description contains footer keywords
    footer_keywords = ['Generated On', 'YES BANK', 'Disclaimer', 'Transaction codes']
    for kw in footer_keywords:
        df = df[~df['Description'].astype(str).str.contains(kw, na=False)]
        
    # 4. Standardize Reference Number (the fix for Cheque/Ref)
    if 'Cheque No/Reference No' in df.columns:
        df['Cheque No/Reference No'] = df['Cheque No/Reference No'].astype(str).str.strip()

    # Ensure required reconciliation columns exist
    for col in ['Entity', 'Person', 'Remarks', 'Splitwise match']:
        if col not in df.columns:
            df[col] = None
            
    return df

def apply_smart_matching(new_df, historical_df):
    new_df['Match_Confidence'] = 'Needs Review'
    
    default_rules = {
        "RAZORPAY": ("Bold and Italic", "Customer", "Razorpay deposits"),
        "TRIPURA BIO": ("Socialight", "Tripura Bio", "Client payment"),
        "VUESOL": ("Socialight", "Vuesol", "Client payment"),
        "FACEBOOK": ("Bold and Italic", "Vendor", "FB Ads")
    }

    historical_dict = {}
    if not historical_df.empty:
        valid_history = historical_df.dropna(subset=['Entity', 'Description'])
        for _, row in valid_history.iterrows():
            historical_dict[str(row['Description']).upper().strip()] = (
                row['Entity'], row['Person'], row['Remarks']
            )

    for idx, row in new_df.iterrows():
        desc = str(row['Description']).upper().strip()
        
        if desc in historical_dict:
            new_df.at[idx, 'Entity'] = historical_dict[desc][0]
            new_df.at[idx, 'Person'] = historical_dict[desc][1]
            new_df.at[idx, 'Remarks'] = historical_dict[desc][2]
            new_df.at[idx, 'Match_Confidence'] = 'Auto-Reconciled'
            continue
            
        matched = False
        for key, value in default_rules.items():
            if key in desc:
                new_df.at[idx, 'Entity'] = value[0]
                new_df.at[idx, 'Person'] = value[1]
                new_df.at[idx, 'Remarks'] = value[2]
                new_df.at[idx, 'Match_Confidence'] = 'Auto-Reconciled'
                matched = True
                break
                
    return new_df
