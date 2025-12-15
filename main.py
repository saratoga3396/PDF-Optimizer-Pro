import os
import sys
import argparse
import fitz
from pdf_processor import PDFProcessor
from utils import is_generic_filename, sanitize_filename
import logging
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_single_pdf(filepath, processor, dry_run=False):
    logger.info(f"Processing: {filepath}")
    
    try:
        doc = fitz.open(filepath)
        out_doc = fitz.open() # Create new PDF
        
        needs_rename = is_generic_filename(os.path.basename(filepath))
        new_title = None
        new_date = None
        
        pages_kept = 0
        
        for i, page in enumerate(doc):
            # 1. Blank Page Removal
            if processor.detect_blank_page(page):
                logger.info(f"  Page {i+1} removed (blank).")
                continue
                
            # 2. Extract Metadata (only from first *kept* page)
            if pages_kept == 0 and needs_rename:
                t, d = processor.extract_metadata_for_rename(page)
                if t: new_title = t
                if d: new_date = d
            
            # 3. Auto-Rotation
            rotation = processor.fix_orientation(page)
            if rotation != 0:
                logger.info(f"  Page {i+1} rotated {rotation} degrees.")
                page.set_rotation(rotation)
                
            # Add to output doc
            out_doc.insert_pdf(doc, from_page=i, to_page=i)
            pages_kept += 1
            
        if pages_kept == 0:
            logger.warning(f"  All pages removed from {filepath}. Skipping save.")
            return

        # Determine output filename
        dirname = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        name, ext = os.path.splitext(filename)
        
        final_name = f"{name}_processed{ext}"
        
        if needs_rename and new_title and new_date:
            sanitized_title = sanitize_filename(new_title)
            final_name = f"{sanitized_title}_{new_date}{ext}"
            logger.info(f"  Proposed new name: {final_name}")
        elif needs_rename and new_title:
             sanitized_title = sanitize_filename(new_title)
             final_name = f"{sanitized_title}{ext}"
             logger.info(f"  Proposed new name: {final_name}")
        
        output_path = os.path.join(dirname, final_name)
        
        if not dry_run:
            out_doc.save(output_path)
            logger.info(f"Saved to: {output_path}")
        else:
            logger.info(f"[DRY RUN] Would save to: {output_path}")
            
    except Exception as e:
        logger.error(f"Failed to process {filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(description="PDF Convenience Tool")
    parser.add_argument("path", help="Path to PDF file or directory")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without saving files")
    
    args = parser.parse_args()
    
    processor = PDFProcessor()
    
    target = args.path
    if os.path.isfile(target):
        if target.lower().endswith(".pdf"):
            process_single_pdf(target, processor, args.dry_run)
    elif os.path.isdir(target):
        for root, _, files in os.walk(target):
            for file in files:
                if file.lower().endswith(".pdf"):
                    process_single_pdf(os.path.join(root, file), processor, args.dry_run)
    else:
        logger.error("Invalid path provided.")

if __name__ == "__main__":
    main()
