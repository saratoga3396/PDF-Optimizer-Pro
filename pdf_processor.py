import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageOps # Added ImageOps
import io
import re
import statistics
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self):
        pass

    def enhance_page_image(self, image):
        """
        Enhances image quality for better OCR (Contrast/Denoise).
        """
        try:
            # Auto Contrast
            if image.mode != 'RGB':
                image = image.convert('RGB')
            enhanced = ImageOps.autocontrast(image, cutoff=2)
            return enhanced
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}")
            return image

    def convert_to_searchable_pdf(self, page, enhance=False):
        """
        Converts a single PDF page to a 1-page searchable PDF document using OCR.
        Returns a fitz.Document object of that single page.
        """
        try:
            # 1. Get high-res image (reduced to 150 for Render memory limits)
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # 2. Enhance if requested
            if enhance:
                img = self.enhance_page_image(img)
            
            # 3. generate PDF with text layer
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension='pdf', lang='jpn+eng')
            
            # 4. Open as fitz doc
            ocr_pdf = fitz.open("pdf", pdf_bytes)
            return ocr_pdf
        except Exception as e:
            logger.error(f"Failed to convert to searchable PDF: {e}")
            return None

    def detect_blank_page(self, page, threshold=99.5):
        """
        Detects if a page is blank based on image statistics.
        Returns True if blank, False otherwise.
        """
        try:
            pix = page.get_pixmap(dpi=72)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Convert to grayscale
            img = img.convert("L")
            
            # Calculate statistics
            # A blank white page will have high mean (near 255) and low stdev
            pixels = list(img.getdata())
            stdev = statistics.stdev(pixels)
            mean = statistics.mean(pixels)
            
            # Criteria: Very uniform (low stdev) and bright (high mean)
            # Adjust these thresholds based on testing
            is_blank = stdev < 5.0 and mean > 250
            
            if is_blank:
                logger.info(f"Page detected as blank: Mean={mean:.2f}, Stdev={stdev:.2f}")
            
            return is_blank
        except Exception as e:
            logger.error(f"Error checking blank page: {e}")
            return False

    def fix_orientation(self, page):
        """
        Detects orientation and returns the rotation angle (0, 90, 180, 270).
        """
        try:
            pix = page.get_pixmap(dpi=150) # Higher DPI for OCR
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            osd = pytesseract.image_to_osd(img)
            rotation = int(re.search(r'(?<=Rotate: )\d+', osd).group(0))
            
            if rotation != 0:
                logger.info(f"Detected rotation: {rotation}")
                return rotation
            return 0
        except Exception as e:
            logger.warning(f"OSD failed, assuming 0 rotation. Error: {e}")
            return 0

    def extract_metadata_for_rename(self, page):
        """
        Extracts potential title and date from the first page.
        Uses OCR with layout analysis if text layer is missing.
        """
        text_content = page.get_text()
        
        candidates = [] # list of {text, size}
        full_text_for_date = text_content
        
        # Check if we need OCR (insufficient text)
        ocr_height = None
        
        if len(text_content.strip()) < 50:
            logger.info("  Low text content detected. Running OCR with layout analysis...")
            try:
                pix = page.get_pixmap(dpi=150)
                ocr_height = pix.height
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Get detailed data (box, conf, height, text)
                # Output is a dict with lists: 'text', 'height', 'top', 'left', etc.
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, lang='jpn+eng')
                
                # Reconstruct full text for date search
                full_text_for_date = " ".join([t for t in data['text'] if t.strip()])
                
                # Group by lines (roughly) or blocks to form title candidates
                # Tesseract gives 'block_num', 'par_num', 'line_num'.
                # We can aggregate text by line and calculate average height as "size".
                
                current_line_text = []
                current_line_heights = []
                current_line_tops = []
                last_line_id = None # Tuple (block, par, line)
                
                num_boxes = len(data['text'])
                for i in range(num_boxes):
                    # Filter low confidence
                    try:
                        conf = int(data['conf'][i])
                    except:
                        conf = 0
                    
                    text = data['text'][i].strip()
                    if not text: continue
                    
                    if conf < 30: continue # Skip low confidence / background
                    
                    line_id = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
                    height = data['height'][i]
                    top = data['top'][i]
                    
                    if line_id != last_line_id and current_line_text:
                        # Flush previous line
                        avg_height = sum(current_line_heights) / len(current_line_heights)
                        min_top = min(current_line_tops)
                        
                        joined_text = " ".join(current_line_text)
                        candidates.append({
                            "text": joined_text, 
                            "size": avg_height,
                            "top": min_top
                        })
                        current_line_text = []
                        current_line_heights = []
                        current_line_tops = []
                    
                    current_line_text.append(text)
                    current_line_heights.append(height)
                    current_line_tops.append(top)
                    last_line_id = line_id
                
                # Flush last line
                if current_line_text:
                    avg_height = sum(current_line_heights) / len(current_line_heights)
                    min_top = min(current_line_tops)
                    candidates.append({
                        "text": " ".join(current_line_text),
                        "size": avg_height,
                        "top": min_top
                    })
                
                logger.info(f"  OCR Candidates found: {len(candidates)}")
                for c in candidates:
                    logger.info(f"    - '{c['text']}' (Sz: {c['size']:.2f}, Top: {c['top']})")
                    
            except Exception as e:
                logger.warning(f"  OCR failed: {e}")
                pass
        else:
            # Native PDF Text extraction
            text_blocks = page.get_text("dict")["blocks"]
            for block in text_blocks:
                if "lines" not in block: continue
                # Block also has 'bbox' -> (x0, y0, x1, y1)
                for line in block["lines"]:
                    # Aggregate spans in a line to form a cohesive title candidate
                    line_text = ""
                    max_size = 0
                    min_top = 9999
                    for span in line["spans"]:
                        line_text += span["text"]
                        if span["size"] > max_size:
                            max_size = span["size"]
                        # span 'bbox' is (x0, y0, x1, y1)
                        if span["bbox"][1] < min_top:
                            min_top = span["bbox"][1]
                    
                    if len(line_text.strip()) > 1:
                        candidates.append({
                            "text": line_text.strip(),
                            "size": max_size,
                            "top": min_top
                        })

        # 1. Date Extraction
        date = None
        # Enhanced patterns
        date_patterns = [
            r'(\d{4})[\s年/.-]+(\d{1,2})[\s月/.-]+(\d{1,2})[日]?', # Flexible spacers
            r'(?:作成|発行|提出|date)[:：\s]*(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
            r'(\d{4})\s+(\d{1,2})\s+(\d{1,2})' # Space separated
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, full_text_for_date)
            if match:
                 # Extract groups that look like digits
                 nums = [g for g in match.groups() if g and g.isdigit()]
                 if len(nums) >= 3:
                     y, m, d = nums[:3]
                     try:
                         # Basic validation
                         if 1900 < int(y) < 2100 and 1 <= int(m) <= 12 and 1 <= int(d) <= 31:
                             date = f"{y}{int(m):02d}{int(d):02d}"
                             break
                     except: pass
        
        # 2. Title Extraction
        title = None
        if candidates:
            # Filter candidates:
            filtered_candidates = []
            
            # Determine page height for normalization
            if ocr_height:
                norm_height = ocr_height
            else:
                try:
                    norm_height = page.rect.height
                except:
                    norm_height = 1000 # Fallback
                
            for c in candidates:
                raw = c["text"]
                
                # CLEANUP: Strict Whitelist strategy
                cleaned = re.sub(r'[^\w\s\-]', '', raw)
                
                # FIX SPACING: Remove spaces between Japanese characters
                jp_char_pat = r'[\u4e00-\u9faf\u3040-\u309f\u30a0-\u30ff]'
                cleaned = re.sub(f'(?<={jp_char_pat})\s+(?={jp_char_pat})', '', cleaned)
                
                cleaned = cleaned.strip()
                
                if len(cleaned) < 3: continue
                if re.match(r'^[\d\s\-]+$', cleaned): continue
                
                if date:
                    date_nums = date.replace(" ","").replace("/","").replace("-","")
                    raw_nums = re.sub(r'\D', '', cleaned)
                    if raw_nums and raw_nums in date_nums:
                         continue
                
                # Use cleaned text
                c["text"] = cleaned
                
                # CALCULATE SCORE
                # Score = sqrt(Size) * PositionBonus
                # Sqrt dampens the effect of massive fonts (logos, slogans)
                # Strong bias for top-of-page items
                norm_top = c["top"] / norm_height
                
                if norm_top < 0.1:   # Top 10%
                    bonus = 3.0
                elif norm_top < 0.2: # Top 20%
                    bonus = 2.0
                elif norm_top < 0.35: # Top 35%
                    bonus = 1.3
                else:
                    bonus = 1.0
                
                # Penalize if too far down (below 40%)
                if norm_top > 0.4:
                    bonus *= 0.5
                
                # Use sqrt of size to reduce outlier impact
                import math
                c["score"] = math.sqrt(c["size"]) * bonus
                c["norm_top"] = norm_top # for debug
                
                filtered_candidates.append(c)
            
            # Debug Log to file
            try:
                with open("debug_last_run.txt", "w", encoding="utf-8") as f:
                    f.write(f"--- Debug Log ---\n")
                    f.write(f"Candidates found: {len(filtered_candidates)}\n")
                    for i, c in enumerate(sorted(filtered_candidates, key=lambda x: x["score"], reverse=True)):
                        f.write(f"#{i+1}: '{c['text']}'\n")
                        f.write(f"    Size: {c['size']:.1f} -> {math.sqrt(c['size']):.2f} (sqrt)\n")
                        f.write(f"    Top:  {c['top']:.1f} ({c['norm_top']:.2%})\n")
                        f.write(f"    Score: {c['score']:.2f}\n")
            except: pass

            logger.info(f"  Filtered Candidates: {len(filtered_candidates)}")
            for c in filtered_candidates:
                logger.info(f"    -> '{c['text']}' (Score:{c['score']:.2f})")

            if filtered_candidates:
                # Sort by SCORE descending
                filtered_candidates.sort(key=lambda x: x["score"], reverse=True)
                title = filtered_candidates[0]["text"]
                # Final strict sanitize for filename
                title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
            
        return title, date
