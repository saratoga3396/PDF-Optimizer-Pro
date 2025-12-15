import re

def is_generic_filename(filename):
    """
    Checks if a filename appears to be a generic alphanumeric string
    (e.g., 'IMG_001.pdf', '202310101234.pdf', 'scan001.pdf').
    """
    # Remove extension
    name = filename.rsplit('.', 1)[0]
    
    # Check for common scanner patterns
    patterns = [
        r'^IMG_\d+$',           # IMG_0001
        r'^scan\d+$',           # scan0001
        r'^\d{8,}$',            # 202312141010
        r'^[a-zA-Z0-9]{8,}$',   # Random string like abcd1234
        r'^New Doc.*$'          # New Doc 2023...
    ]
    
    for pattern in patterns:
        if re.match(pattern, name, re.IGNORECASE):
            return True
    return False

def sanitize_filename(text):
    """
    Removes characters invalid in filenames and truncates length.
    """
    # Remove characters that are problematic in filenames
    text = re.sub(r'[\\/*?:"<>|]', "", text)
    # Replace control characters
    text = re.sub(r'[\x00-\x1f]', "", text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text[:250]  # Limit length
