"""Utility to fetch patent information from Google Patents URLs."""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import time
import re

def fetch_patent_info(url: str) -> Optional[Dict]:
    """Fetch patent information from Google Patents URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract basic information
        title_elem = soup.find('meta', {'property': 'og:title'})
        title = title_elem['content'] if title_elem else None
        
        # Extract abstract
        abstract = soup.find('div', {'class': 'abstract'})
        abstract = abstract.get_text().strip() if abstract else None
        
        # Clean up title
        if title:
            title = re.sub(r'\s*-\s*Google\s+Patents\s*$', '', title)
            title = title.strip()
        
        # Extract patent number and clean it
        number = re.search(r'US[\d,]+[A-Z][\d,]+', url)
        if number:
            number = number.group(0)
            number = number.replace(',', '')
        
        # Extract date
        date_elem = soup.find('time')
        date = date_elem.get_text().strip() if date_elem else None
        
        if not title:
            return None
            
        return {
            'title': title,
            'abstract': abstract,
            'number': number,
            'date': date,
            'url': url
        }
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch_multiple_patents(urls: List[str]) -> List[Dict]:
    """Fetch information for multiple patents with rate limiting."""
    results = []
    
    for url in urls:
        patent = fetch_patent_info(url)
        if patent:
            results.append(patent)
        time.sleep(1)  # Rate limiting
        
    return results