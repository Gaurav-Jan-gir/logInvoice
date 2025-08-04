import database_functions1 as dbf
from cryptography.fernet import Fernet
import json
import os
import re
import imaplib
import email
import help
from datetime import datetime
import pdfplumber
import pandas as pd
from tkinter import filedialog

def get_workspace_dir():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(script_dir)
    return workspace_dir

global settings_file, key_file
workspace_dir = get_workspace_dir()
settings_file = os.path.join(workspace_dir, ".invoice_logger_settings.json.enc")
key_file = os.path.join(workspace_dir, ".invoice_logger_key")

def save_file_dialog(filetypes):
    """
    Open a save file dialog and return the selected file path
    """
    try:
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=filetypes,
            title="Save Excel File As..."
        )
        return filename if filename else None
    except Exception as e:
        print(f"Error opening file dialog: {e}")
        return None

def generate_or_load_key():
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file,'wb') as f:
            f.write(key)
        return key

def get_db(db_config):
    if not db_config or not all([db_config.get('host'), db_config.get('user'), db_config.get('database')]):
        print("Incomplete database configuration.")
        return None
    return dbf.Database(db_config.get('host'), db_config.get('user'), db_config.get('password'), db_config.get('database'))

def get_remembered_settings():
    key = generate_or_load_key()
    if not os.path.exists(settings_file):
        return None, None
    
    fernet = Fernet(key)

    with open(settings_file, "rb") as f:
        encrypted = f.read()

    decrypted = fernet.decrypt(encrypted)
    settings = json.loads(decrypted)
    return settings.get('mail'), settings.get('database')

def load_remembered_settings():
    mail_config, db_config = get_remembered_settings()
    
    mail_obj = None
    db_obj = None
    
    if mail_config and mail_config.get("email") and mail_config.get("password"):
        mail_obj = connect_email(mail_config.get("email"), mail_config.get("password"))
    
    if db_config and all([db_config.get('host'), db_config.get('user'), db_config.get('database')]):
        db_obj = get_db(db_config)
    
    if mail_obj is None and db_obj is None:
        print("No valid remembered settings found.")
    
    return mail_obj, db_obj

def validate_email(email_address):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email_address):
        return False
    return True

def get_imap_server(email_address):
    validate_email(email_address)
    domain = email_address.split('@')[1].lower() 
    imap_servers = {
        'gmail.com': 'imap.gmail.com',
        'yahoo.com': 'imap.mail.yahoo.com',
        'outlook.com': 'outlook.office365.com',
        'hotmail.com': 'outlook.office365.com',
        'live.com': 'outlook.office365.com',
        'icloud.com': 'imap.mail.me.com',
        'me.com': 'imap.mail.me.com',
        'mac.com': 'imap.mail.me.com'
    }
    if domain in imap_servers:
        return imap_servers[domain]
    else:
        raise ValueError(f"IMAP server not configured for domain: {domain}")

def get_email_object(email_address : str, password : str):
    imap_server = get_imap_server(email_address)
    ob_email = imaplib.IMAP4_SSL(imap_server)
    ob_email.login(email_address, password)
    return ob_email

def connect_email(email_address, password):
    if not validate_email(email_address):
        print("Invalid Email Address")
        return None
    try:
        mail = get_email_object(email_address, password)
        return mail
    except Exception as e:
        print(f"Error : {e}")
        return None
    
def store_mail(email_address, password):
    _, db_config = get_remembered_settings()
    mail_config = {'email' : email_address, 'password' : password}
    config = {'mail' : mail_config, 'database' : db_config}
    
    key = generate_or_load_key()
    fernet = Fernet(key)

    data = json.dumps(config).encode()
    encrypted = fernet.encrypt(data)

    with open(settings_file, "wb") as f:
        f.write(encrypted)

def get_email_help(email_address):
    domain = email_address.split('@')[1].lower()
    return help.get_email_help_text(domain)

def store_db(host, user, password, database):
    mail_config, _ = get_remembered_settings()
    db_config = {'host' : host, 'user' : user, 'password' : password, 'database' : database}
    config = {'mail' : mail_config, 'database' : db_config}
    
    key = generate_or_load_key()
    fernet = Fernet(key)

    data = json.dumps(config).encode()
    encrypted = fernet.encrypt(data)

    with open(settings_file, "wb") as f:
        f.write(encrypted)

def get_database_help():
    return help.get_database_help_text()
        
def log_invoice(mail, db):
    if not mail:
        return "Email is not connected."
    if not db:
        return "Database is not connected."

    try:
        # This function handles the entire pipeline: download -> extract -> parse -> log
        results = parse_all_invoices(mail, db=db)

        download_results = results.get('download_results', {})
        parsing_results = results.get('parsing_results')

        dl_count = download_results.get('successful_count', 0)
        
        # Ensure parsing_results is not None before accessing its keys
        if parsing_results:
            parse_count = len(parsing_results.get('successful_parses', []))
        else:
            parse_count = 0
        
        if dl_count == 0:
            return "No new invoices found to download."
        
        return f"Process complete. Downloaded {dl_count} new attachments. Successfully parsed and logged {parse_count} invoices."

    except Exception as e:
        print(f"[ERROR] An error occurred during the log_invoice process: {e}")
        return f"An error occurred during invoice logging: {str(e)}"
    
def log_invoices_periodically(mail, db, interval, stop_event):
    while not stop_event.is_set():
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running periodic check for new invoices...")
        try:
            result = log_invoice(mail, db)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Periodic check finished. Result: {result}")
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] An error occurred in the periodic logging thread: {e}")
        stop_event.wait(interval)
    print("Periodic invoice logging has been stopped.")

