import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Import our new constants
from core.constants import (
    COMPANY_NAME, COMPANY_CO, COMPANY_ADDRESS, 
    COMPANY_GSTIN, COMPANY_PAN, COMPANY_STATE,
    BANK_NAME, BANK_ACCOUNT_NAME, BANK_ACCOUNT_NO, BANK_IFSC
)

def generate_invoice_pdf(invoice_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    # --- Header ---
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, fontSize=16, spaceAfter=20)
    elements.append(Paragraph(f"<b>{invoice_data['invoice_type'].upper()}</b>", title_style))

    # --- Company Info & Invoice Details ---
    # Create a 2-column layout for the top section
    top_data = [
        [Paragraph(f"<b>{COMPANY_NAME}</b><br/>{COMPANY_ADDRESS.replace(chr(10), '<br/>')}<br/><b>GSTIN:</b> {COMPANY_GST}", styles['Normal']),
         Paragraph(f"<b>Invoice No:</b> {invoice_data['invoice_no']}<br/><b>Date:</b> {invoice_data['order_date']}<br/><b>Place of Supply:</b> {invoice_data['place_of_supply']}", styles['Normal'])]
    ]
    
    top_table = Table(top_data, colWidths=[3.5 * inch, 3.5 * inch])
    top_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
    ]))
    elements.append(top_table)

    # --- Bill To Section ---
    elements.append(Paragraph("<b>Billed To:</b>", styles['Heading3']))
    elements.append(Paragraph(f"{invoice_data['client_name']}<br/>{invoice_data['client_address'].replace(chr(10), '<br/>')}<br/><b>GSTIN:</b> {invoice_data['client_gst']}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # --- Itemized Table ---
    table_data = [['S.No', 'Description', 'HSN/SAC', 'Qty', 'Rate', 'Amount']]
    
    subtotal = 0
    for idx, item in enumerate(invoice_data['items']):
        amt = item['qty'] * item['rate']
        subtotal += amt
        table_data.append([str(idx + 1), item['desc'], item['hsn'], str(item['qty']), f"Rs. {item['rate']:,.2f}", f"Rs. {amt:,.2f}"])

    # Tax Logic
    is_telangana = invoice_data['place_of_supply'].strip().lower() == "telangana"
    if is_telangana:
        cgst = subtotal * 0.09
        sgst = subtotal * 0.09
        total = subtotal + cgst + sgst
        table_data.append(['', '', '', '', 'Subtotal', f"Rs. {subtotal:,.2f}"])
        table_data.append(['', '', '', '', 'CGST (9%)', f"Rs. {cgst:,.2f}"])
        table_data.append(['', '', '', '', 'SGST (9%)', f"Rs. {sgst:,.2f}"])
    else:
        igst = subtotal * 0.18
        total = subtotal + igst
        table_data.append(['', '', '', '', 'Subtotal', f"Rs. {subtotal:,.2f}"])
        table_data.append(['', '', '', '', 'IGST (18%)', f"Rs. {igst:,.2f}"])

    table_data.append(['', '', '', '', 'Grand Total', f"Rs. {total:,.2f}"])

    # Style the Item Table
    item_table = Table(table_data, colWidths=[0.5 * inch, 2.5 * inch, 1 * inch, 0.5 * inch, 1.25 * inch, 1.25 * inch])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'), # Description left aligned
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'), # Money right aligned
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
        
        # Make Total rows bold
        ('FONTNAME', (4, -len(table_data)+len(invoice_data['items'])+1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    elements.append(item_table)

    # --- Footer ---
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("<b>Bank Details:</b>", styles['Normal']))
    elements.append(Paragraph("Bank: YES BANK<br/>A/c Name: BOLD AND ITALIC<br/>A/c No: 123456789<br/>IFSC: YESB0000001", styles['Normal'])) # Update with actual bank
    
    doc.build(elements)
    buffer.seek(0)
    return buffer, total
