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
import re
import json
import PyPDF2
import docx
from pdf2image import convert_from_path
import numpy as np
# import pytesseract

import magic

import easyocr
import spacy

def get_mime_type(file_path: str) -> str:
    """
        @description: Get the mime type of the file.
    """
    mime = magic.Magic()
    descriptive_mime_type = mime.from_file(file_path)
    print(f"Descriptive mime type is {descriptive_mime_type} for file {file_path}")
    return map_descriptive_to_mime(descriptive_mime_type)

def map_descriptive_to_mime(descriptive_mime_type: str) -> str:
    """
        @description: Map descriptive mime types to standard mime types.
    """
    # Define a dictionary to map descriptive mime types to standard mime types
    mime_mapping = {
        'PDF document, version 1.4': 'application/pdf',
        'PDF document, version 1.5': 'application/pdf',
        'PDF document, version 1.6': 'application/pdf',
        'PDF document, version 1.7': 'application/pdf',
        'PDF document, version 1.8': 'application/pdf',
        # ... add other mappings as needed
        'Microsoft Word 2007+': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    }
    # Get the standard mime type from the mapping, or default to 'application/octet-stream' if not found
    return mime_mapping.get(descriptive_mime_type, 'application/octet-stream')


def clean_text_from_pdf(text: str) -> str:
    """
    Cleans the extracted text from a PDF by removing unwanted characters while preserving paragraph structure and accented characters.
    
    Args:
    - text (str): The text extracted from a PDF.
    
    Returns:
    - str: The cleaned text with preserved paragraph structure.
    """
    # Remove unwanted characters but preserve accented characters and common punctuation
    text = re.sub(r'[^\w\s.,!?;:\'\”\“\(\)\-\n\u00C0-\u00FF]', '', text, flags=re.UNICODE)
    
    # Normalize space characters and remove any form of multiple whitespaces
    text = re.sub(r'\s+', ' ', text, flags=re.UNICODE)
    
    # Replace multiple newlines with two newlines (considered as paragraph break)
    # Assuming that a paragraph is separated by two or more newline characters
    text = re.sub(r'(\n\s*){2,}', '\n\n', text, flags=re.UNICODE)
    
    # Remove extra spaces at the beginning and end of each line
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines]

    # Rejoin the cleaned lines with a single newline character
    text = '\n'.join(cleaned_lines)
    
    # Replace single newlines within paragraphs with a space
    text = text.replace('\n', ' ')
    
    # Reintroduce the double newline characters for paragraph breaks
    text = text.replace(' \n\n ', '\n\n')
    
    return text.strip()  # Remove any leading or trailing whitespace that may have been left over

def merge_split_words_spacy( text, nlp ):
    # Process the text with SpaCy
    doc = nlp(text)

    # Create a list to hold the processed tokens
    new_tokens = []

    # Iterate over the tokens
    skip_next = False
    for i, token in enumerate(doc):
        # If we're skipping this token (because we merged it with the previous one), continue
        if skip_next:
            skip_next = False
            continue

        # If this token is not a known word, try merging it with the next token
        if not token.is_alpha and i < len(doc) - 1:
            merged_word = token.text + doc[i+1].text
            merged_doc = nlp(merged_word)

            # If the merged word is recognized, use it and skip the next token
            if merged_doc[0].is_alpha:
                new_tokens.append(merged_word)
                skip_next = True
            else:
                new_tokens.append(token.text)
        else:
            new_tokens.append(token.text)

    # Join the tokens back into a single string
    return ' '.join(new_tokens)

def get_file_name_from_path(file_path: str) -> str :
    return os.path.splitext(os.path.basename(file_path))[0]

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

        reader_ocr = easyocr.Reader(['en'])
        nlp = spacy.load("en_core_web_sm")

        entries = []

        # Extract text from each page
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()

            # If no text is found for the page, it might be a scanned pdf
            if not text:
                image = np.array(convert_from_path(file_path, first_page=page_num, last_page=page_num)[0])
                text = ' '.join(reader_ocr.readtext(image, detail=0))

            text = clean_text_from_pdf( text )
            text = merge_split_words_spacy( text, nlp )
            
 
            # Split text into paragraphs and create entries
            paragraphs = [p for p in text.split("\n\n") if p.strip()]
            entries.extend([{"file_mimetype": "application/pdf", "page": page_num, "index": i, "file_name": get_file_name_from_path(file_path), "paragraph": p} for i, p in enumerate(paragraphs)])

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
    return [{"file_mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "page": 0, "index": i, "file_name": get_file_name_from_path(file_path), "paragraph": p.text} for i, p in enumerate(doc.paragraphs) if p.text]

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
        return [{"file_mimetype": mimetype, "page": 0, "index": i, "file_name": get_file_name_from_path(file_path), "paragraph": p} for i, p in enumerate(paragraphs) if p.strip()]

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
        raise ValueError(f"File type {mimetype} not supported for file {file_path}")

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

            try :

                entries = extract_paragraphs_from_any(file_path, mimetype)
                
                for entry in entries:
                    results.append(entry)

            except Exception as error: 
                
                print("An exception occurred:", error)
                continue
    
    return results


if __name__ == '__main__':  

    paragraph_file = "/home/ubuntu/working-repositories/haliro/test_data/indexes/v01_paragraphs.json"

    paragraphs = extract_paragraphs_from_directory("/home/ubuntu/working-repositories/haliro/test_data/test_docs/")

    # Saving the dictionary to a file in JSON format
    with open(paragraph_file, 'w') as f:
        json.dump(paragraphs, f, indent=4)

    # print (paragraphs)
