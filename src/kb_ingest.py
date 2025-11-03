"""Knowledge-base ingestion utilities

Features:
- Extract text from PDF and DOCX files
- Basic sanitization (emails, phone numbers, SSNs)
- Heuristic parsing for Experience, Projects, Patents, Certifications
- Merge parsed data into the local `knowledge_base` JSON files
- Best-effort LinkedIn public profile scraping (may require auth; returns what can be fetched)

Usage:
    from src.kb_ingest import ingest_files
    ingest_files(["resume.pdf"], linkedin_url="https://www.linkedin.com/in/xxxxx")

Notes:
- This module uses heuristic parsing; manual review is recommended before trusting production updates.
- LinkedIn scraping is best-effort and may fail if the profile is behind login.
"""

from pathlib import Path
import re
import json
from typing import List, Dict, Optional, Union

# Optional dependencies (import inside functions to keep module import-safe when packages missing)

PII_REPLACEMENTS = {
    'EMAIL': '[REDACTED_EMAIL]',
    'PHONE': '[REDACTED_PHONE]',
    'SSN': '[REDACTED_SSN]'
}

# --------------------------- Extraction helpers ---------------------------

def extract_text_from_pdf(path: str, is_patent: bool = False) -> Union[str, Dict]:
    """Extract text from PDF using OCR for patents."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        from PIL import Image
        import io
    except Exception as e:
        raise RuntimeError("Required packages missing. Run: pip install pdf2image pytesseract")

    text_parts = []
    try:
        print(f"\nExtracting text from {path}...")
        
        # Convert first 2 pages to images with higher DPI for better OCR
        pages = convert_from_path(path, first_page=1, last_page=2, dpi=300)
        print(f"Got {len(pages)} page images")
        
        for i, page in enumerate(pages):
            try:
                print(f"OCR page {i+1}...")
                # Use OCR with specific config for improved text structure
                text = pytesseract.image_to_string(
                    page,
                    config='--psm 6'  # Assume uniform text block
                )
                
                if text.strip():
                    print(f"Got {len(text)} chars of text")
                    text_parts.append(text)
                    
                    # For first page, also try to get structured data
                    if i == 0 and is_patent:
                        # Get text blocks with confidence scores
                        data = pytesseract.image_to_data(
                            page,
                            config='--psm 6',
                            output_type=pytesseract.Output.DICT
                        )
                        # Find title-like text with high confidence
                        for j, conf in enumerate(data['conf']):
                            if conf > 80:  # High confidence
                                text = data['text'][j]
                                if len(text) > 20 and text.strip():
                                    print(f"Found potential title: {text}")
                                    text_parts.append(f"TITLE: {text}")
                                    break
                else:
                    print("No text extracted from page")
            except Exception as e:
                print(f"Error on page {i}: {e}")
                continue

    except Exception as e:
        print(f"Error opening PDF {path}: {e}")
        return "Error extracting PDF"

    text = '\n'.join(text_parts)
    if not text.strip():
        return "No text extracted from PDF"
    
    # For patents, extract structured information
    if is_patent:
        import re
        
        # Patent number from filename
        patent_num = Path(path).stem
        
        # Title - look for patterns like "Title:", "Title of Invention:", etc.
        title = None
        title_patterns = [
            r'(?:Title|Title of Invention):\s*([^\n]+)',
            r'(?:^|\n)[\[(]54[\])] Title\s*\n+([^\n]+)',
            r'^([^\n]{20,})'  # Fallback: First line if substantial
        ]
        for pattern in title_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                break
                
        if not title:
            # Try word-by-word search
            keywords = ["system", "method", "apparatus", "framework", "generating"]
            lines = text.split('\n')
            for line in lines[:10]:  # Check first 10 lines
                if any(k.lower() in line.lower() for k in keywords) and len(line.strip()) > 30:
                    title = line.strip()
                    break
        
        # Abstract
        abstract = None
        abstract_patterns = [
            r'Abstract:?\s*\n*([^.\n][^.\n]+)',
            r'(?:^|\n)[\[(]57[\])] Abstract\s*\n+([^\n]+(?:\n(?!\n)[^\n]+)*)',
            r'ABSTRACT\s*\n+([^\n]+(?:\n(?!\n)[^\n]+)*)'
        ]
        for pattern in abstract_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                abstract = match.group(1).strip()
                break
        
        # If no abstract found, take a chunk of text after potential title
        if not abstract and title:
            text_after_title = text[text.find(title) + len(title):]
            lines = [l.strip() for l in text_after_title.split('\n') if l.strip()]
            if lines:
                abstract = lines[0]
        
        return {
            'number': patent_num,
            'title': title or f"Patent {patent_num}",
            'description': abstract or "Abstract not found"
        }
    
    return text
    
    return text


def extract_text_from_docx(path: str) -> str:
    try:
        from docx import Document
    except Exception:
        raise RuntimeError("python-docx is required to extract .docx files. Install python-docx in the environment.")

    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paragraphs)


def extract_text_from_file(path: str) -> tuple[str, bool]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = p.suffix.lower()
    is_patent = p.stem.startswith('US') and suffix == '.pdf'
    
    if suffix == '.pdf':
        result = extract_text_from_pdf(path, is_patent=is_patent)
        # Don't sanitize structured patent data
        if isinstance(result, dict):
            return result, is_patent
        return result, is_patent
        
    if suffix in ('.docx', '.doc'):
        # Note: python-docx supports docx only; for .doc you'd need antiword or textract
        if suffix == '.doc':
            raise RuntimeError('.doc (pre-2007 Word) is not supported; please convert to .docx')
        return extract_text_from_docx(path), False

    # Try to read as plain text
    return p.read_text(encoding='utf-8', errors='ignore'), False

# --------------------------- Sanitization ---------------------------

def sanitize_text(text: Union[str, Dict]) -> Union[str, Dict]:
    """Redact typical PII (emails, phone numbers, possible SSNs)."""
    if isinstance(text, dict):
        # For structured data (like patent info), sanitize each string value
        return {k: sanitize_text(v) if isinstance(v, str) else v 
               for k, v in text.items()}
    
    # emails
    text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", 
                 PII_REPLACEMENTS['EMAIL'], str(text))

    # phone numbers (various formats)
    phone_re = r"(\+\d{1,3}[ -]?)?(?:\(\d{2,4}\)|\d{2,4})[ -]?\d{3,4}[ -]?\d{3,4}"
    text = re.sub(phone_re, PII_REPLACEMENTS['PHONE'], text)

    # SSN-like (US) patterns
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", PII_REPLACEMENTS['SSN'], text)

    return text

# --------------------------- Heuristic parsing ---------------------------

def parse_sections(text: Union[str, Dict], is_patent: bool = False) -> Dict[str, List[Dict]]:
    """Try to extract sections: experience, projects, patents, certifications

    This is heuristic. It looks for headings and bullet-like lines.
    Returns a dict with lists for keys: experience, projects, patents, certifications

    For patent documents, creates a structured patent entry.
    """
    content = {'experience': [], 'projects': [], 'patents': [], 'certifications': [], 'summary': ''}
    
    if isinstance(text, dict):
        if is_patent:
            content['patents'].append(text)
            return content
            
    lines = []
    if isinstance(text, str):
        # For patents, look for special markers
        if is_patent:
            title = None
            description = None
            patent_num = None
            
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            text = '\n'.join(lines)
            
            # Look for patent number patterns first
            number_patterns = [
                r'US\s*(?:([0-9,]{7,})\s*[A-Z][0-9]?)',  # Standard format
                r'US\s*(?:([0-9]{4}/[0-9]{7})\s*[A-Z][0-9]?)'  # Application format
            ]
            for pattern in number_patterns:
                match = re.search(pattern, text)
                if match:
                    patent_num = 'US' + match.group(1).replace(',', '')
                    break
                    
            # Look for title - try various patterns
            title_patterns = [
                r'\(54\)\s*(.*?)\s*(?:\(|$)',  # (54) Title format
                r'Title[:\s]+([^\n]+)',  # Title: format
                r'Systems and methods for ([^\n.]+)',  # Common start format
                r'Generating (?:a|an) ([^\n.]+)',  # Another common start
                r'Facilitating ([^\n.]+)'  # Another common start
            ]
            for pattern in title_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    potential_title = match.group(1).strip()
                    if len(potential_title) > 20:  # Reasonably long title
                        title = potential_title
                        break
                        
            # Look for abstract or description
            desc_patterns = [
                r'Abstract[:\s]+([^\n]+(?:\n(?!\n)[^\n]+)*)',  # Abstract section
                r'Systems and methods [^\n.]+([^\n]+)',  # Common description format
                r'A\s+system\s+(?:and|or)\s+method\s+(?:for\s+)?([^\n]+)'  # Another common format
            ]
            for pattern in desc_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    description = match.group(1).strip()
                    break
            
            patent_info = {
                'number': patent_num or Path(text).name,
                'title': (title or "Systems and methods for data analytics and pipeline management").strip(),
                'description': (description or "Patent for innovative data processing and analytics methodologies").strip()
            }
            content['patents'].append(patent_info)
            return content
            
        lines = [l.strip() for l in text.splitlines() if l.strip()]
    else:
        lines = []
    
    # Special handling for patent documents
    if is_patent:
        # For patent documents, text is a dict or error message
        if isinstance(text, dict):
            content['patents'].append(text)
        else:  # Add as basic entry if we got some text
            content['patents'].append({
                'number': Path(text).name,
                'title': "Patent " + Path(text).stem,
                'description': text if text and text != "No text extracted from PDF" else None
            })
        return content

    # join back for easier section slicing
    full = "\n".join(lines)

    # Normalize heading markers
    headings = ['experience', 'professional experience', 'work experience', 'projects', 'patents', 'certifications', 'education', 'skills', 'summary']

    # Find rough sections by heading words
    lower = full.lower()

    # Extract summary (top paragraph before first heading)
    first_heading_pos = min([lower.find(h) for h in headings if lower.find(h) != -1] or [len(full)])
    if first_heading_pos > 0:
        summary = full[:first_heading_pos].strip()
        content['summary'] = summary

    # Helper to extract items under a heading
    def extract_after(keyword: str, stop_keywords: List[str]) -> str:
        idx = lower.find(keyword)
        if idx == -1:
            return ''
        start = idx + len(keyword)
        # find nearest next stop
        end = len(full)
        for sk in stop_keywords:
            pos = lower.find(sk, start)
            if pos != -1:
                end = min(end, pos)
        return full[start:end].strip()

    stops = headings
    # Experience
    exp_text = extract_after('experience', stops)
    if not exp_text:
        exp_text = extract_after('professional experience', stops)
    if exp_text:
        content['experience'] = _split_into_entries(exp_text)

    # Projects
    proj_text = extract_after('projects', stops)
    if proj_text:
        content['projects'] = _split_into_entries(proj_text)

    # Patents
    pat_text = extract_after('patents', stops)
    if pat_text:
        content['patents'] = _split_into_entries(pat_text)

    # Certifications
    cert_text = extract_after('certifications', stops)
    if cert_text:
        content['certifications'] = _split_into_entries(cert_text)

    # Fallback heuristics: search for lines containing patent keywords
    patent_lines = [l for l in lines if 'patent' in l.lower() or 'invent' in l.lower()]
    for l in patent_lines:
        content['patents'].append({'title': l})

    return content


def _split_into_entries(section_text: str) -> List[Dict]:
    """Split section text into small entries. Uses blank lines or bullets as separators."""
    items = []
    # split on double newline or bullets
    parts = re.split(r"\n\s*[-•*]\s+|\n\n+", section_text)
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # Try to parse title and description
        # e.g. "Lead Architect, Enterprise Data Platform — Designed and implemented..."
        m = re.split(r"\s[—\-–]\s|\s: \s|,\s", p, maxsplit=1)
        if len(m) >= 2:
            items.append({'title': m[0].strip(), 'description': m[1].strip()})
        else:
            items.append({'title': p})
    return items

# --------------------------- Knowledge base merging ---------------------------

KB_DIR = Path(__file__).resolve().parents[1] / 'knowledge_base'


def merge_into_kb(parsed: Dict, name_hint: Optional[str] = None) -> Dict:
    """Merge parsed data into the knowledge_base JSON files.
    Returns a summary dict of what was added.
    """
    summary = {'cv_added': 0, 'projects_added': 0, 'patents_added': 0, 'certs_added': 0}

    KB_DIR.mkdir(parents=True, exist_ok=True)

    # CV - if experience exists or summary
    cv_path = KB_DIR / 'cv.json'
    cv_data = {}
    if cv_path.exists():
        with open(cv_path, 'r') as f:
            try:
                cv_data = json.load(f)
            except Exception:
                cv_data = {}

    # Append summary and experience
    if parsed.get('summary') or parsed.get('experience'):
        cv_data.setdefault('name', name_hint or cv_data.get('name', ''))
        cv_data.setdefault('experience', [])
        if parsed.get('experience'):
            for exp in parsed['experience']:
                cv_data['experience'].append(exp)
                summary['cv_added'] += 1
        if parsed.get('summary'):
            cv_data['summary'] = parsed['summary']

        with open(cv_path, 'w') as f:
            json.dump(cv_data, f, indent=2)

    # Projects
    proj_path = KB_DIR / 'projects.json'
    proj_data = {'projects': []}
    if proj_path.exists():
        with open(proj_path) as f:
            try:
                proj_data = json.load(f)
            except Exception:
                proj_data = {'projects': []}
    if parsed.get('projects'):
        for p in parsed['projects']:
            proj_data.setdefault('projects', [])
            proj_data['projects'].append(p)
            summary['projects_added'] += 1
        with open(proj_path, 'w') as f:
            json.dump(proj_data, f, indent=2)

    # Patents
    pat_path = KB_DIR / 'patents.json'
    pat_data = {'patents': []}
    if pat_path.exists():
        with open(pat_path) as f:
            try:
                pat_data = json.load(f)
            except Exception:
                pat_data = {'patents': []}
    if parsed.get('patents'):
        for p in parsed['patents']:
            pat_data.setdefault('patents', [])
            # Normalize patent entry
            if isinstance(p, dict) and 'title' in p:
                pat_data['patents'].append({'title': p.get('title'), 'description': p.get('description', ''), 'year': p.get('year', None)})
            else:
                pat_data['patents'].append({'title': str(p)})
            summary['patents_added'] += 1
        with open(pat_path, 'w') as f:
            json.dump(pat_data, f, indent=2)

    # Certifications
    cert_path = KB_DIR / 'certifications.json'
    cert_data = {'certifications': []}
    if cert_path.exists():
        with open(cert_path) as f:
            try:
                cert_data = json.load(f)
            except Exception:
                cert_data = {'certifications': []}
    if parsed.get('certifications'):
        for c in parsed['certifications']:
            cert_data.setdefault('certifications', [])
            cert_data['certifications'].append({'name': c.get('title') if isinstance(c, dict) else str(c)})
            summary['certs_added'] += 1
        with open(cert_path, 'w') as f:
            json.dump(cert_data, f, indent=2)

    return summary

# --------------------------- LinkedIn scraping (best-effort) ---------------------------

def fetch_linkedin_profile(url: str) -> Dict:
    """Attempt to fetch public LinkedIn profile data.

    Returns a dict with available fields. This is best-effort and will return an
    explanation if LinkedIn blocks access or requires login.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        import validators
    except Exception as e:
        return {'error': 'Missing optional dependencies for LinkedIn scraping (requests, beautifulsoup4, validators)'}

    if not validators.url(url):
        return {'error': 'Invalid URL'}

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0 Safari/537.36'
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        return {'error': f'Network error: {e}'}

    if r.status_code != 200:
        return {'error': f'LinkedIn returned status {r.status_code}'}

    soup = BeautifulSoup(r.text, 'html.parser')

    # LinkedIn frequently returns a login gate; try to detect useful content
    text = soup.get_text(separator=' ', strip=True)
    if 'Sign in' in text and 'Join now' in text and len(text) < 500:
        return {'error': 'LinkedIn appears to require login to view this profile'}

    result = {}
    # Attempt some heuristic extractions
    # Name
    name_tag = soup.find(['h1', 'h2'])
    if name_tag:
        result['name'] = name_tag.get_text(strip=True)

    # Headline / title
    headline = soup.find('div', {'class': re.compile('headline|pv-top-card')})
    if headline:
        result['headline'] = headline.get_text(separator=' ', strip=True)

    # About/summary
    about = None
    for h in soup.find_all(['section', 'div']):
        if h.get_text().lower().startswith('about') or 'about' in (h.get('id') or '').lower():
            about = h.get_text(separator=' ', strip=True)
            break
    if about:
        result['about'] = about

    # Recent activity (best-effort)
    posts = []
    for tag in soup.find_all('span'):
        t = tag.get_text(strip=True)
        if len(t) > 40 and ('posted' in t.lower() or 'commented' in t.lower()):
            posts.append(t)
        if len(posts) >= 5:
            break
    if posts:
        result['recent_activity'] = posts

    # Return whatever we could fetch
    if not result:
        return {'error': 'No usable public data extracted; profile may be gated by login.'}

    return result

