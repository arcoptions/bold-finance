import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

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

def fetch_table(tab_name):
    worksheet = get_worksheet("Stoic_Social_ERP", tab_name)
    try:
        data = worksheet.get_all_records()
        if data:
            return pd.DataFrame(data)
    except Exception:
        pass
    return pd.DataFrame()

def push_to_table(df, tab_name):
    worksheet = get_worksheet("Stoic_Social_ERP", tab_name)
    first_row = worksheet.row_values(1)
    
    if not first_row or all(cell == "" for cell in first_row):
        worksheet.update('A1', [list(df.columns)])
    
    data_to_upload = df.fillna("").astype(str).values.tolist()
    worksheet.append_rows(data_to_upload)
    return True

def remove_duplicates(new_df, tab_name):
    """Prevents duplicate transactions from syncing to the Master Ledger."""
    master_df = fetch_table(tab_name)
    if master_df.empty:
        return new_df
        
    # Create a composite key to identify unique transactions (Date + Description + Amount)
    def make_key(df):
        return df['Transaction Date'].astype(str) + "|" + df['Description'].astype(str).str.strip().str.upper() + "|" + df['Withdrawals'].astype(str)
        
    new_df['dup_key'] = make_key(new_df)
    master_df['dup_key'] = make_key(master_df)
    
    # Filter out rows that already exist in the master sheet
    clean_df = new_df[~new_df['dup_key'].isin(master_df['dup_key'])].drop(columns=['dup_key'])
    return clean_df
    
def update_expense_status(expense_ids, bank_reference):
    worksheet = get_worksheet("Stoic_Social_ERP", "Expense_Log")
    records = worksheet.get_all_records()
    for idx, row in enumerate(records):
        if str(row.get('Expense_ID')) in expense_ids:
            row_num = idx + 2 
            worksheet.update_cell(row_num, 7, "Settled")       
            worksheet.update_cell(row_num, 8, bank_reference)  
    return True