def get_invoices_from_db(db, date_in = "", time_in = "", date_out = "", time_out = ""):
    if not db:
        return "Database is not connected."
    return db.get_invoices(date_in, time_in, date_out, time_out)

def validate_date_time(date, time):
    date_pattern = r'^\d{2}-\d{2}-\d{4}$'
    time_pattern = r'^\d{2}:\d{2}:\d{2}$'

    if date == "" and time == "":
        return True

    if date != "" and not re.match(date_pattern, date):
        return False

    if time != "" and not re.match(time_pattern, time):
        return False
    
    return True

def validate_sql_query(query):
    stripped_query = query.strip()
    if not stripped_query:
        return (False, "Query cannot be empty.")

    allowed_start_pattern = r'^\s*(select|insert|update|delete|show|desc|explain)\b'
    if not re.search(allowed_start_pattern, stripped_query, re.IGNORECASE):
        return (False, "Query must begin with a valid command (e.g., SELECT, INSERT, UPDATE).")

    destructive_pattern = r'\b(drop|truncate)\b'
    if re.search(destructive_pattern, stripped_query, re.IGNORECASE):
        return (False, "Destructive commands (DROP, TRUNCATE) are not allowed.")

    if ';' in stripped_query[:-1]:
        return (False, "Only a single SQL statement is allowed.")

    return (True, "Validation successful.")

def execute_query(db, query):
    is_valid, message = validate_sql_query(query)
    
    if not is_valid:
        return message
        
    if not db:
        return "Database is not connected."

    return db.execute_raw_query(query)

def get_database_summary(db):
    if not db:
        return "Database is not Connected"
    return db.get_summary()




