# utils/parser.py
import re
from dateutil import parser as dateparser
from rapidfuzz import process, fuzz
from typing import List, Dict, Tuple

# Enhanced patterns for Q&A detection
QA_PATTERNS = [
    r'Questions and Answers', r'Question-and-Answer', r'\bQ&A\b',
    r'Operator:', r'We will now open the line for questions', 
    r'First question is from', r'our first question', r'first question',
    r'Now we will open the floor for questions', r'Let\'s open the floor for questions',
    r'We\'ll now open the floor for questions', r'Now we\'ll take questions',
    r'Let\'s take some questions', r'We\'ll take some questions',
    r'Questions from the floor', r'Questions from analysts',
    r'Analyst questions', r'Investor questions'
]

# Enhanced speaker detection patterns
SPEAKER_LINE_RE = re.compile(r'^(?P<speaker>[A-Z][A-Z0-9 \.\-]{2,60})[:\-\—]\s*(?P<message>.+)', re.M)
SPEAKER_LINE_ALT_RE = re.compile(r'^(?P<speaker>[A-Za-z][A-Za-z0-9 \.\-]{2,60})[:\-\—]\s*(?P<message>.+)', re.M)

# Question indicators
QUESTION_INDICATORS = [
    r'\?', r'\b(question|ask|wondering|curious|inquire)\b',
    r'\b(what|how|why|when|where|which|who)\b.*\?',
    r'\b(can you|could you|would you|do you)\b'
]

