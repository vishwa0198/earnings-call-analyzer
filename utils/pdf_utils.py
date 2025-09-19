import io
import re
from typing import List, Dict, Tuple
from PyPDF2 import PdfReader

def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """
    Extracts full text from a PDF given as bytes with enhanced cleaning.
    """
    pdf_reader = PdfReader(io.BytesIO(file_bytes))
    text = []
    for page in pdf_reader.pages:
        try:
            page_text = page.extract_text() or ""
            # Clean the text
            page_text = clean_text(page_text)
            text.append(page_text)
        except Exception:
            continue
    return "\n".join(text)

def get_first_pages_text_from_bytes(file_bytes: bytes, n: int = 2) -> str:
    """
    Extract text from the first n pages of a PDF (default 2 pages).
    """
    pdf_reader = PdfReader(io.BytesIO(file_bytes))
    text = []
    for i, page in enumerate(pdf_reader.pages[:n]):
        try:
            page_text = page.extract_text() or ""
            page_text = clean_text(page_text)
            text.append(page_text)
        except Exception:
            continue
    return "\n".join(text)

def clean_text(text: str) -> str:
    """
    Clean and preprocess text to remove formatting artifacts.
    """
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page numbers and headers/footers
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    
    # Remove common PDF artifacts
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Remove non-ASCII characters
    text = re.sub(r'\f', '\n', text)  # Replace form feeds with newlines
    
    # Clean up speaker patterns
    text = re.sub(r'([A-Z][A-Z0-9 \.\-]{2,60})\s*[:\-\—]\s*', r'\1: ', text)
    
    return text.strip()

def find_conference_call_start(text: str) -> int:
    """
    Find the start of the conference call using pattern matching.
    """
    patterns = [
        r"Ladies and gentlemen, welcome to",
        r"Good morning and welcome to",
        r"Good afternoon and welcome to",
        r"Thank you for joining us",
        r"Welcome to.*earnings call",
        r"Welcome to.*conference call",
        r"Thank you for joining.*earnings",
        r"Thank you for joining.*conference"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.start()
    
    return 0

def extract_participants_from_first_pages(text: str) -> List[Dict[str, str]]:
    """
    Extract management participants with their designations from first pages.
    """
    participants = []
    lines = text.split('\n')
    
    # Common management titles
    titles = [
        'CEO', 'CFO', 'President', 'Chief Executive Officer', 'Chief Financial Officer',
        'COO', 'Chief Operating Officer', 'CTO', 'Chief Technology Officer',
        'VP', 'Vice President', 'Director', 'Chairman', 'Chair', 'Head of',
        'Managing Director', 'Executive Vice President', 'Senior Vice President'
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if line contains management titles
        for title in titles:
            if re.search(rf'\b{re.escape(title)}\b', line, re.IGNORECASE):
                # Extract name and title
                name_match = re.search(r'^([^,]+)', line)
                if name_match:
                    participants.append({
                        'name': name_match.group(1).strip(),
                        'title': title,
                        'full_line': line
                    })
                break
    
    return participants