def download_invoices(email_object : imaplib.IMAP4_SSL):
    tracking_file = os.path.join(get_workspace_dir(), "email_tracking.json")
    try:
        with open(tracking_file, 'r') as f:
            tracking_data = json.load(f)
    except FileNotFoundError:
        tracking_data = {
            'last_successful_date': None,
            'processed_emails': [],
            'failed_emails': []
        }
    email_object.select("INBOX")
    search_criteria = [
        'OR',
            'OR',
                'OR',
                    'SUBJECT', 'Invoice',
                    'SUBJECT', 'invoice',
                'SUBJECT', 'bill',
            'SUBJECT', 'receipt'
    ]
    if tracking_data['last_successful_date']:
        try:
            since_date = datetime.strptime(tracking_data['last_successful_date'], "%d-%b-%Y").strftime("%d-%b-%Y")
        except Exception:
            since_date = tracking_data['last_successful_date']
        search_criteria += ['SINCE', since_date]
    status, email_ids = email_object.search(None, *search_criteria)
    email_ids = email_ids[0].split()
    pdf_paths = []
    current_time = datetime.now().strftime("%d-%b-%Y")
    new_processed = []
    new_failed = []
    for email_id in email_ids:
        email_id_str = email_id.decode() if isinstance(email_id, bytes) else str(email_id)
        if email_id_str in tracking_data['processed_emails']:
            continue
        try:
            status, msg_data = email_object.fetch(email_id, "(RFC822)")
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            email_date = email_message.get('Date', '')
            email_subject = email_message.get('Subject', '')
            pdf_found = False
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue
                    filename = part.get_filename()
                    if filename and filename.lower().endswith('.pdf'):
                        pdf_found = True
                        attachments_dir = os.path.join(get_workspace_dir(), "attachments")
                        os.makedirs(attachments_dir, exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        unique_filename = f"{timestamp}_{filename}"
                        pdf_path = os.path.join(attachments_dir, unique_filename)
                        pdf_paths.append(pdf_path)
                        with open(pdf_path, 'wb') as f:
                            f.write(part.get_payload(decode=True))
            
            new_processed.append({
                'email_id': email_id_str,
                'date': email_date,
                'subject': email_subject,
                'pdf_found': pdf_found,
                'processed_date': current_time,
                'status': 'success'
            })
            
        except Exception as e:
            new_failed.append({
                'email_id': email_id_str,
                'error': str(e),
                'failed_date': current_time,
                'retry_count': tracking_data.get('failed_emails', {}).get(email_id_str, {}).get('retry_count', 0) + 1
            })

    tracking_data['processed_emails'].extend([item['email_id'] for item in new_processed])
    tracking_data['failed_emails'].extend(new_failed)
    tracking_data['last_successful_date'] = current_time
    tracking_data['last_run_date'] = current_time
    
    with open(tracking_file, 'w') as f:
        json.dump(tracking_data, f, indent=2)
    
    parsed_invoices_file = os.path.join(get_workspace_dir(), "parsed_invoices.json")
    try:
        with open(parsed_invoices_file, 'r') as f:
            parsed_invoices = json.load(f)
    except FileNotFoundError:
        parsed_invoices = []
    
    for i, pdf_path in enumerate(pdf_paths):
        parsed_invoices.append({
            'pdf_path': pdf_path,
            'original_filename': os.path.basename(pdf_path).split('_', 1)[-1] if '_' in os.path.basename(pdf_path) else os.path.basename(pdf_path),
            'email_info': new_processed[i] if i < len(new_processed) else {},
            'downloaded_date': current_time,
            'status': 'downloaded',
            'parsed': False
        })
    
    with open(parsed_invoices_file, 'w') as f:
        json.dump(parsed_invoices, f, indent=2)
    
    return {
        'pdf_paths': pdf_paths,
        'successful_count': len(new_processed),
        'failed_count': len(new_failed),
        'total_processed': len(email_ids)
    }

def retry_failed_downloads(email_object : imaplib.IMAP4_SSL, max_retries=3):
    tracking_file = os.path.join(get_workspace_dir(), "email_tracking.json")
    try:
        with open(tracking_file, 'r') as f:
            tracking_data = json.load(f)
    except FileNotFoundError:
        return {'message': 'No tracking data found'}
    
    failed_emails = [email for email in tracking_data.get('failed_emails', []) 
                    if email.get('retry_count', 0) < max_retries]
    
    if not failed_emails:
        return {'message': 'No failed emails to retry'}
    
    pdf_paths = []
    current_time = datetime.now().strftime("%d-%b-%Y")
    successful_retries = []
    still_failed = []
    
    email_object.select("INBOX")
    
    for failed_email in failed_emails:
        email_id = failed_email['email_id']
        try:
            status, msg_data = email_object.fetch(email_id, "(RFC822)")
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            email_date = email_message.get('Date', '')
            email_subject = email_message.get('Subject', '')
            
            pdf_found = False
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                    if part.get('Content-Disposition') is None:
                        continue
                    filename = part.get_filename()
                    if filename and filename.lower().endswith('.pdf'):
                        pdf_found = True
                        attachments_dir = os.path.join(get_workspace_dir(), "attachments")
                        os.makedirs(attachments_dir, exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        unique_filename = f"{timestamp}_{filename}"
                        pdf_path = os.path.join(attachments_dir, unique_filename)
                        pdf_paths.append(pdf_path)
                        
                        with open(pdf_path, 'wb') as f:
                            f.write(part.get_payload(decode=True))
            
            successful_retries.append({
                'email_id': email_id,
                'date': email_date,
                'subject': email_subject,
                'pdf_found': pdf_found,
                'processed_date': current_time,
                'status': 'retry_success',
                'retry_attempt': failed_email.get('retry_count', 0) + 1
            })
            
        except Exception as e:
            still_failed.append({
                'email_id': email_id,
                'error': str(e),
                'failed_date': current_time,
                'retry_count': failed_email.get('retry_count', 0) + 1,
                'original_error': failed_email.get('error', '')
            })
    
    successful_email_ids = [item['email_id'] for item in successful_retries]
    tracking_data['failed_emails'] = [email for email in tracking_data['failed_emails'] 
                                     if email['email_id'] not in successful_email_ids]
    
    tracking_data['failed_emails'].extend(still_failed)
    
    tracking_data['processed_emails'].extend(successful_email_ids)
    tracking_data['last_retry_date'] = current_time
    
    with open(tracking_file, 'w') as f:
        json.dump(tracking_data, f, indent=2)
    
    parsed_invoices_file = os.path.join(get_workspace_dir(), "parsed_invoices.json")
    try:
        with open(parsed_invoices_file, 'r') as f:
            parsed_invoices = json.load(f)
    except FileNotFoundError:
        parsed_invoices = []
    
    for i, pdf_path in enumerate(pdf_paths):
        parsed_invoices.append({
            'pdf_path': pdf_path,
            'original_filename': os.path.basename(pdf_path).split('_', 1)[-1] if '_' in os.path.basename(pdf_path) else os.path.basename(pdf_path),
            'email_info': successful_retries[i] if i < len(successful_retries) else {},
            'downloaded_date': current_time,
            'status': 'retry_downloaded',
            'parsed': False
        })
    
    with open(parsed_invoices_file, 'w') as f:
        json.dump(parsed_invoices, f, indent=2)
    
    return {
        'pdf_paths': pdf_paths,
        'successful_retries': len(successful_retries),
        'still_failed': len(still_failed),
        'total_attempted': len(failed_emails),
        'message': f'Retry completed: {len(successful_retries)} successful, {len(still_failed)} still failed'
    }

def extract_text_from_pdfs(pdf_paths, output_folder=None):
    if output_folder is None:
        output_folder = os.path.join(get_workspace_dir(), "extracted_text")
    extraction_results = {
        'successful_extractions': [],
        'failed_extractions': [],
        'total_processed': len(pdf_paths)
    }
    
    for pdf_path in pdf_paths:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_content = ""
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"--- Page {page_num + 1} ---\n"
                        text_content += page_text + "\n\n"
                
                if text_content.strip():
                    os.makedirs(output_folder, exist_ok=True)

                    pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
                    output_filename = f"{pdf_basename}_extracted.txt"
                    output_file = os.path.join(output_folder, output_filename)
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(text_content)
                    
                    extraction_results['successful_extractions'].append({
                        'pdf_path': pdf_path,
                        'text_file': output_file,
                        'pages_extracted': len(pdf.pages),
                        'text_length': len(text_content)
                    })
                else:
                    extraction_results['failed_extractions'].append({
                        'pdf_path': pdf_path,
                        'error': 'No text content extracted'
                    })
                    
        except Exception as e:
            extraction_results['failed_extractions'].append({
                'pdf_path': pdf_path,
                'error': str(e)
            })
    
    return extraction_results

def process_downloaded_invoices(email_object: imaplib.IMAP4_SSL, extract_text=True):
    download_results = download_invoices(email_object)
    
    results = {
        'download_results': download_results,
        'extraction_results': None
    }

    if extract_text and download_results['pdf_paths']:
        extraction_results = extract_text_from_pdfs(download_results['pdf_paths'])
        results['extraction_results'] = extraction_results

        try:
            parsed_invoices_file = os.path.join(get_workspace_dir(), "parsed_invoices.json")
            with open(parsed_invoices_file, 'r') as f:
                parsed_invoices = json.load(f)
        except FileNotFoundError:
            parsed_invoices = []

        for invoice in parsed_invoices:
            pdf_path = invoice.get('pdf_path', '')
            
            for success in extraction_results['successful_extractions']:
                if success['pdf_path'] == pdf_path:
                    invoice['text_extracted'] = True
                    invoice['text_file'] = success['text_file']
                    invoice['extraction_date'] = datetime.now().strftime("%d-%b-%Y")
                    break
            else:
                for failure in extraction_results['failed_extractions']:
                    if failure['pdf_path'] == pdf_path:
                        invoice['text_extracted'] = False
                        invoice['extraction_error'] = failure['error']
                        break
        
        with open(parsed_invoices_file, 'w') as f:
            json.dump(parsed_invoices, f, indent=2)
    
    return results

def retry_and_extract(email_object: imaplib.IMAP4_SSL, max_retries=3, extract_text=True):
    retry_results = retry_failed_downloads(email_object, max_retries)
    results = {
        'retry_results': retry_results,
        'extraction_results': None
    }
    if extract_text and 'pdf_paths' in retry_results and retry_results['pdf_paths']:
        extraction_results = extract_text_from_pdfs(retry_results['pdf_paths'])
        results['extraction_results'] = extraction_results
        try:
            parsed_invoices_file = os.path.join(get_workspace_dir(), "parsed_invoices.json")
            with open(parsed_invoices_file, 'r') as f:
                parsed_invoices = json.load(f)
        except FileNotFoundError:
            parsed_invoices = []
        
        for invoice in parsed_invoices:
            pdf_path = invoice.get('pdf_path', '')
            for success in extraction_results['successful_extractions']:
                if success['pdf_path'] == pdf_path:
                    invoice['text_extracted'] = True
                    invoice['text_file'] = success['text_file']
                    invoice['extraction_date'] = datetime.now().strftime("%d-%b-%Y")
                    break
        
        with open(parsed_invoices_file, 'w') as f:
            json.dump(parsed_invoices, f, indent=2)
    
    return results

def get_extraction_summary():
    try:
        parsed_invoices_file = os.path.join(get_workspace_dir(), "parsed_invoices.json")
        with open(parsed_invoices_file, 'r') as f:
            parsed_invoices = json.load(f)
    except FileNotFoundError:
        return {'message': 'No parsed invoices found'}
    
    summary = {
        'total_invoices': len(parsed_invoices),
        'downloaded_count': len([inv for inv in parsed_invoices if inv.get('status') in ['downloaded', 'retry_downloaded']]),
        'text_extracted_count': len([inv for inv in parsed_invoices if inv.get('text_extracted', False)]),
        'extraction_failed_count': len([inv for inv in parsed_invoices if inv.get('text_extracted') == False]),
        'pending_extraction': len([inv for inv in parsed_invoices if 'text_extracted' not in inv]),
        'recent_downloads': [inv for inv in parsed_invoices if inv.get('downloaded_date') == datetime.now().strftime("%d-%b-%Y")],
        'failed_extractions': [inv for inv in parsed_invoices if inv.get('text_extracted') == False]
    }
    
    return summary

def clean_extracted_text(text):

    text = re.sub(r'\s+', ' ', text)

    def fix_doubled_chars(match):
        word = match.group(0)
        if len(word) > 2:
            fixed = ""
            i = 0
            while i < len(word):
                fixed += word[i]
                if i + 1 < len(word) and word[i] == word[i + 1]:
                    i += 2
                else:
                    i += 1
            return fixed
        return word

    text = re.sub(r'\b[A-Z]{2,}[a-z]*[A-Z]*[a-z]*\b', fix_doubled_chars, text)
    
    return text

def convert_date_to_mysql_format(date_str):
    """
    Convert various date formats to MySQL date format (YYYY-MM-DD)
    """
    if not date_str:
        return None
    
    import time
    from datetime import datetime
    
    # Clean the date string
    date_str = re.sub(r'[^\w\s/-]', '', date_str).strip()
    
    # Common date patterns and their conversions
    date_formats = [
        '%Y-%m-%d',      # 2025-08-03
        '%d/%m/%Y',      # 23/08/2025
        '%m/%d/%Y',      # 08/23/2025
        '%d-%m-%Y',      # 23-08-2025
        '%m-%d-%Y',      # 08-23-2025
        '%d/%m/%y',      # 23/08/25
        '%m/%d/%y',      # 08/23/25
        '%Y/%m/%d',      # 2025/08/23
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # Try to handle partial dates like "23, 2025"
    if re.match(r'^\d{1,2},?\s+\d{4}$', date_str):
        parts = re.findall(r'\d+', date_str)
        if len(parts) == 2:
            day, year = parts
            # Default to current month if only day and year provided
            current_month = datetime.now().month
            try:
                parsed_date = datetime(int(year), current_month, int(day))
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                pass
    
    print(f"[DEBUG] Could not parse date: {date_str}, using current date as fallback")
    return datetime.now().strftime('%Y-%m-%d')

def parse_invoice_data(invoice_text):
    """
    Parse invoice text and extract key information with robust fallback values
    """
    if not invoice_text:
        return None
        
    print(f"[DEBUG] Parsing invoice text (length: {len(invoice_text)})")
    
    cleaned_text = clean_extracted_text(invoice_text)
    
    # Extract invoice number with fallback
    invoice_number = None
    patterns = [
        r'Invoice\s*#?\s*[:\-]?\s*(\w+\d+|\d+)',
        r'Invoice\s*#:\s*(\d+)',          
        r'Invoice Number:\s*(\S+)',
        r'INV(\d+)',
        r'#\s*(\d+)',
        r'Invoice\s+(\w+)',
        r'INVOICE[\s\w]*\s+(\w+\d+)',
        r'(?:Invoice|INVOICE)[\s\-]*(\w*\d+)'
    ]
    
    for pattern in patterns:
        for text_version in [invoice_text, cleaned_text]:
            match = re.search(pattern, text_version, re.IGNORECASE)
            if match:
                invoice_number = match.group(1)
                break
        if invoice_number:
            break
    
    if not invoice_number:
        print("[DEBUG] Invoice number not found, using fallback")
        import time
        invoice_number = f"INV_{int(time.time())}"  # Fallback invoice number

    # Extract and convert date with robust parsing
    date = None
    date_patterns = [
        r'(?:Due Date|Invoice Date):\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'Date:\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'Date:\s*(\d{4}-\d{2}-\d{2})',
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{1,2}-\d{1,2}-\d{4})',
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),?\s+(\d{4})',
        r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})',
        r'(\d{1,2}),?\s+(\d{4})',  # Handle "23, 2025" format
    ]
    
    for pattern in date_patterns:
        for text_version in [invoice_text, cleaned_text]:
            match = re.search(pattern, text_version, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:  # Month name format
                    month_names = {
                        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
                    }
                    if pattern.startswith(r'(Jan'):  # Format: "Jul 14, 2025"
                        month = month_names.get(match.group(1).lower()[:3], '01')
                        day = match.group(2).zfill(2)
                        year = match.group(3)
                        date = f"{year}-{month}-{day}"
                    else:  # Format: "14 Jul 2025"
                        day = match.group(1).zfill(2)
                        month = month_names.get(match.group(2).lower()[:3], '01')
                        year = match.group(3)
                        date = f"{year}-{month}-{day}"
                else:
                    raw_date = match.group(1).strip()
                    date = convert_date_to_mysql_format(raw_date)
                break
        if date:
            break
    
    if not date:
        print("[DEBUG] Date not found, using current date")
        from datetime import datetime
        date = datetime.now().strftime('%Y-%m-%d')  # Fallback to current date

    # Extract billed_to with fallback
    billed_to = None
    billed_patterns = [
        r'Bill\s+To:\s*\n\s*([^\n]+)',            
        r'(?:Billed?\s+To|Bill\s+To):\s*([^\n]+?)(?:\s+Balance Due|\s+\w+@|\n)',
        r'BBIILLLL\s+TTOO\s*\n\s*([^\n]+)',
        r'BILL TO[:\s]*([^\n]+)',
        r'Billed To[:\s]*([^\n]+)',
        r'Bill\s+To[:\s]*([^\n]+)'
    ]
    
    for pattern in billed_patterns:
        for text_version in [invoice_text, cleaned_text]:
            match = re.search(pattern, text_version, re.IGNORECASE)
            if match:
                billed_to = match.group(1).strip()
                billed_to = clean_extracted_text(billed_to)
                break
        if billed_to:
            break
    
    if not billed_to:
        print("[DEBUG] Billed To information not found, using fallback")
        billed_to = "Customer"  # Fallback value

    # Extract address with fallback
    address = None
    address_patterns = [
        r'Address:\s*(.+?)\n',
        r'(?:Billed?\s+To|Bill\s+To)[^\n]*\n\s*([^\n]+(?:\n[^\n]+)*?)(?:\n\s*\n|\n\s*\w+@)',
        r'BBIILLLL\s+TTOO\s*\n\s*[^\n]+\s*\n\s*([^\n]+)',
        r'Gurugram[^\n]*\n([^\n]+)', 
    ]
    
    for pattern in address_patterns:
        for text_version in [invoice_text, cleaned_text]:
            match = re.search(pattern, text_version, re.IGNORECASE | re.DOTALL)
            if match:
                address = match.group(1).strip()
                address = clean_extracted_text(address)
                break
        if address:
            break
    
    if not address:
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', invoice_text)
        if email_match:
            address = email_match.group(0)
        else:
            print("[DEBUG] Address not found, using fallback")
            address = "N/A"  # Fallback value
    
    items_patterns = [
        r'^\d+\s+([^$]+?)\s+\$(\d+(?:\.\d{2})?)\s+(\d+)\s+\$(\d+(?:\.\d{2})?)$',
        r'(\w+(?:\s+\w+)*)\s+₹([\d,]+(?:\.\d{2})?)\s+(\d+)\s+₹([\d,]+(?:\.\d{2})?)(?:\s|$)',
        r'^(Phone Cover|Screen Guard|Earbuds|Earphones|Widget [AB]|Service Fee)\s+(\d+)\s+[₹$]\s*(\d+(?:\.\d{2})?)\s+[₹$]\s*(\d+(?:\.\d{2})?)$',
        r'^(Widget [AB]|Service Fee|Bag)\s+(\d+)\s+\$(\d+(?:\.\d{2})?)\s+\$(\d+(?:\.\d{2})?)$',
        r'^(\w+(?:\s+\w+)*)\s+₹([\d,]+(?:\.\d{2})?)\s+(\d+)\s+₹([\d,]+(?:\.\d{2})?)$',
        r'^(\w+(?:\s+\w+)*)\s+(\d+)\s+[₹$]([\d,]+(?:\.\d{2})?)\s+[₹$]([\d,]+(?:\.\d{2})?)$'
    ]
    
    items = []
    for pattern in items_patterns:
        for text_version in [invoice_text, cleaned_text]:
            found_items = re.findall(pattern, text_version, re.MULTILINE)
            if found_items:
                items = found_items
                break
        if items:
            break

    # Extract sender information with better patterns and fallback
    sender_info = None
    sender_patterns = [
        r'Bill From:\s*([^\n]+)',  # Bill From: single line only
        r'From:\s*([^\n]+)',  # From: pattern  
        r'Sender:\s*([^\n]+)',  # Sender: pattern
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*<([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>',  # Name <email>
        r'([A-Z][a-z]+ [A-Z][a-z]+)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # Name followed by email
        r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # Just email
    ]
    
    for pattern in sender_patterns:
        for text_version in [invoice_text, cleaned_text]:
            match = re.search(pattern, text_version, re.IGNORECASE)
            if match:
                if len(match.groups()) >= 2:  # Name and email pattern
                    name = match.group(1).strip()
                    email = match.group(2).strip()
                    if len(name) < 100:  # Reasonable name length
                        sender_info = f"{name} <{email}>"
                    else:
                        sender_info = email  # If name is too long, just use email
                else:
                    candidate = match.group(1).strip()
                    if len(candidate) < 100:  # Reasonable sender info length
                        sender_info = candidate
                
                if sender_info:
                    sender_info = clean_extracted_text(sender_info)
                    break
        if sender_info:
            break
    
    if not sender_info:
        print("[DEBUG] Sender information not found, using fallback")
        sender_info = "Unknown Sender"  # Fallback value

    # Detect currency from the text
    currency = 'USD'  # Default currency
    currency_patterns = [
        r'[₹]',  # Indian Rupee symbol
        r'INR|Rs\.',  # Indian Rupee text
        r'[$]',  # Dollar symbol  
        r'USD|US\$',  # US Dollar text
        r'[€]',  # Euro symbol
        r'EUR',  # Euro text
        r'[£]',  # Pound symbol
        r'GBP',  # British Pound text
    ]
    
    currency_map = {
        '₹': 'INR', 'INR': 'INR', 'Rs.': 'INR',
        '$': 'USD', 'USD': 'USD', 'US$': 'USD',
        '€': 'EUR', 'EUR': 'EUR',
        '£': 'GBP', 'GBP': 'GBP'
    }
    
    for pattern in currency_patterns:
        if re.search(pattern, invoice_text, re.IGNORECASE):
            for symbol, curr_code in currency_map.items():
                if pattern.strip('[]') in symbol or pattern == symbol:
                    currency = curr_code
                    break
            break
    
    print(f"[DEBUG] Detected currency: {currency}")
    print(f"[DEBUG] Detected sender: {sender_info}")

    df_items = pd.DataFrame()
    if items:
        if len(items[0]) == 4 and items[0][1].replace('.', '').isdigit():
            reordered_items = []
            for item in items:
                reordered_items.append((item[0].strip(), item[2], item[1], item[3]))
            df_items = pd.DataFrame(reordered_items, columns=['Item', 'Quantity', 'Unit Price', 'Total'])
        else:
            df_items = pd.DataFrame(items, columns=['Item', 'Quantity', 'Unit Price', 'Total'])
    
    if not df_items.empty:
        df_items['Item'] = df_items['Item'].apply(clean_extracted_text)
        df_items['Quantity'] = df_items['Quantity'].astype(str).str.replace(',', '').astype(float)
        df_items['Unit Price'] = df_items['Unit Price'].astype(str).str.replace(',', '').str.replace('$', '').astype(float)
        df_items['Total'] = df_items['Total'].astype(str).str.replace(',', '').str.replace('$', '').astype(float)
    
    total_amount = None
    total_patterns = [
        r'Total:\s*\$([\d,]+(?:\.\d{2})?)',                  
        r'₹₹(\d)(\d)(\d)(\d)(\d)(\d)\.\.(\d)(\d)(\d)(\d)',
        r'TTOOTTAALL\s*₹\s*([\d,]+(?:\.\d{2})?)',
        r'BALANCE DUE[^\d]*₹₹?\s*([\d,]+(?:\.\d{2})?)', 
        r'₹₹([\d,]+(?:\.\d{2})?)',  
        r'Total:?\s*[₹$]\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'Total\s*\$(\d+(?:\.\d{2})?)',
        r'TOTAL\s*₹([\d,]+(?:\.\d{2})?)',
    ]
    
    for pattern in total_patterns:
        for text_version in [invoice_text, cleaned_text]:
            match = re.search(pattern, text_version, re.IGNORECASE)
            if match:
                if len(match.groups()) == 10:             
                    total_amount = f"{match.group(1)}{match.group(4)}{match.group(5)}.{match.group(7)}{match.group(8)}"
                else:
                    total_amount = match.group(1).replace(',', '')
                break
        if total_amount:
            break
    
    if not total_amount:
        print("[DEBUG] Total amount not found, calculating from items or using fallback")
        if not df_items.empty:
            total_amount = str(df_items['Total'].sum())
        else:
            total_amount = '0.00'  # Fallback value
    
    try:
        total_amount_float = float(total_amount)
    except (ValueError, TypeError):
        print("[DEBUG] Could not convert total amount to float, using 0.00")
        total_amount_float = 0.00
    
    print(f"[DEBUG] Final parsed values - Invoice: {invoice_number}, Date: {date}, Sender: {sender_info}, Currency: {currency}")
    
    from datetime import datetime
    
    return {
        'invoice_number': invoice_number or "UNKNOWN",
        'date': date or datetime.now().strftime('%Y-%m-%d'),
        'sender_info': sender_info or "Unknown Sender",
        'billed_to': billed_to or "Customer",
        'address': address or "N/A",
        'items': df_items,
        'total_amount': total_amount_float,
        'currency': currency
    }

def process_text_files_to_data(text_folder=None, output_folder=None, db=None):
    if text_folder is None:
        text_folder = os.path.join(get_workspace_dir(), "extracted_text")
    if output_folder is None:
        output_folder = os.path.join(get_workspace_dir(), "parsed_data")
        
    if not os.path.exists(text_folder):
        return {'error': 'Text folder not found'}
    
    os.makedirs(output_folder, exist_ok=True)
    
    processing_results = {
        'successful_parses': [],
        'failed_parses': [],
        'total_processed': 0
    }
    
    text_files = [f for f in os.listdir(text_folder) if f.endswith('.txt')]
    processing_results['total_processed'] = len(text_files)

    for text_file in text_files:
        text_path = os.path.join(text_folder, text_file)
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                invoice_text = f.read()
                
            parsed_data = parse_invoice_data(invoice_text)
            invoice_id = None
            if db:
                original_pdf_filename = text_file.replace('_extracted.txt', '.pdf').split('_', 1)[-1]
                invoice_id = db.log_invoice_data(parsed_data, original_pdf_filename)
                
                if not invoice_id:
                    print(f"[DEBUG] Skipped file saving for {text_file} due to DB log failure.")
                    processing_results['failed_parses'].append({
                        'text_file': text_path,
                        'error': 'Failed to log to database (likely a duplicate invoice).'
                    })
                    continue

            json_filename = os.path.splitext(text_file)[0] + '_parsed.json'
            json_path = os.path.join(output_folder, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'invoice_number': parsed_data['invoice_number'],
                    'date': parsed_data['date'],
                    'sender_info': parsed_data['sender_info'],
                    'billed_to': parsed_data['billed_to'],
                    'address': parsed_data['address'],
                    'total_amount': parsed_data['total_amount'],
                    'items': parsed_data['items'].to_dict('records') if not parsed_data['items'].empty else []
                }, f, indent=2)
            
            # Save CSV for items if any
            csv_path = None
            if not parsed_data['items'].empty:
                csv_filename = os.path.splitext(text_file)[0] + '_items.csv'
                csv_path = os.path.join(output_folder, csv_filename)
                parsed_data['items'].to_csv(csv_path, index=False)

            processing_results['successful_parses'].append({
                'text_file': text_path,
                'json_file': json_path,
                'csv_file': csv_path,
                'invoice_number': parsed_data['invoice_number'],
                'database_id': invoice_id 
            })
            
        except Exception as e:
            processing_results['failed_parses'].append({
                'text_file': text_path,
                'error': str(e)
            })
            
    return processing_results

def parse_all_invoices(email_object: imaplib.IMAP4_SSL, extract_text=True, parse_data=True, db=None):
    results = process_downloaded_invoices(email_object, extract_text)

    if parse_data and extract_text and results.get('extraction_results'):
        if results['extraction_results']['successful_extractions']:
            parsing_results = process_text_files_to_data(db=db)
            results['parsing_results'] = parsing_results
            try:
                parsed_invoices_file = os.path.join(get_workspace_dir(), "parsed_invoices.json")
                with open(parsed_invoices_file, 'r') as f:
                    parsed_invoices = json.load(f)
            except FileNotFoundError:
                parsed_invoices = []
            for invoice in parsed_invoices:
                text_file = invoice.get('text_file', '')
                if text_file:
                    text_basename = os.path.splitext(os.path.basename(text_file))[0]
                    for success in parsing_results['successful_parses']:
                        if text_basename in success['text_file']:
                            invoice['data_parsed'] = True
                            invoice['parsed_json'] = success['json_file']
                            invoice['parsed_csv'] = success.get('csv_file')
                            invoice['parsing_date'] = datetime.now().strftime("%d-%b-%Y")
                            print(f"[DEBUG] Invoice parsed and logged: {text_file}")
                            break
                    else:
                        for failure in parsing_results['failed_parses']:
                            if text_basename in failure['text_file']:
                                invoice['data_parsed'] = False
                                invoice['parsing_error'] = failure['error']
                                print(f"[DEBUG] Invoice parsing failed: {text_file}, error={failure['error']}")
                                break
            with open(parsed_invoices_file, 'w') as f:
                json.dump(parsed_invoices, f, indent=2)
    
    return results

def process_old_invoices(db):
    if not db:
        return "No database connection"
    
    workspace_dir = get_workspace_dir()
    extracted_text_dir = os.path.join(workspace_dir, "extracted_text")
    parsed_data_dir = os.path.join(workspace_dir, "parsed_data")
    
    if not os.path.exists(extracted_text_dir):
        return "No extracted text directory found"
    
    text_files = [f for f in os.listdir(extracted_text_dir) if f.endswith('_extracted.txt')]
    
    if not text_files:
        return "No extracted text files found to retry"
    
    retry_count = 0
    success_count = 0
    error_count = 0
    
    for text_file in text_files:
        try:

            base_name = text_file.replace('_extracted.txt', '')
            json_file = f"{base_name}_extracted_parsed.json"
            json_path = os.path.join(parsed_data_dir, json_file)
            
            if os.path.exists(json_path):

                with open(json_path, 'r') as f:
                    parsed_data = json.load(f)

                invoice_number = parsed_data.get('invoice_number')
                if invoice_number:
 
                    db.cursor.execute("SELECT id FROM invoices WHERE invoice_number = %s", (invoice_number,))
                    existing = db.cursor.fetchone()
                    
                    if existing:
                        print(f"[DEBUG] Invoice {invoice_number} already exists in database, skipping")
                        continue

                if 'items' in parsed_data and isinstance(parsed_data['items'], list):
                    items_df = pd.DataFrame(parsed_data['items'])
                    parsed_data['items'] = items_df

                invoice_id = db.log_invoice_data(parsed_data, text_file)
                
                if invoice_id:
                    success_count += 1
                    print(f"[DEBUG] Successfully retried and logged: {text_file} -> ID: {invoice_id}")
                else:
                    error_count += 1
                    print(f"[DEBUG] Failed to retry log: {text_file}")
                
                retry_count += 1
                
            else:
                text_path = os.path.join(extracted_text_dir, text_file)
                try:
                    with open(text_path, 'r', encoding='utf-8') as f:
                        text_content = f.read()
                    
                    parsed_data = parse_invoice_data(text_content)
                    
                    if parsed_data:
                        invoice_id = db.log_invoice_data(parsed_data, text_file)
                        
                        if invoice_id:
                            success_count += 1
                            print(f"[DEBUG] Successfully reparsed and logged: {text_file} -> ID: {invoice_id}")
                            
                            if 'items' in parsed_data and hasattr(parsed_data['items'], 'to_dict'):
                                parsed_data_copy = parsed_data.copy()
                                parsed_data_copy['items'] = parsed_data['items'].to_dict('records')
                            else:
                                parsed_data_copy = parsed_data
                            
                            os.makedirs(parsed_data_dir, exist_ok=True)
                            with open(json_path, 'w') as f:
                                json.dump(parsed_data_copy, f, indent=2)
                        else:
                            error_count += 1
                            print(f"[DEBUG] Failed to log reparsed invoice: {text_file}")
                    else:
                        error_count += 1
                        print(f"[DEBUG] Failed to reparse: {text_file}")
                        
                    retry_count += 1
                    
                except Exception as e:
                    error_count += 1
                    print(f"[DEBUG] Error reparsing {text_file}: {e}")
                    
        except Exception as e:
            error_count += 1
            print(f"[DEBUG] Error processing {text_file}: {e}")
    
    if retry_count == 0:
        return "No invoices found to retry"
    
    return f"Retry completed: {success_count} successful, {error_count} failed out of {retry_count} total attempts"

def export_invoices_to_excel(db, output_file=None):
    """
    Export invoices and invoice items from database to Excel file with detailed item-level data
    """
    if output_file is None:
        output_file = os.path.join(get_workspace_dir(), "invoices.xlsx")
    
    if not db:
        return "Database is not connected."
    
    # Handle case where file dialog was cancelled
    if not output_file:
        return "Export cancelled by user."
    
    try:
        # Get detailed export data from database
        detailed_data = db.get_detailed_export_data()
        
        if not detailed_data:
            return "Error retrieving data from database."
        
        if not detailed_data:
            return "No invoices found to export."
        
        # Convert to DataFrame
        detailed_df = pd.DataFrame(detailed_data)
        
        print(f"[DEBUG] Export data - Total rows: {len(detailed_df)}")
        
        # Clean up and format the DataFrame
        if not detailed_df.empty:
            # Format dates - handle None/NULL values properly
            if 'Date' in detailed_df.columns:
                detailed_df['Date'] = pd.to_datetime(detailed_df['Date'], errors='coerce')
                # Format as date string for better Excel display
                detailed_df['Date'] = detailed_df['Date'].dt.strftime('%Y-%m-%d')
                detailed_df['Date'] = detailed_df['Date'].replace('NaT', '')
            
            # Format monetary values
            for col in ['Unit_Price', 'Total_Price']:
                if col in detailed_df.columns:
                    detailed_df[col] = pd.to_numeric(detailed_df[col], errors='coerce').round(2)
            
            # Format quantity
            if 'Item_Quantity' in detailed_df.columns:
                detailed_df['Item_Quantity'] = pd.to_numeric(detailed_df['Item_Quantity'], errors='coerce')
            
            # Clean up text fields - remove extra whitespace and handle None values
            text_columns = ['Invoice_No', 'Receiver', 'Receiver_Address', 'Sender', 'Sender_Address', 'Item_Name']
            for col in text_columns:
                if col in detailed_df.columns:
                    detailed_df[col] = detailed_df[col].astype(str).str.strip()
                    detailed_df[col] = detailed_df[col].replace('None', '')
                    detailed_df[col] = detailed_df[col].replace('nan', '')
        
        # Write to Excel with single sheet
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main export sheet with detailed item data
            detailed_df.to_excel(writer, sheet_name='Invoice Details', index=False)
            
            # Format the sheet
            worksheet = writer.sheets['Invoice Details']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Apply header formatting
            for cell in worksheet[1]:
                cell.font = cell.font.copy(bold=True)
        
        return f"Successfully exported {len(detailed_df)} invoice items to {output_file}"
        
    except Exception as e:
        return f"Error exporting to Excel: {str(e)}"
