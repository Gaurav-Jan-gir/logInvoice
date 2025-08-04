

import re
import sys
import pandas as pd
import os

def parse_invoice_data(invoice_text):
    invoice_number = re.search(r'Invoice Number:\s*(\S+)|#\s+(\d+)', invoice_text, re.IGNORECASE)
    if invoice_number:
        invoice_number = invoice_number.group(1) or invoice_number.group(2)
    else:
        invoice_number = None
    date = re.search(r'Date:\s*([\w\s,]+\d{4}|[\d-]+)', invoice_text)
    if date:
        date = date.group(1).strip()
    else:
        date = None
    billed_to = re.search(r'(?:Billed?\s+To|Bill\s+To):\s*([^\n]+?)(?:\s+Balance Due|\s+\w+@|\n)', invoice_text, re.IGNORECASE)
    if billed_to:
        billed_to = billed_to.group(1).strip()
    else:
        billed_to = None
    address = re.search(r'Address:\s*(.+?)\n', invoice_text)
    if address:
        address = address.group(1).strip()
    else:
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', invoice_text)
        address = email_match.group(0) if email_match else "Address not found"
    items_pattern = r'^(Phone Cover|Screen Guard|Earbuds|Earphones|Widget [AB]|Service Fee)\s+(\d+)\s+[₹$]\s*(\d+(?:\.\d{2})?)\s+[₹$]\s*(\d+(?:\.\d{2})?)$'
    items = re.findall(items_pattern, invoice_text, re.MULTILINE)
    sender_match = re.search(r'(The\s+\w+.*?@\w+\.\w+)', invoice_text, re.DOTALL)
    sender_info = sender_match.group(1).strip() if sender_match else None
    df_items = pd.DataFrame(items, columns=['Item', 'Quantity', 'Unit Price', 'Total'])
    if not df_items.empty:
        df_items['Quantity'] = pd.to_numeric(df_items['Quantity'])
        df_items['Unit Price'] = pd.to_numeric(df_items['Unit Price'])
        df_items['Total'] = pd.to_numeric(df_items['Total'])
    total_amount = re.search(r'Total:?\s*[₹$]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', invoice_text)
    if total_amount:
        total_amount = total_amount.group(1).replace(',', '')
    else:
        total_amount = '0.00'
    return {
        'invoice_number': invoice_number,
        'date': date,
        'sender_info': sender_info,
        'billed_to': billed_to,
        'address': address,
        'items': df_items,
        'total_amount': float(total_amount)
    }


