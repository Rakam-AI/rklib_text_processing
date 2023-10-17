'''
    requirement: 
        PyPDF2==3.0.1
        pdf2image==1.16.3
        python-docx==1.0.0
        pytesseract==0.3.10
        python-magic==0.4.27
    usage : 
        python main.py .....l...

'''

# TODO : Ajouter des fichiers test
# TODO : Add .txt , .md  , .docx files

import os
import json
import PyPDF2
import docx
from pdf2image import convert_from_path
import pytesseract

import magic

def get_mime_type(file_path: str) -> str:
    """
        @description: Get the mime type of the file.
    """
    mime = magic.Magic()
    mime_type = mime.from_file(file_path)
    if mime_type == 'empty':
        mime_type = 'application/octet-stream'
    return mime_type

def extract_paragraphs_from_pdf(file_path: str) -> list:
    """
    Extracts paragraphs from a PDF file and returns them as dictionary entries.
    
    Args:
    - file_path (str): The path to the PDF file.
    
    Returns:
    - List[dict]: List of dictionary entries for the paragraphs.
    """
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        entries = []

        # Extract text from each page
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()

            # If no text is found for the page, it might be a scanned pdf
            if not text:
                image = convert_from_path(file_path, first_page=page_num, last_page=page_num)[0]
                text = pytesseract.image_to_string(image)

            # Split text into paragraphs and create entries
            paragraphs = [p for p in text.split("\n\n") if p.strip()]
            entries.extend([{"file_mimetype": "application/pdf", "page_or_index": page_num, "paragraph": p} for p in paragraphs])

        return entries

def extract_paragraphs_from_docx(file_path: str) -> list:
    """
    Extracts paragraphs from a DOCX file and returns them as dictionary entries.
    
    Args:
    - file_path (str): The path to the DOCX file.
    
    Returns:
    - List[dict]: List of dictionary entries for the paragraphs.
    """
    doc = docx.Document(file_path)
    return [{"file_mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "page_or_index": i, "paragraph": p.text} for i, p in enumerate(doc.paragraphs) if p.text]

def extract_paragraphs_from_txt_md(file_path: str, mimetype: str) -> list:
    """
    Extracts paragraphs from a TXT or MD file and returns them as dictionary entries.
    
    Args:
    - file_path (str): The path to the TXT or MD file.
    - mimetype (str): MIME type of the file.
    
    Returns:
    - List[dict]: List of dictionary entries for the paragraphs.
    """
    with open(file_path, 'r') as f:
        paragraphs = f.read().split('\n\n')
        return [{"file_mimetype": mimetype, "page_or_index": i, "paragraph": p} for i, p in enumerate(paragraphs) if p.strip()]

def extract_paragraphs_from_any(file_path: str, mimetype: str) -> list:
    """
    Extract paragraphs from a file based on its MIME type.
    
    Parameters:
    - file_path (str): The path to the file from which to extract paragraphs.
    - mimetype (str): The MIME type of the file.
    
    Returns:
    - list: A list of extracted paragraphs.
    
    Raises:
    - ValueError: If the provided MIME type isn't supported.
    """
    
    # Check if the MIME type corresponds to a PDF file.
    if mimetype == "application/pdf":
        return extract_paragraphs_from_pdf(file_path)
    
    # Check if the MIME type corresponds to a DOCX (Word) file.
    elif mimetype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_paragraphs_from_docx(file_path)
    
    # Check if the MIME type corresponds to a plain text or markdown file.
    elif mimetype in ["text/plain", "text/markdown"]:
        return extract_paragraphs_from_txt_md(file_path, mimetype)
    
    # If the MIME type doesn't match any of the supported types, raise an exception.
    else:
        raise ValueError(f"File type {mimetype} not supported")

def extract_paragraphs_from_directory( directory: str ) -> list:
    """
    Extracts paragraphs from all supported files in a directory and returns them as dictionary entries.
    
    Args:
    - directory (str): The path to the directory containing the files.
    
    Returns:
    - List[dict]: List of dictionary entries for the paragraphs from all files.
    """
    results = []
    for subdir, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(subdir, file)
            mimetype = get_mime_type(file_path)

            entries = extract_paragraphs_from_any(file_path, mimetype)
            
            for entry in entries:
                entry["file_name"] = file  # Add the file name to each entry
                results.append(entry)
    
    return results


if __name__ == '__main__':

    paragraphs = extract_paragraphs_from_directory("./test_data")
    print (paragraphs)
    None
