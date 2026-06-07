import streamlit as st
import pandas as pd
from datetime import date
from core.invoice_generator import generate_invoice_pdf

def render_invoice_view():
    st.markdown("## 🧾 Generate Invoice")
    
    # 1. Initialize session state
    if 'pdf_data' not in st.session_state:
        st.session_state.pdf_data = None
        st.session_state.inv_no = ""

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
        default_items = pd.DataFrame([{"Description": "", "HSN/SAC": "", "Qty": 0, "Rate": 0.0}])
        edited_items = st.data_editor(default_items, num_rows="dynamic", use_container_width=True)
        
        col_d1, col_d2 = st.columns(2)
        discount = col_d1.number_input("Discount (₹)", min_value=0.0, value=0.0)
        deduction = col_d2.number_input("Other Deductions (₹)", min_value=0.0, value=0.0)

        # --- PREVIEW CALCULATION ---
        # Force numeric conversion
        preview_df = edited_items.copy()
        preview_df['Qty'] = pd.to_numeric(preview_df['Qty'], errors='coerce').fillna(0)
        preview_df['Rate'] = pd.to_numeric(preview_df['Rate'], errors='coerce').fillna(0)
        
        # Calculate Subtotal
        subtotal = (preview_df['Qty'] * preview_df['Rate']).sum()
        
        # Calculate Net Taxable Amount
        net_taxable = subtotal - discount - deduction
        # Ensure it doesn't go below zero
        net_taxable = max(0.0, net_taxable)
        
        # Calculate Tax on the Net Amount
        tax_amount = net_taxable * 0.18
        grand_total = net_taxable + tax_amount
        
        st.markdown("---")
        st.markdown("#### 📊 Preview Totals")
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Subtotal", f"₹{subtotal:,.2f}")
        p2.metric("Adjustments", f"-₹{(discount+deduction):,.2f}")
        p3.metric("GST (18% on Net)", f"₹{tax_amount:,.2f}")
        p4.metric("Grand Total", f"₹{grand_total:,.2f}")

        submitted = st.form_submit_button("Generate PDF Invoice", type="primary")

        if submitted:
            valid_items = []
            for _, row in edited_items.iterrows():
                if str(row['Description']).strip() and float(row['Qty']) > 0:
                    valid_items.append({
                        "desc": str(row['Description']),
                        "hsn": str(row['HSN/SAC']),
                        "qty": int(row['Qty']),
                        "rate": float(row['Rate'])
                    })
            
            if not valid_items:
                st.error("Please add at least one valid item.")
            else:
                invoice_data = {
                    "invoice_type": inv_type, "invoice_no": inv_no, "order_date": order_date.strftime("%d-%b-%Y"),
                    "client_name": client_name, "client_address": client_address, "client_gst": client_gst,
                    "place_of_supply": place_of_supply, "items": valid_items,
                    "discount": discount, "deduction": deduction
                }
                pdf_buffer, _ = generate_invoice_pdf(invoice_data)
                st.session_state.pdf_data = pdf_buffer
                st.session_state.inv_no = inv_no

    # --- DOWNLOAD BUTTON (Outside Form) ---
    if st.session_state.pdf_data is not None:
        st.download_button(f"⬇️ Download {st.session_state.inv_no}.pdf", st.session_state.pdf_data, 
                           f"{st.session_state.inv_no}.pdf", "application/pdf")
