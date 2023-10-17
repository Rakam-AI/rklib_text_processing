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

def extract_paragraphs_from_pdf(file_path):

    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = [page.extract_text() for page in reader.pages]
        
        # If no text is found, it might be a scanned pdf
        if not any(text):
            images = convert_from_path(file_path)
            text = [pytesseract.image_to_string(img) for img in images]
            
        return text

def extract_paragraphs_from_docx(file_path):
    doc = docx.Document(file_path)
    return [p.text for p in doc.paragraphs if p.text]

def extract_paragraphs_from_txt_md(file_path):
    with open(file_path, 'r') as f:
        return f.read().split('\n\n')

def extract_paragraphs_from_any(file_path: str, mimetype: str):
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
        return extract_paragraphs_from_txt_md(file_path)
    
    # If the MIME type doesn't match any of the supported types, raise an exception.
    else:
        raise ValueError(f"File type {mimetype} not supported")


def extract_paragraphs_from_directory(directory):
    results = []
    for subdir, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(subdir, file)
            paragraphs = extract_paragraphs_from_any(file_path, get_mime_type(file_path))
            
            for p in paragraphs:
                entry = {
                    "file_name": file,
                    "paragraph": p
                }
                results.append(entry)
    
    return results

if __name__ == '__main__':

    paragraphs = extract_paragraphs_from_directory("./test_data")
    print (paragraphs)
    None