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
        # Failsafe if headers are missing or malformed
        pass
    return pd.DataFrame()

def push_to_table(df, tab_name):
    worksheet = get_worksheet("Stoic_Social_ERP", tab_name)
    existing_data = worksheet.get_all_values()
    
    # Check if the sheet is functionally empty (only contains blank cells)
    is_empty = True
    if existing_data:
        for row in existing_data:
            if any(str(cell).strip() for cell in row):
                is_empty = False
                break
                
    if is_empty:
        # Wipe hidden formatting and blank rows so it starts cleanly at A1
        worksheet.clear()
        worksheet.append_row(list(df.columns))
    
    data_to_upload = df.fillna("").astype(str).values.tolist()
    worksheet.append_rows(data_to_upload)
    return True

def update_expense_status(expense_ids, bank_reference):
    worksheet = get_worksheet("Stoic_Social_ERP", "Expense_Log")
    records = worksheet.get_all_records()
    
    for idx, row in enumerate(records):
        if str(row.get('Expense_ID')) in expense_ids:
            # idx + 2 accounts for 0-indexing and the header row
            row_num = idx + 2 
            worksheet.update_cell(row_num, 7, "Settled")       # Column G: Status
            worksheet.update_cell(row_num, 8, bank_reference)  # Column H: Bank_Reference
    return True
