def fetch_from_ledger(sheet_name="Stoic_Social_ERP", tab_name="Transactions_Master"):
    """Fetches data from Google Sheets and returns a Pandas DataFrame."""
    worksheet = get_worksheet(sheet_name, tab_name)
    
    # get_all_records() automatically uses row 1 as headers
    data = worksheet.get_all_records()
    
    if data:
        df = pd.DataFrame(data)
        
        # Ensure financial columns are numeric for calculations
        for col in ['Deposits', 'Withdrawals']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        # Ensure date column is datetime
        if 'Transaction Date' in df.columns:
            df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], errors='coerce')
            
        return df
    else:
        return pd.DataFrame()
