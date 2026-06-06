import streamlit as st
from core.database import log_proactive_expense
from datetime import date

st.set_page_config(page_title="Proactive Expense Log", layout="centered")
st.title("Log an Expense Context")
st.markdown("Provide context for transactions immediately as they occur to assist with end-of-month reconciliation.")

with st.form("expense_log_form"):
    expense_date = st.date_input("Date of Transaction", date.today())
    entity = st.selectbox("Entity", ["Socialight", "Bold and Italic"])
    person = st.text_input("Person or Vendor Name")
    amount = st.number_input("Amount", min_value=0.0, step=1.0)
    context = st.text_area("Transaction Description (e.g., context previously sent via messaging apps)")
    
    submitted = st.form_submit_button("Submit Context Log")
    
    if submitted:
        data = {
            "Date": str(expense_date),
            "Entity": entity,
            "Person": person,
            "Amount": str(amount),
            "Context": context,
            "Status": "Pending Reconciliation"
        }
        try:
            log_proactive_expense(data)
            st.success("Expense context logged successfully.")
        except Exception as e:
            st.error(f"Error logging context: {e}")
