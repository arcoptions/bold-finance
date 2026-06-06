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
    data = worksheet.get_all_records()
    if data:
        return pd.DataFrame(data)
    return pd.DataFrame()

def push_to_table(df, tab_name):
    worksheet = get_worksheet("Stoic_Social_ERP", tab_name)
    existing_data = worksheet.get_all_values()
    if not existing_data:
        worksheet.append_row(list(df.columns))
    
    data_to_upload = df.fillna("").astype(str).values.tolist()
    worksheet.append_rows(data_to_upload)
    return True

def update_expense_status(expense_ids, bank_reference):
    worksheet = get_worksheet("Stoic_Social_ERP", "Expense_Log")
    records = worksheet.get_all_records()
    
    # Identify rows to update (adding 2 to account for 0-index and header row)
    for idx, row in enumerate(records):
        if str(row.get('Expense_ID')) in expense_ids:
            row_num = idx + 2 
            worksheet.update_cell(row_num, 6, "Settled") # Assuming Status is col 6
            worksheet.update_cell(row_num, 7, bank_reference) # Assuming Bank_Ref is col 7
    return True
