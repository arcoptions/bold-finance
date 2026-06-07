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

@st.cache_data(ttl=300)
def fetch_table(tab_name):
    """Brute-force fetch: Ensures every row is read and columns are unique."""
    for attempt in range(3):
        try:
            client = get_sheets_client()
            sheet = client.open("Stoic_Social_ERP")
            worksheet = sheet.worksheet(tab_name)
            data = worksheet.get_all_values()
            
            if not data or len(data) < 2: return pd.DataFrame()
            
            # Find the true header row
            header_idx = 0
            for i, row in enumerate(data):
                if len([c for c in row if str(c).strip()]) >= 3:
                    header_idx = i
                    break
            
            # Extract and force unique headers
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
            
            # Clean duplicate columns and empty rows
            df = df.loc[:, ~df.columns.duplicated()]
            return df.replace("", pd.NA).dropna(how='all')
            
        except Exception:
            time.sleep(2)
            
    return pd.DataFrame()

def push_to_table(df, tab_name):
    try:
        client = get_sheets_client()
        sheet = client.open("Stoic_Social_ERP")
        worksheet = sheet.worksheet(tab_name)
        worksheet.append_rows(df.fillna("").astype(str).values.tolist())
        st.cache_data.clear()
        return True
    except Exception:
        return False
