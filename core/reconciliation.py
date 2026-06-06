import pandas as pd
import re

def process_bank_statement(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name='Account Statement')
    df = df.dropna(subset=['Description'])
    
    # Ensure mandatory audit columns exist for manual review later
    required_columns = ['Entity', 'Person', 'Remarks', 'Splitwise match']
    for col in required_columns:
        if col not in df.columns:
            df[col] = None
            
    return df

def apply_mapping_rules(df, rules):
    rules_df = pd.DataFrame(rules)
    
    for idx, row in df.iterrows():
        desc = str(row.get('Description', '')).upper()
        
        if pd.notna(row.get('Entity')) and str(row.get('Entity')).strip() != '':
            continue

        for _, rule in rules_df.iterrows():
            if pd.notna(rule['keyword']) and re.search(rule['keyword'], desc):
                df.at[idx, 'Entity'] = rule['entity']
                df.at[idx, 'Person'] = rule['person']
                df.at[idx, 'Remarks'] = rule['remarks']
                df.at[idx, 'Splitwise match'] = rule['match']
                break 
                
    return df
