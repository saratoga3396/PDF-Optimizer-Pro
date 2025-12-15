import fitz
import os

def create_sample_pdf(path):
    doc = fitz.open()

    # Page 1: Title and Date (Generic Name test)
    page1 = doc.new_page()
    # Large Title
    page1.insert_text((50, 100), "Project Alpha Report", fontsize=30)
    # Date
    page1.insert_text((50, 150), "作成日: 2024年05月20日", fontsize=12, fontname="japan") 
    # Note: PyMuPDF default fonts might not support Japanese characters perfectly without specific font loading,
    # but for regex detection of numbers it might be okay, or I'll use ISO format for safety if font fails.
    # Let's use ISO date to be safe with default fonts: "Date: 2024-05-20"
    page1.insert_text((50, 200), "Date: 2024-05-20", fontsize=12)

    # Page 2: Blank (Visual emptiness)
    page2 = doc.new_page()
    # Literally nothing added.

    # Page 3: Rotated Text (Simulate Scanned Rotation)
    # We want top-down text (90 degree visual rotation)
    page3 = doc.new_page()
    # To simulate a scan that needs 90 degree CW rotation to be upright:
    # The text on the page should be written such that it looks like it's on its side.
    # If I write text at 270 degrees, it reads from bottom to top. 
    # If the user scans a paper in landscape, it might appear sideways.
    # Let's write text normally, but set the page rotation metadata to 0. 
    # Wait, if I want to test "fix_orientation", I need to simulate a "badly rotated" page.
    # Case A: PDF Rotation=0, but Image Content is sideways. (Common in raw scans)
    # Case B: PDF Rotation=90, Image Content is upright relative to that. (Already correct)
    
    # We want Case A. 
    # So I will insert an image or text that is rotated.
    # Inserting text with `rotate=90`.
    page3.insert_text((300, 300), "This text is sideways", rotate=90, fontsize=20)
    
    doc.save(path)
    print(f"Created {path}")

if __name__ == "__main__":
    if not os.path.exists("samples"):
        os.makedirs("samples")
    create_sample_pdf("samples/IMG_001.pdf")