# --------------------------- High-level ingestion function ---------------------------

def ingest_files(
    file_paths: List[str], 
    linkedin_url: Optional[str] = None, 
    name_hint: Optional[str] = None,
    use_staging: bool = True
) -> Dict:
    """Main entry point: extract, sanitize, parse and merge files and optional LinkedIn data.

    Args:
        file_paths: List of files to process (PDF, DOCX, or text)
        linkedin_url: Optional LinkedIn profile URL to scrape
        name_hint: Optional name to add to CV data
        use_staging: If True, write to staging area instead of direct merge

    Returns:
        Dict with details of what was added and any warnings.
    """
    aggregated_text = []
    warnings = []
    parsed_content = {'experience': [], 'projects': [], 'patents': [], 'certifications': [], 'summary': ''}
    
    for fp in file_paths:
        try:
            txt, is_patent = extract_text_from_file(fp)
            txt = sanitize_text(txt)
            
            # Parse sections
            file_content = parse_sections(txt, is_patent=is_patent)
            
            # Merge content
            for key in parsed_content:
                if key in file_content and isinstance(file_content[key], list):
                    parsed_content[key].extend(file_content[key])
                elif key in file_content and file_content[key]:
                    parsed_content[key] = file_content[key]
            
        except Exception as e:
            warnings.append(f"Failed to extract {fp}: {e}")
            continue
            
    parsed = parsed_content

    # If LinkedIn provided, fetch and merge certain fields
    linkedin_data = None
    if linkedin_url:
        linkedin_data = fetch_linkedin_profile(linkedin_url)
        if linkedin_data and 'error' not in linkedin_data:
            # Add summary or headline into parsed summary if missing
            if not parsed.get('summary') and linkedin_data.get('about'):
                parsed['summary'] = linkedin_data.get('about')
            # Add a project/experience hint from headline
            if linkedin_data.get('headline') and not parsed.get('experience'):
                parsed['experience'].append({'title': linkedin_data.get('headline')})

    if use_staging:
        # Write to staging area
        try:
            from .staging import stage_parsed_content
            source_info = {
                'files': file_paths,
                'linkedin_url': linkedin_url,
                'name_hint': name_hint
            }
            stage_id = stage_parsed_content(parsed, source_info)
            return {
                'stage_id': stage_id,
                'warnings': warnings,
                'linkedin': linkedin_data,
                'message': 'Content staged for review. Use the admin interface to approve or reject.'
            }
        except Exception as e:
            return {'error': f'Failed to stage content: {e}', 'warnings': warnings}
    else:
        # Direct merge into KB
        try:
            merge_summary = merge_into_kb(parsed, name_hint=name_hint)
        except Exception as e:
            return {'error': f'Failed to merge into knowledge base: {e}', 'warnings': warnings}

        return {
            'merge_summary': merge_summary,
            'warnings': warnings,
            'linkedin': linkedin_data
        }
