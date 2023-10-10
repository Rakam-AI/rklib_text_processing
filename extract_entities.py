'''
    dependence :
        pip install PyPDF2 docx pdf2image pytesseract
    usage : 
        python main.py .....l...

'''

# TODO : Ajouter des fichiers test
# TODO : Add .txt , .md  , .docx files

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

def extract_paragraphs_from_any(file_path):
    _, file_extension = os.path.splitext(file_path)
    
    if file_extension == ".pdf":
        return extract_from_pdf(file_path)
    elif file_extension == ".docx":
        return extract_from_docx(file_path)
    elif file_extension in [".txt", ".md"]:
        return extract_from_txt_md(file_path)
    else:
        print(f"File type {file_extension} not supported")
        return []

def extract_paragraphs_from_directory(directory):
    results = []
    for subdir, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(subdir, file)
            paragraphs = extract_paragraphs(file_path)
            
            for p in paragraphs:
                entry = {
                    "file_name": file,
                    "paragraph": p
                }
                results.append(entry)
    
    return results

if __name__ == '__main__':

    None