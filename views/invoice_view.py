import streamlit as st
import pandas as pd
from datetime import date
from core.invoice_generator import generate_invoice_pdf

def render_invoice_view():
    st.markdown("## 🧾 Generate Invoice")
    # Initialize session state for PDF data
    if 'pdf_data' not in st.session_state:
        st.session_state.pdf_data = None
        st.session_state.inv_no = ""
    with st.form("invoice_form"):
        # Top Config
        col1, col2, col3 = st.columns(3)
        inv_type = col1.selectbox("Invoice Type", ["Proforma Invoice", "Tax Invoice"])
        inv_no = col2.text_input("Invoice Number", "PI-26-27-001")
        order_date = col3.date_input("Order Date", date.today())

        # Client Details
        st.markdown("#### Client Details")
        c1, c2, c3 = st.columns(3)
        client_name = c1.text_input("Client Name", "Acme Corp")
        place_of_supply = c2.selectbox("Place of Supply", ["Telangana", "Maharashtra", "Karnataka", "Delhi", "Others..."])
        client_gst = c3.text_input("Client GSTIN (Optional)", "")
        client_address = st.text_area("Client Address")

        # Line Items
        st.markdown("#### Line Items")
        st.info("Edit the table below to add your services/products.")
        
        # Default empty rows for the UI data editor
        default_items = pd.DataFrame([
            {"Description": "Digital Marketing Retainer", "HSN/SAC": "998311", "Qty": 1, "Rate": 50000.0},
            {"Description": "", "HSN/SAC": "", "Qty": 0, "Rate": 0.0}
        ])
        
        edited_items = st.data_editor(default_items, num_rows="dynamic", use_container_width=True)

        submitted = st.form_submit_button("Generate PDF Invoice", type="primary")

        if submitted:
            # Clean empty rows from the data editor
            valid_items = []
            for _, row in edited_items.iterrows():
                if str(row['Description']).strip() and row['Qty'] > 0:
                    valid_items.append({
                        "desc": str(row['Description']),
                        "hsn": str(row['HSN/SAC']),
                        "qty": int(row['Qty']),
                        "rate": float(row['Rate'])
                    })
                    
            if not valid_items:
                st.error("Please add at least one valid item with a quantity greater than 0.")
                return

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

            # Generate PDF
            pdf_buffer, grand_total = generate_invoice_pdf(invoice_data)
            
            st.success(f"Invoice generated successfully! Grand Total: ₹ {grand_total:,.2f}")
            
        # Download Button
        st.download_button(
            label=f"⬇️ Download {inv_no}.pdf",
            data=pdf_buffer,
            file_name=f"{inv_no}.pdf",
            mime="application/pdf"
            )
