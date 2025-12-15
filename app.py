from flask import Flask, render_template, request, send_file, jsonify
import os
import shutil
import fitz
from pdf_processor import PDFProcessor
from utils import is_generic_filename, sanitize_filename
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
app.config['PROCESSED_FOLDER'] = '/tmp/processed_web'
app.secret_key = 'supersecretkey'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

processor = PDFProcessor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        # Save uploaded file
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(input_path)
        
        try:
            # Process the file
            doc = fitz.open(input_path)
            out_doc = fitz.open()
            
            # Get options
            make_searchable = request.form.get('searchable') == 'true'
            enhance_image = request.form.get('enhance') == 'true'
            
            needs_rename = is_generic_filename(file.filename)
            new_title = None
            new_date = None
            pages_kept = 0
            
            for i, page in enumerate(doc):
                # Blank Page Removal
                if processor.detect_blank_page(page):
                    continue
                
                # Auto-Rotation
                rotation = processor.fix_orientation(page)
                if rotation != 0:
                    page.set_rotation(rotation)
                
                # Make Searchable (OCR) or just copy
                target_page = page
                ocr_doc_ref = None # Keep reference to prevent GC if needed
                
                if make_searchable:
                    ocr_doc = processor.convert_to_searchable_pdf(page, enhance=enhance_image)
                    if ocr_doc:
                        ocr_doc_ref = ocr_doc
                        target_page = ocr_doc[0]
                        out_doc.insert_pdf(ocr_doc)
                    else:
                        # Fallback if OCR fails
                        out_doc.insert_pdf(doc, from_page=i, to_page=i)
                else:
                    out_doc.insert_pdf(doc, from_page=i, to_page=i)

                # Metadata (from first kept page)
                # Now we use 'target_page' which might be the OCR'd clean page
                if pages_kept == 0 and needs_rename:
                    t, d = processor.extract_metadata_for_rename(target_page)
                    if t: new_title = t
                    if d: new_date = d
                    
                pages_kept += 1
            
            if pages_kept == 0:
                 return jsonify({'error': 'All pages were blank and removed.'}), 400

            # Determine Output Name
            name, ext = os.path.splitext(file.filename)
            final_name = f"{name}_processed{ext}"
            
            if needs_rename and new_title:
                sanitized = sanitize_filename(new_title)
                if new_date:
                    final_name = f"{sanitized}_{new_date}{ext}"
                else:
                    final_name = f"{sanitized}{ext}"
            
            output_filename = final_name
            output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
            out_doc.save(output_path)
            out_doc.close()
            doc.close()
            
            # Clean up input
            os.remove(input_path)
            
            return jsonify({
                'success': True,
                'filename': output_filename,
                'download_url': f'/download/{output_filename}'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['PROCESSED_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5555)
