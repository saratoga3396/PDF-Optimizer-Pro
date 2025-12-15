import fitz
import sys

filepath = sys.argv[1]
try:
    doc = fitz.open(filepath)
    text = ""
    for page in doc:
        text += page.get_text()
    
    print(f"--- Extracted Text form {filepath} ---")
    print(text.strip())
    
    if "Tanpopo" in text:
        print("SUCCESS: Searchable text found.")
    else:
        print("FAILURE: No expected text found.")
except Exception as e:
    print(f"Error: {e}")
