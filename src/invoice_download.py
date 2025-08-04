import imaplib
import email
import os

def login(email_address, password):
    imap_server = "imap.gmail.com"
    em = imaplib.IMAP4_SSL(imap_server)
    em.login(email_address, password)
    return em

def get_credentials():
    if os.path.exists("credentials.txt"):
        with open("credentials.txt", "r") as f:
            lines = f.readlines()
            email_address = lines[0].split('=')[1].strip()
            password = lines[1].split('=')[1].strip().strip('\"')
            return email_address, password
    else:
        email_address = input("Enter your email address: ")
        password = input("Enter your password: ")

def invoice_download(em : imaplib.IMAP4_SSL):
    em.select("INBOX")
    status, email_ids = em.search(None, "SUBJECT Invoice")
    email_ids = email_ids[0].split()
    pdf_paths = []
    for email_id in email_ids:
        status, msg_data = em.fetch(email_id, "(RFC822)")
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                filename = part.get_filename()
                os.makedirs('attachments', exist_ok=True)
                pdf_paths.append(f'attachments/{filename}')
                with open(f'attachments/{filename}', 'wb') as f:
                    f.write(part.get_payload(decode=True))
                    f.close()
    return pdf_paths

if __name__ == '__main__':
    email_address, password = get_credentials()
    em = login(email_address, password)
    pdf_files = invoice_download(em)
    print("Downloaded PDF files:")
    for pdf in pdf_files:
        print(pdf)

    