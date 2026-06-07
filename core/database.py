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

# --- FIX 1: CACHING & EXPONENTIAL BACKOFF ---
# Caches the data for 5 minutes. Streamlit will not ping Google again until this expires or is cleared.
@st.cache_data(ttl=300)
def fetch_table(tab_name):
    # Retry logic: If Google drops the connection, wait and try again invisibly
    for attempt in range(3):
        try:
            worksheet = get_worksheet("Stoic_Social_ERP", tab_name)
            data = worksheet.get_all_records()
            if data:
                return pd.DataFrame(data)
            return pd.DataFrame()
        except gspread.exceptions.APIError:
            if attempt == 2:
                st.error("Google Sheets API is currently busy. Displaying cached or empty data.")
                return pd.DataFrame()
            time.sleep(2 ** attempt) # Waits 1s, then 2s, then fails gracefully
    return pd.DataFrame()

def push_to_table(df, tab_name):
    worksheet = get_worksheet("Stoic_Social_ERP", tab_name)
    first_row = worksheet.row_values(1)
    
    if not first_row or all(cell == "" for cell in first_row):
        worksheet.update('A1', [list(df.columns)])
    
    data_to_upload = df.fillna("").astype(str).values.tolist()
    worksheet.append_rows(data_to_upload)
    
    # Clear the cache so the dashboard immediately shows the new data
    st.cache_data.clear() 
    return True

def remove_duplicates(new_df, tab_name):
    master_df = fetch_table(tab_name)
    if master_df.empty:
        return new_df
        
    def make_key(df):
        return df['Transaction Date'].astype(str) + "|" + df['Description'].astype(str).str.strip().str.upper() + "|" + df['Withdrawals'].astype(str)
        
    new_df['dup_key'] = make_key(new_df)
    master_df['dup_key'] = make_key(master_df)
    
    clean_df = new_df[~new_df['dup_key'].isin(master_df['dup_key'])].drop(columns=['dup_key'])
    return clean_df
    
def update_expense_status(expense_ids, bank_reference):
    worksheet = get_worksheet("Stoic_Social_ERP", "Expense_Log")
    records = worksheet.get_all_records()
    
    # --- FIX 2: BATCH CELL UPDATING ---
    cells_to_update = []
    for idx, row in enumerate(records):
        if str(row.get('Expense_ID')) in expense_ids:
            row_num = idx + 2 
            # We bundle the updates into memory instead of hitting the API one by one
            cells_to_update.append(gspread.Cell(row=row_num, col=7, value="Settled"))
            cells_to_update.append(gspread.Cell(row=row_num, col=8, value=bank_reference))
            
    if cells_to_update:
        # Pushes all changes in ONE single API call
        worksheet.update_cells(cells_to_update)
        
    # Clear the cache so the pending expenses disappear from the UI immediately
    st.cache_data.clear()
    return True
