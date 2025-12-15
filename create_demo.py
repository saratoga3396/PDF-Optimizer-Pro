import fitz
import os

def create_demo_pdf(path):
    doc = fitz.open()

    # Page 1: Clear Title and Date to demonstrate Renaming
    # This simulates a document that needs renaming.
    page1 = doc.new_page()
    page1.insert_text((50, 100), "Project Beta Proposal", fontsize=30, color=(0, 0, 1))
    page1.insert_text((50, 150), "Submission Date: 2025/01/15", fontsize=14)
    page1.insert_text((50, 300), "This page tests the renaming feature.", fontsize=12)

    # Page 2: Blank Page to demonstrate Removal
    page2 = doc.new_page()

    # Page 3: Rotated Text to demonstrate Rotation
    # We rotate the text 90 degrees so it looks sideways if the page is upright (0 rotation)
    # The tool should detect this and rotate the page data to match.
    # Note: Text rotation in PyMuPDF is relative. 
    # If we want to simulate a "scanned sideways" page, we usually have an image that is wide.
    # For text, we'll just write it rotated.
    page3 = doc.new_page()
    page3.insert_text((300, 300), "This page should be rotated.", rotate=90, fontsize=20)
    
    doc.save(path)
    print(f"Created {path}")

if __name__ == "__main__":
    if not os.path.exists("samples"):
        os.makedirs("samples")
    create_demo_pdf("samples/DEMO_FILE.pdf")
