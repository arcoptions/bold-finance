import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time

@st.cache_resource
def get_sheets_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scopes)
    return gspread.authorize(creds)

def get_worksheet(sheet_name, tab_name):
    client = get_sheets_client()
    sheet = client.open(sheet_name)
    try:
        return sheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        return sheet.add_worksheet(title=tab_name, rows="1000", cols="20")

@st.cache_data(ttl=300)
def fetch_table(tab_name):
    # Always return a DataFrame, even on failure
    result_df = pd.DataFrame() 
    
    for attempt in range(3):
        try:
            worksheet = get_worksheet("Stoic_Social_ERP", tab_name)
            data = worksheet.get_all_values()
            if not data:
                return pd.DataFrame()
            
            # Find the header row
            header_idx = 0
            for i, row in enumerate(data):
                if len([c for c in row if str(c).strip()]) >= 3:
                    header_idx = i
                    break
            
            # Build DataFrame
            df = pd.DataFrame(data[header_idx+1:], columns=data[header_idx])
            df = df.loc[:, ~df.columns.duplicated()] # Drop duplicate columns
            result_df = df.replace("", pd.NA).dropna(how='all')
            break # Success!
        except Exception:
            time.sleep(2 ** attempt)
            
    return result_df
def push_to_table(df, tab_name):
    worksheet = get_worksheet("Stoic_Social_ERP", tab_name)
    data_to_upload = df.fillna("").astype(str).values.tolist()
    worksheet.append_rows(data_to_upload)
    st.cache_data.clear() 
    return True

def remove_duplicates(new_df, tab_name):
    master_df = fetch_table(tab_name)
    if master_df.empty:
        return new_df
        
    def make_key(df):
        # Dynamically find the right columns just in case headers shift
        date_col = 'Transaction Date' if 'Transaction Date' in df.columns else df.columns[0]
        desc_col = 'Description' if 'Description' in df.columns else df.columns[1]
        amt_col = 'Withdrawals' if 'Withdrawals' in df.columns else df.columns[2]
        return df[date_col].astype(str) + "|" + df[desc_col].astype(str).str.strip().str.upper() + "|" + df[amt_col].astype(str)
        
    new_df['dup_key'] = make_key(new_df)
    master_df['dup_key'] = make_key(master_df)
    
    clean_df = new_df[~new_df['dup_key'].isin(master_df['dup_key'])].drop(columns=['dup_key'])
    return clean_df
    
def update_expense_status(expense_ids, bank_reference):
    worksheet = get_worksheet("Stoic_Social_ERP", "Expense_Log")
    data = worksheet.get_all_values()
    if not data: return False
    
    headers = data[0]
    try:
        id_col_idx = headers.index("Expense_ID")
        status_col_idx = headers.index("Status") + 1
        ref_col_idx = headers.index("Bank_Reference") + 1
    except ValueError:
        id_col_idx = 0
        status_col_idx = 7
        ref_col_idx = 8
    
    cells_to_update = []
    for idx, row in enumerate(data):
        if idx == 0: continue
        if len(row) > id_col_idx and str(row[id_col_idx]) in expense_ids:
            row_num = idx + 1 
            cells_to_update.append(gspread.Cell(row=row_num, col=status_col_idx, value="Settled"))
            cells_to_update.append(gspread.Cell(row=row_num, col=ref_col_idx, value=bank_reference))
            
    if cells_to_update:
        worksheet.update_cells(cells_to_update)
    st.cache_data.clear()
    return True
