import streamlit as st
import gspread
import pandas as pd
import time
from oauth2client.service_account import ServiceAccountCredentials

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
    """Brute-force fetch that handles duplicate headers and formatting errors."""
    for attempt in range(3):
        try:
            worksheet = get_worksheet("Stoic_Social_ERP", tab_name)
            data = worksheet.get_all_values()
            if not data or len(data) < 2: return pd.DataFrame()
            
            # Find true header row
            header_idx = 0
            for i, row in enumerate(data):
                if len([c for c in row if str(c).strip()]) >= 3:
                    header_idx = i
                    break
            
            # Extract and unique-ify headers
            raw_headers = data[header_idx]
            clean_headers = []
            seen = {}
            for h in raw_headers:
                h = str(h).strip()
                if h in seen:
                    seen[h] += 1
                    clean_headers.append(f"{h}_{seen[h]}")
                else:
                    seen[h] = 0
                    clean_headers.append(h)
            
            df = pd.DataFrame(data[header_idx+1:], columns=clean_headers)
            df = df.loc[:, ~df.columns.duplicated()] # Drop duplicate columns
            return df.replace("", pd.NA).dropna(how='all')
        except Exception:
            time.sleep(2)
    return pd.DataFrame()

def push_to_table(df, tab_name):
    try:
        worksheet = get_worksheet("Stoic_Social_ERP", tab_name)
        worksheet.append_rows(df.fillna("").astype(str).values.tolist())
        st.cache_data.clear()
        return True
    except Exception:
        return False

def remove_duplicates(new_df, tab_name):
    master_df = fetch_table(tab_name)
    if master_df.empty: return new_df
    
    def make_key(df):
        # Dynamically map keys based on available columns
        date_c = [c for c in df.columns if 'date' in c.lower()][0]
        desc_c = [c for c in df.columns if 'desc' in c.lower()][0]
        amt_c = [c for c in df.columns if 'withdraw' in c.lower()][0]
        return df[date_c].astype(str) + "|" + df[desc_c].astype(str).str.strip().str.upper() + "|" + df[amt_c].astype(str)
        
    new_df['dup_key'] = make_key(new_df)
    master_df['dup_key'] = make_key(master_df)
    return new_df[~new_df['dup_key'].isin(master_df['dup_key'])].drop(columns=['dup_key'])

def update_expense_status(expense_ids, bank_reference):
    """Marks expenses as Settled and links the Bank Reference."""
    worksheet = get_worksheet("Stoic_Social_ERP", "Expense_Log")
    data = worksheet.get_all_values()
    if not data: return False
    
    headers = data[0]
    id_idx = headers.index("Expense_ID")
    status_idx = headers.index("Status") + 1
    ref_idx = headers.index("Bank_Reference") + 1
    
    cells_to_update = []
    for idx, row in enumerate(data):
        if idx == 0: continue
        # Row index in gspread is 1-based, index 0 is header
        if str(row[id_idx]) in expense_ids:
            cells_to_update.append(gspread.Cell(row=idx + 1, col=status_idx, value="Settled"))
            cells_to_update.append(gspread.Cell(row=idx + 1, col=ref_idx, value=bank_reference))
            
    if cells_to_update:
        worksheet.update_cells(cells_to_update)
        st.cache_data.clear()
        return True
    return False
