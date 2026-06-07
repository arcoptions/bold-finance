import streamlit as st
import pandas as pd
from datetime import date
from core.invoice_generator import generate_invoice_pdf

def render_invoice_view():
    st.markdown("## 🧾 Generate Invoice")
    
    # 1. Initialize session state variables safely
    if 'pdf_data' not in st.session_state:
        st.session_state.pdf_data = None
    if 'inv_no' not in st.session_state:
        st.session_state.inv_no = ""

    # 2. Form for inputs
    with st.form("invoice_form"):
        col1, col2, col3 = st.columns(3)
        inv_type = col1.selectbox("Invoice Type", ["Proforma Invoice", "Tax Invoice"])
        inv_no = col2.text_input("Invoice Number", "PI-26-27-001")
        order_date = col3.date_input("Order Date", date.today())
        
        c1, c2, c3 = st.columns(3)
        client_name = c1.text_input("Client Name", "Acme Corp")
        place_of_supply = c2.selectbox("Place of Supply", ["Telangana", "Maharashtra", "Karnataka", "Delhi", "Others..."])
        client_gst = c3.text_input("Client GSTIN", "")
        client_address = st.text_area("Client Address")

        st.markdown("#### Line Items")
        # Initialize with one empty row
        default_items = pd.DataFrame([{"Description": "", "HSN/SAC": "", "Qty": 0, "Rate": 0.0}])
        edited_items = st.data_editor(default_items, num_rows="dynamic", use_container_width=True)

        submitted = st.form_submit_button("Generate PDF Invoice", type="primary")

        if submitted:
            # Prepare line items
            valid_items = []
            for _, row in edited_items.iterrows():
                if str(row['Description']).strip() and row['Qty'] > 0:
                    valid_items.append({
                        "desc": str(row['Description']),
                        "hsn": str(row['HSN/SAC']),
                        "qty": int(row['Qty']),
                        "rate": float(row['Rate'])
                    })
            
            if valid_items:
                invoice_data = {
                    "invoice_type": inv_type, 
                    "invoice_no": inv_no, 
                    "order_date": order_date.strftime("%d-%b-%Y"),
                    "client_name": client_name, 
                    "client_address": client_address, 
                    "client_gst": client_gst,
                    "place_of_supply": place_of_supply, 
                    "items": valid_items
                }
                
                # Generate and store in Session State
                pdf_buffer, _ = generate_invoice_pdf(invoice_data)
                st.session_state.pdf_data = pdf_buffer
                st.session_state.inv_no = inv_no
            else:
                st.error("Please add at least one valid item with quantity > 0.")
                st.session_state.pdf_data = None 

    # 3. DOWNLOAD BUTTON (Placed OUTSIDE the form to avoid StreamlitAPIException)
    # This now reads from the session state, ensuring no UnboundLocalError occurs
    if st.session_state.pdf_data is not None:
        st.success("PDF Generated! Click below to download.")
        st.download_button(
            label=f"⬇️ Download {st.session_state.inv_no}.pdf",
            data=st.session_state.pdf_data,
            file_name=f"{st.session_state.inv_no}.pdf",
            mime="application/pdf"
        )
