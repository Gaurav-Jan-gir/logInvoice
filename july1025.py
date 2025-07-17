import imaplib
import email
from PyPDF2 import PdfReader

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
                pdf_paths.append(f'attachments/{filename}')
                with open(f'attachments/{filename}', 'wb') as f:
                    f.write(part.get_payload(decode=True))
                    f.close()
    return pdf_paths

if __name__ == "__main__":
    email_address = "gaurav.jngira@gmail.com"
    password = "ujyb ufal ebjl muxk"
    imap_server = "imap.gmail.com"
    em = imaplib.IMAP4_SSL(imap_server)
    em.login(email_address, password)
    pdf_paths = invoice_download(em)
    for pdf_path in pdf_paths:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PdfReader(f)
            for page in pdf_reader.pages:
                print(page.extract_text())
    em.close()
    em.logout() 