def extract_date(text: str):
    # attempt to locate common date patterns
    possible = re.findall(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*\d{4}\b', text)
    if possible:
        try:
            return dateparser.parse(possible[0]).date()
        except:
            pass
    # fallback numeric dates
    possible2 = re.findall(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', text)
    if possible2:
        try:
            return dateparser.parse(possible2[0]).date()
        except:
            pass
    return None

def extract_company_name(first_pages_text: str) -> str:
    # crude heuristic: the first non-empty uppercase-ish line
    for line in first_pages_text.splitlines():
        line = line.strip()
        if not line:
            continue
        # if line contains company suffix or is uppercase short
        if re.search(r'\b(Inc|Corp|Corporation|LLC|Limited|PLC|Co\.)\b', line, re.I) or (line.isupper() and 2 < len(line) < 80):
            return line
    # fallback: first non-empty line
    for line in first_pages_text.splitlines():
        if line.strip():
            return line.strip()
    return "Unknown Company"

def find_q_a_split(full_text: str) -> Tuple[str, str]:
    for pat in QA_PATTERNS:
        m = re.search(pat, full_text, flags=re.I)
        if m:
            return full_text[:m.start()], full_text[m.start():]
    return full_text, ""

def basic_speaker_chunks(text: str) -> List[Dict]:
    """
    Enhanced speaker chunker with better pattern matching:
    - Try multiple speaker patterns
    - Handle speaker name variations
    - Better orphan text handling
    """
    chunks = []
    cur = None
    
    for line in text.splitlines():
        line_strip = line.strip()
        if not line_strip:
            continue
            
        # Try primary speaker pattern first
        m = SPEAKER_LINE_RE.match(line_strip)
        if not m:
            # Try alternative pattern for mixed case speakers
            m = SPEAKER_LINE_ALT_RE.match(line_strip)
        
        if m:
            if cur:
                chunks.append(cur)
            cur = {
                "speaker_raw": m.group("speaker").strip(),
                "text": m.group("message").strip()
            }
        else:
            if cur:
                cur["text"] += "\n" + line_strip
            else:
                # Check if this might be a speaker line without proper formatting
                if is_likely_speaker_line(line_strip):
                    # Try to extract speaker and message
                    speaker, message = extract_speaker_from_line(line_strip)
                    if speaker:
                        cur = {
                            "speaker_raw": speaker,
                            "text": message
                        }
                    else:
                        cur = {"speaker_raw": "UNKNOWN", "text": line_strip}
                else:
                    cur = {"speaker_raw": "UNKNOWN", "text": line_strip}
    
    if cur:
        chunks.append(cur)
    return chunks

def is_likely_speaker_line(line: str) -> bool:
    """
    Check if a line is likely a speaker line based on patterns.
    """
    # Check for common speaker patterns
    patterns = [
        r'^[A-Z][A-Z0-9 \.\-]{2,60}[:\-\—]',
        r'^[A-Za-z][A-Za-z0-9 \.\-]{2,60}[:\-\—]',
        r'^[A-Z][A-Z0-9 \.\-]{2,60}\s+[A-Z]',  # Speaker name followed by capital letter
    ]
    
    for pattern in patterns:
        if re.match(pattern, line):
            return True
    return False

def extract_speaker_from_line(line: str) -> Tuple[str, str]:
    """
    Try to extract speaker and message from a line that might be a speaker line.
    """
    # Try different patterns
    patterns = [
        r'^(?P<speaker>[A-Z][A-Z0-9 \.\-]{2,60})[:\-\—]\s*(?P<message>.+)',
        r'^(?P<speaker>[A-Za-z][A-Za-z0-9 \.\-]{2,60})[:\-\—]\s*(?P<message>.+)',
        r'^(?P<speaker>[A-Z][A-Z0-9 \.\-]{2,60})\s+(?P<message>[A-Z].+)',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, line)
        if match:
            return match.group("speaker").strip(), match.group("message").strip()
    
    return "", line

def map_speakers_to_roles(chunks: List[Dict], participant_list: List[str]) -> List[Dict]:
    """
    Use fuzzy matching to map raw speaker labels to known participants (management).
    If match score is high, tag as management; else investor/moderator.
    """
    mapped = []
    for c in chunks:
        raw = c.get("speaker_raw", "")
        if raw.strip().upper() in ("OPERATOR", "MODERATOR"):
            role = "moderator"
            name = raw
        else:
            # fuzzy match against participant_list
            if participant_list:
                best = process.extractOne(raw, participant_list, scorer=fuzz.token_sort_ratio)
                if best and best[1] > 75:
                    name = best[0]
                    role = "management"
                else:
                    name = raw
                    role = "investor"
            else:
                name = raw
                role = "investor"
        mapped.append({
            "speaker_name": name,
            "speaker_raw": raw,
            "role": role,
            "text": c.get("text", "")
        })
    return mapped

def pair_questions_answers(q_chunks: List[Dict]) -> List[Dict]:
    """
    Enhanced Q&A pairing with better question detection:
    - Identify questions using multiple indicators
    - Match questions to their corresponding answers
    - Handle speaker companies/roles for context
    """
    pairs = []
    i = 0
    N = len(q_chunks)
    
    while i < N:
        block = q_chunks[i]
        is_question = is_question_block(block)
        
        if is_question:
            # Collect answer blocks until next question or end
            j = i + 1
            answers = []
            
            while j < N:
                next_block = q_chunks[j]
                # Stop if we hit another question
                if is_question_block(next_block):
                    break
                # Stop if we hit a moderator/operator (usually indicates new question)
                if next_block.get('role') == 'moderator' and 'question' in next_block.get('text', '').lower():
                    break
                answers.append(next_block)
                j += 1
            
            # Extract speaker company/role for context
            question_context = extract_question_context(block)
            
            pairs.append({
                "question": block,
                "answers": answers,
                "question_context": question_context,
                "question_speaker": block.get('speaker_name', 'Unknown'),
                "answer_speakers": [ans.get('speaker_name', 'Unknown') for ans in answers]
            })
            i = j
        else:
            i += 1
    
    return pairs

def is_question_block(block: Dict) -> bool:
    """
    Enhanced question detection using multiple indicators.
    """
    text = block.get('text', '').lower()
    role = block.get('role', '')
    
    # Check for question indicators
    for indicator in QUESTION_INDICATORS:
        if re.search(indicator, text, re.IGNORECASE):
            return True
    
    # Check for role-based indicators
    if role == 'investor':
        return True
    
    # Check for specific question patterns
    question_patterns = [
        r'\b(analyst|question|ask|wondering|curious|inquire)\b',
        r'\b(what|how|why|when|where|which|who)\b.*\?',
        r'\b(can you|could you|would you|do you)\b',
        r'\b(first|next|follow-up)\s+(question|one)\b'
    ]
    
    for pattern in question_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def extract_question_context(question_block: Dict) -> Dict[str, str]:
    """
    Extract context information from question block.
    """
    text = question_block.get('text', '')
    speaker = question_block.get('speaker_name', 'Unknown')
    
    context = {
        'speaker': speaker,
        'company': 'Unknown',
        'role': 'Analyst'
    }
    
    # Try to extract company name from speaker or text
    company_patterns = [
        r'from\s+([A-Z][A-Za-z\s&]+)',
        r'([A-Z][A-Za-z\s&]+)\s+analyst',
        r'([A-Z][A-Za-z\s&]+)\s+here'
    ]
    
    for pattern in company_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            context['company'] = match.group(1).strip()
            break
    
    # Try to extract role
    if 'analyst' in text.lower():
        context['role'] = 'Analyst'
    elif 'investor' in text.lower():
        context['role'] = 'Investor'
    elif 'fund' in text.lower():
        context['role'] = 'Fund Manager'
    
    return context
