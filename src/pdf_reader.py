
import os
import pdfplumber
from pathlib import Path

pdf_paths = ["attachments/Invoice 1.pdf"]
output_folder = "extracted_text"
for pdf_path in pdf_paths:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text_content = ""
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                print(page_text)
                if page_text:
                    text_content += f"--- Page {page_num + 1} ---\n"
                    text_content += page_text + "\n\n"
            if text_content.strip():
                output_file = Path(output_folder) / f"{Path(pdf_path).stem}_extracted.txt"
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                print(f"Text extracted and saved to {output_file}")
            else:
                print("No text content extracted.")
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
    print()

