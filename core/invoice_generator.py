import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from num2words import num2words

# Import your constants
from core.constants import (
    COMPANY_NAME, COMPANY_CO, COMPANY_ADDRESS, 
    COMPANY_GST, COMPANY_PAN, BANK_NAME, 
    BANK_ACCOUNT_NAME, BANK_ACCOUNT_NO, BANK_IFSC
)

def get_amount_in_words(amount):
    return num2words(int(amount), lang='en_IN').title() + " Only"

def generate_invoice_pdf(invoice_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    # 1. Logo
    try:
        logo = Image("logo.png", width=1.5*inch, height=0.75*inch)
        elements.append(logo)
        elements.append(Spacer(1, 10))
    except:
        pass # Logo missing, continue without

    # 2. Header
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, fontSize=16, spaceAfter=10)
    elements.append(Paragraph(f"<b>{invoice_data['invoice_type'].upper()}</b>", title_style))

    # 3. Company & Invoice Details
    full_company_text = f"<b>{COMPANY_NAME}</b><br/>{COMPANY_CO}<br/>{COMPANY_ADDRESS.replace(chr(10), '<br/>')}<br/><b>GSTIN:</b> {COMPANY_GST}<br/><b>PAN:</b> {COMPANY_PAN}"
    
    top_data = [
        [Paragraph(full_company_text, styles['Normal']),
         Paragraph(f"<b>Invoice No:</b> {invoice_data['invoice_no']}<br/><b>Date:</b> {invoice_data['order_date']}<br/><b>Place of Supply:</b> {invoice_data['place_of_supply']}", styles['Normal'])]
    ]
    
    top_table = Table(top_data, colWidths=[3.5 * inch, 3.5 * inch])
    top_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(top_table)
    elements.append(Spacer(1, 20))

    # 4. Itemized Table
    table_data = [['S.No', 'Description', 'HSN', 'Qty', 'Rate', 'Amount']]
    subtotal = 0
    for idx, item in enumerate(invoice_data['items']):
        amt = item['qty'] * item['rate']
        subtotal += amt
        table_data.append([str(idx+1), item['desc'], item['hsn'], str(item['qty']), f"{item['rate']:,.2f}", f"{amt:,.2f}"])

    # Tax Logic
    is_telangana = invoice_data['place_of_supply'].strip().lower() == "telangana"
    tax_amt = subtotal * 0.18
    
    table_data.append(['', '', '', '', 'Subtotal', f"{subtotal:,.2f}"])
    if is_telangana:
        table_data.append(['', '', '', '', 'CGST (9%)', f"{subtotal*0.09:,.2f}"])
        table_data.append(['', '', '', '', 'SGST (9%)', f"{subtotal*0.09:,.2f}"])
    else:
        table_data.append(['', '', '', '', 'IGST (18%)', f"{tax_amt:,.2f}"])
        
    # Add Deductions if present
    if invoice_data.get('discount', 0) > 0:
        table_data.append(['', '', '', '', 'Discount', f"-{invoice_data['discount']:,.2f}"])
    if invoice_data.get('deduction', 0) > 0:
        table_data.append(['', '', '', '', 'Deduction', f"-{invoice_data['deduction']:,.2f}"])

    total = subtotal + tax_amt - invoice_data.get('discount', 0) - invoice_data.get('deduction', 0)
    table_data.append(['', '', '', '', 'Grand Total', f"{total:,.2f}"])

    # Apply Right Alignment for all numeric columns (4 and 5)
    item_table = Table(table_data, colWidths=[0.5*inch, 2.5*inch, 0.8*inch, 0.5*inch, 1.0*inch, 1.0*inch])
    styles_list = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
        ('ALIGN', (4, 0), (-1, -1), 'RIGHT'), # Force Right Align Money
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),   # Description Left
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
    ]
    # Bold the totals
    styles_list.append(('FONTNAME', (4, -1), (-1, -1), 'Helvetica-Bold'))
    
    item_table.setStyle(TableStyle(styles_list))
    elements.append(item_table)

    # 5. Footer & Legal
    elements.append(Paragraph(f"<b>Amount in Words:</b> {get_amount_in_words(total)}", styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("<b>Declaration:</b><br/>Certified that the particulars given above are true and correct.", styles['Normal']))
    elements.append(Spacer(1, 40))

    # Signature Block
    sign_data = [["", "For BOLD AND ITALIC"], ["", ""], ["", "Authorized Signatory"]]
    sign_table = Table(sign_data, colWidths=[4*inch, 3*inch])
    sign_table.setStyle(TableStyle([('ALIGN', (1, 2), (1, 2), 'CENTER')]))
    elements.append(sign_table)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer, total
