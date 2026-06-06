import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

@st.cache_resource
def get_sheets_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
    client = gspread.authorize(creds)
    return client

def get_worksheet(sheet_name, tab_name):
    client = get_sheets_client()
    sheet = client.open(sheet_name)
    try:
        worksheet = sheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        # Auto-create the tab if it does not exist
        worksheet = sheet.add_worksheet(title=tab_name, rows="1000", cols="20")
    return worksheet
    
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
def push_to_ledger(df, sheet_name="Stoic_Social_ERP", tab_name="Transactions_Master"):
    worksheet = get_worksheet(sheet_name, tab_name)
    
    # Check if headers exist; if not, write them
    existing_data = worksheet.get_all_values()
    if not existing_data:
        worksheet.append_row(list(df.columns))
        
    data_to_upload = df.fillna("").astype(str).values.tolist()
    worksheet.append_rows(data_to_upload)
    return True
    
def log_proactive_expense(data_dict, sheet_name="Stoic_Social_ERP", tab_name="Expense_Log"):
    worksheet = get_worksheet(sheet_name, tab_name)
    existing_data = worksheet.get_all_values()
    
    if not existing_data:
        headers = list(data_dict.keys())
        worksheet.append_row(headers)
        
    worksheet.append_row(list(data_dict.values()))
    return True
