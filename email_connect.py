import email.message
import imaplib
import email
import getpass
import PyPDF2
import io

class EmailConnector:
    def __init__(self):
        self.__email_address : str
        self.__password : str
        self.__imap_server : str
        self.__mail = None
        self.__is_connected = False

    def connect(self, email_address: str, password: str, imap_server: str) -> bool:
        self.__email_address = email_address
        self.__password = password
        self.__imap_server = imap_server
        try:
            self.__mail = imaplib.IMAP4_SSL(self.__imap_server)
            self.__mail.login(self.__email_address, self.__password)
            self.__is_connected = True
            return True
        except imaplib.IMAP4.error as e:
            error_message = str(e).lower()
            print(f"✗ IMAP Error: {e}")
            if "authentication failed" in error_message or "invalid credentials" in error_message:
                self.__show_authentication_help()
            return False
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
        
    def __show_authentication_help(self):
        if "gmail.com" in self.__imap_server:
            print("\nGmail Authentication Help:")
            print("1. Make sure you have 2-Factor Authentication enabled")
            print("2. Generate an App Password:")
            print("   - Go to: https://myaccount.google.com/apppasswords")
            print("   - Select 'Mail' and generate a password")
            print("   - Use that 16-character password instead of your regular password")
            print("3. If you don't see App Passwords option, enable 2FA first")
        elif "outlook" in self.__imap_server:
            print("\nOutlook Authentication Help:")
            print("1. Enable 2-Factor Authentication")
            print("2. Use an App Password or enable 'Less secure app access'")
        else:
            print(f"\nAuthentication failed for {self.__imap_server}")

    def close_connection(self):
        try:
            if self.__mail and self.__is_connected:
                self.__mail.close()
                self.__mail.logout()
                self.__is_connected = False
        except Exception as e:
            print(f"Error closing connection: {e}")

    def is_connected(self) -> bool:
        return self.__is_connected
    
    def select_folder(self, folder_name: str) -> int:
        try:
            status, messages = self.__mail.select(folder_name)
            if status == 'OK':
                return int(messages[0])
            else:
                print(f"Failed to select folder {folder_name}")
                return 0
        except Exception as e:
            print(f"Error selecting folder: {e}")
            return 0
    
    def search_emails(self, search_criteria: str) -> list:
        try:
            status, email_ids = self.__mail.search(None, search_criteria)
            if status == 'OK':
                return email_ids
            else:
                print(f"Search failed with status: {status}")
                return []
        except Exception as e:
            print(f"Error searching emails: {e}")
            return []
    
    def fetch_email(self, email_id: bytes) -> email.message.EmailMessage:
        try:
            status, msg_data = self.__mail.fetch(email_id, "(RFC822)")
            if status == 'OK' and msg_data:
                email_body = msg_data[0][1]
                return email.message_from_bytes(email_body)
            return None
        except Exception as e:
            print(f"Error fetching email {email_id}: {e}")
            return None

class InvoiceEmailFetcher:
    def __init__(self , email : EmailConnector):
        self.__email = email

    def fetch_invoice_emailIds(self) -> list:
        if not self.__email.is_connected():
            print("Not connected to email server")
            return []
        self.__email.select_folder("INBOX")
        # Search for emails with "invoice" in subject or body
        search_result = self.__email.search_emails('SUBJECT "invoice"')
        if search_result and search_result[0]:
            return search_result[0].split()
        # else:
        #     # Try alternative search for invoice-related emails
        #     search_result = self.__email.search_emails('TEXT "invoice"')
        #     if search_result and search_result[0]:
        #         return search_result[0].split()
        return []

    def fetch_email(self, email_id: bytes) -> email.message.EmailMessage:
        return self.__email.fetch_email(email_id)
    
class EmailAttachmentManager:
    def __init__(self, storage_folder: str):
        self.storage_folder = storage_folder

    def loadPDFAttachments(self, email_message: email.message.EmailMessage) -> list:
        pdf_contents = []
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            filename = part.get_filename()
            if not filename or not filename.lower().endswith('.pdf'):
                continue
            try:
                pdf_data = part.get_payload(decode=True)
                pdf_file = io.BytesIO(pdf_data)
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text_content = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content += page.extract_text()
                pdf_info = {
                    'filename': filename,
                    'num_pages': len(pdf_reader.pages),
                    'text_content': text_content,
                    'metadata': pdf_reader.metadata if hasattr(pdf_reader, 'metadata') else {}
                }
                pdf_contents.append(pdf_info)
            except Exception as e:
                print(f"Error processing PDF {filename}: {e}")
                continue
        return pdf_contents
    
def displayPDFContents(pdf_contents: list):
    if not pdf_contents:
        print("No PDF attachments found.")
        return
    
    for pdf in pdf_contents:
        print(f"PDF Filename: {pdf['filename']}")
        print(f"Number of Pages: {pdf['num_pages']}")
        print(f"Metadata: {pdf['metadata']}")
        print("Text Content:")
        print(pdf['text_content'][:500])  # Display first 500 characters
        print("-" * 40)


if __name__ == "__main__":
    email_address = "Your Email Address"
    password = "Your Email Password or APP Password"
    imap_server = "imap.gmail.com"
    email_connector = EmailConnector()
    if email_connector.connect(email_address, password, imap_server):
        invoice_fetcher = InvoiceEmailFetcher(email_connector)
        email_ids = invoice_fetcher.fetch_invoice_emailIds()
        
        if not email_ids:
            print("No invoice emails found.")
        else:
            for email_id in email_ids:
                email_message = invoice_fetcher.fetch_email(email_id)
                if email_message:
                    attachment_manager = EmailAttachmentManager("stored_emails")
                    pdf_contents = attachment_manager.loadPDFAttachments(email_message)
                    displayPDFContents(pdf_contents)
        
        email_connector.close_connection()
    else:
        print("Failed to connect to email server.")
        email_connector.close_connection()
        print("Please check your email and password/app password.")


