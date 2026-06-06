import pandas as pd

def clean_bank_statement(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name='Account Statement')
    
    # 1. Drop junk headers where essential transaction data is missing
    df = df.dropna(subset=['Description'])
    
    # 2. Drop rows where both deposits and withdrawals are NaN/Empty
    df = df.dropna(subset=['Withdrawals', 'Deposits'], how='all')
    
    # Ensure required columns
    for col in ['Entity', 'Person', 'Remarks', 'Splitwise match']:
        if col not in df.columns:
            df[col] = None
            
    # Cast reference number to string for deduplication
    df['Cheque No/Reference No'] = df['Cheque No/Reference No'].astype(str).str.strip()
    return df

def apply_smart_matching(new_df, historical_df):
    new_df['Match_Confidence'] = 'Needs Review'
    
    # Fallback default keywords
    default_rules = {
        "RAZORPAY": ("Bold and Italic", "Customer", "Razorpay deposits"),
        "TRIPURA BIO": ("Socialight", "Tripura Bio", "Client payment"),
        "VUESOL": ("Socialight", "Vuesol", "Client payment"),
        "FACEBOOK": ("Bold and Italic", "Vendor", "FB Ads")
    }

    # Build historical dictionary from past master ledger for exact matches
    historical_dict = {}
    if not historical_df.empty:
        valid_history = historical_df.dropna(subset=['Entity', 'Description'])
        for _, row in valid_history.iterrows():
            historical_dict[str(row['Description']).upper().strip()] = (
                row['Entity'], row['Person'], row['Remarks']
            )

    for idx, row in new_df.iterrows():
        desc = str(row['Description']).upper().strip()
        
        # 1. Check Exact Historical Match
        if desc in historical_dict:
            new_df.at[idx, 'Entity'] = historical_dict[desc][0]
            new_df.at[idx, 'Person'] = historical_dict[desc][1]
            new_df.at[idx, 'Remarks'] = historical_dict[desc][2]
            new_df.at[idx, 'Match_Confidence'] = 'Auto-Reconciled'
            continue
            
        # 2. Check Substring Default Rules
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
