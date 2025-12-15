import time
import os
import shutil
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from main import process_single_pdf
from pdf_processor import PDFProcessor

# Configuration
INPUT_DIR = "input"
PROCESSED_DIR = "processed"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFHandler(FileSystemEventHandler):
    def __init__(self, processor):
        self.processor = processor

    def on_created(self, event):
        if event.is_directory:
            return
        
        filename = os.path.basename(event.src_path)
        if not filename.lower().endswith(".pdf"):
            return

        # Wait briefly for file write to complete (simple debounce)
        time.sleep(1)
        
        logger.info(f"New PDF detected: {filename}")
        self.process_file(event.src_path)

    def process_file(self, filepath):
        try:
            # We need to process the file and save the result to PROCESSED_DIR
            # main.py's logic saves in-place or renames. We want to adapt it slightly.
            # Instead of calling main.py logic directly which affects current dir, 
            # let's adapt it to save to PROCESSED_DIR.
            
            # Since process_single_pdf in main.py is designed to save alongside original,
            # we should move the file to a temp location or handle the output path manually.
            # actually main.py doesn't allow specifying output dir easily yet.
            # Let's import the processor logic but handle I/O here for better control
            # or modify main.py? 
            # Modifying main.py to allow output_dir is best practice, but for now I will just
            # move the input file to a 'processing' stage or rely on the fact that process_single_pdf
            # writes to the same folder.
            
            # Better approach for this watcher:
            # 1. Process the file found in INPUT_DIR
            # 2. Save the result directly to PROCESSED_DIR
            # 3. Delete or archive the original from INPUT_DIR
            
            input_path = filepath
            filename = os.path.basename(filepath)
            
            # Use the processor directly
            doc = import_fitz().open(input_path)
            out_doc = import_fitz().open()
            
            needs_rename = import_utils().is_generic_filename(filename)
            new_title = None
            new_date = None
            pages_kept = 0
            
            for i, page in enumerate(doc):
                if self.processor.detect_blank_page(page):
                     continue
                
                if pages_kept == 0 and needs_rename:
                    t, d = self.processor.extract_metadata_for_rename(page)
                    if t: new_title = t
                    if d: new_date = d
                    
                rotation = self.processor.fix_orientation(page)
                if rotation != 0:
                    page.set_rotation(rotation)
                
                out_doc.insert_pdf(doc, from_page=i, to_page=i)
                pages_kept += 1
            
            if pages_kept == 0:
                logger.warning(f"All pages removed. Skipping: {filename}")
                # Optional: Delete input?
                return

            # Determine Output Name
            name, ext = os.path.splitext(filename)
            final_name = filename 
            
            if needs_rename and new_title:
                sanitized = import_utils().sanitize_filename(new_title)
                if new_date:
                    final_name = f"{sanitized}_{new_date}{ext}"
                else:
                    final_name = f"{sanitized}{ext}"
                    
            output_path = os.path.join(PROCESSED_DIR, final_name)
            
            # Save
            out_doc.save(output_path)
            logger.info(f"Processed and saved to: {output_path}")
            out_doc.close()
            doc.close()
            
            # Clean up input file
            os.remove(input_path)
            logger.info(f"Removed original file from input.")

        except Exception as e:
            logger.error(f"Error processing {filepath}: {e}")

# Helpers to avoid global import issues if dependencies change
def import_fitz():
    import fitz
    return fitz

def import_utils():
    import utils
    return utils

def start_watching():
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)
        
    processor = PDFProcessor()
    event_handler = PDFHandler(processor)
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=False)
    observer.start()
    
    logger.info(f"Monitoring '{INPUT_DIR}' for PDF files...")
    logger.info(f"Processed files will be saved to '{PROCESSED_DIR}'")
    logger.info("Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watching()
