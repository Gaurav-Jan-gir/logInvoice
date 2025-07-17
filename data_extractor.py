import re

def custom_split(line: str, headers: list) -> list:
    invoice_items = ["items", "item", "product", "description", "quantity", "unit", "unit price", "total", "total price"]
    name_keywords = ['item', 'product', 'description', 'name']
    price_keywords = ['price', 'unit', 'unit price', 'total', 'total price', 'amount', 'cost', 'value']
    
    if not headers:
        words = line.split()
        result = []
        i = 0
        while i < len(words):
            if i < len(words) - 1:
                two_word = f"{words[i]} {words[i+1]}".lower()
                if two_word in invoice_items:
                    result.append(f"{words[i]} {words[i+1]}")
                    i += 2
                    continue
            
            if words[i].lower() in invoice_items:
                result.append(words[i])
            i += 1
        
        return result
    else:
        parts = line.split()
        result = []
        
        name_cols = []
        quantity_col = -1
        price_cols = []
        
        for i, header in enumerate(headers):
            header_lower = header.lower()
            if any(keyword in header_lower for keyword in name_keywords):
                name_cols.append(i)
            elif 'quantity' in header_lower:
                quantity_col = i
            elif any(keyword in header_lower for keyword in price_keywords):
                price_cols.append(i)
        
        quantity_idx = -1
        for i, part in enumerate(parts):
            if part.isdigit() or (part.replace('.', '').isdigit() and part.count('.') <= 1):
                if '$' not in part:
                    quantity_idx = i
                    break
        
        if quantity_idx > 0 and len(headers) > 0:
            name = ' '.join(parts[:quantity_idx])
            result.append(name)
            
            result.extend(parts[quantity_idx:])
            
            while len(result) < len(headers):
                result.append("")
            result = result[:len(headers)]
        else:
            if len(parts) >= len(headers):
                name_parts_count = len(parts) - len(headers) + 1
                name = ' '.join(parts[:name_parts_count])
                result = [name] + parts[name_parts_count:]
            else:
                result = parts + [""] * (len(headers) - len(parts))
        
        return result
    


def extract_data_from_text(text : str) -> dict:
    data = {
        "invoice_number": [],
        "date": [],
        "customer_name": [],
        "address": [],
        "total": [],
        "invoice_items": []
    }
    
    dataNames = {
        "invoice_number" : ["invoice number", "invoice no", "inv no"],
        "date" : ["date", "invoice date"],
        "customer_name" : ["customer name", "client name", "client", "bill to", "to", "billed to"],
        "address" : ["address", "billing address", "ship to", "shipping address"],
        "total" : ["total", "grand total", "amount due", "balance due"],
        "invoice_items" : ["items", "item", "product", "description", "quantity", "unit", "unit price", "total", "total price"]
    }
    
    tabular_data = []
    tabular_data_order = []
    
    tabular_data_found = False
    tabular_data_end = False
    lines = text.split('\n')

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        line_words = line.split()
        header_matches = 0
        for word in line_words:
            for header in dataNames["invoice_items"]:
                if word.lower() in header or header in word.lower():
                    header_matches += 1
                    break
        
        if header_matches >= 2 and not tabular_data_found:
            tabular_data_found = True
            tabular_data_order = custom_split(line, [])
            continue
            
        if tabular_data_found and not tabular_data_end:
            if any(word.lower() in dataNames['total'] + ['page'] for word in line_words):
                if any(word.lower() in dataNames['total'] for word in line_words):
                    line_lower = line.lower()
                    for keyword in dataNames['total']:
                        if keyword in line_lower:
                            total_match = re.search(r'\$[\d,]+\.?\d*', line)
                            if total_match:
                                data['total'].append(total_match.group())
                            break
                tabular_data_end = True
                continue
            elif any(char.isdigit() or char in '$.' for char in line):
                tabular_data.append(custom_split(line, tabular_data_order))

        if not tabular_data_found or tabular_data_end:
            line_lower = line.lower()
            for field_name, keywords in dataNames.items():
                if field_name != "invoice_items":
                    for keyword in keywords:
                        if keyword in line_lower:
                            if ':' in line:
                                value = line.split(':', 1)[1].strip()
                            else:
                                keyword_pos = line_lower.find(keyword)
                                value = line[keyword_pos + len(keyword):].strip()
                            
                            if value:
                                data[field_name].append(value)
                            break

    if tabular_data:
        data["invoice_items"] = {
            "headers": tabular_data_order,
            "rows": tabular_data
        }

    return data

with open('sample.txt', 'r') as file:
    text = file.read()
    extracted_data = extract_data_from_text(text)
    print(extracted_data)