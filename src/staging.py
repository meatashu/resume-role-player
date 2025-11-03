"""Staging system for knowledge base updates.

This module manages the staging area where parsed content is stored
before being approved and merged into the main knowledge base.
"""

from pathlib import Path
import json
from datetime import datetime
import hashlib
from typing import Dict, List, Optional, Union
import shutil

STAGING_DIR = Path(__file__).resolve().parents[2] / 'data' / 'staging'
KB_DIR = Path(__file__).resolve().parents[2] / 'knowledge_base'

def ensure_dirs():
    """Ensure staging and knowledge base directories exist."""
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    KB_DIR.mkdir(parents=True, exist_ok=True)

def generate_stage_id(content: Dict) -> str:
    """Generate a unique ID for staged content based on its hash."""
    content_str = json.dumps(content, sort_keys=True)
    return hashlib.sha256(content_str.encode()).hexdigest()[:12]

def stage_parsed_content(parsed: Dict, source_info: Dict) -> str:
    """
    Save parsed content to staging area.
    
    Args:
        parsed: The parsed content (experience, projects, etc.)
        source_info: Dict with metadata about the source (files, LinkedIn URL, etc.)
    
    Returns:
        str: The staging ID for the saved content
    """
    ensure_dirs()
    
    # Create staging entry
    stage_entry = {
        'content': parsed,
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'source': source_info,
            'status': 'pending'  # pending, approved, rejected
        }
    }
    
    # Generate unique ID
    stage_id = generate_stage_id(stage_entry)
    
    # Save to staging
    stage_path = STAGING_DIR / f'{stage_id}.json'
    with open(stage_path, 'w') as f:
        json.dump(stage_entry, f, indent=2)
    
    return stage_id

def get_staged_entry(stage_id: str) -> Optional[Dict]:
    """Retrieve a staged entry by ID."""
    stage_path = STAGING_DIR / f'{stage_id}.json'
    if not stage_path.exists():
        return None
    
    with open(stage_path) as f:
        return json.load(f)

def list_staged_entries(status: Optional[str] = None) -> List[Dict]:
    """
    List all staged entries, optionally filtered by status.
    
    Args:
        status: Optional filter ('pending', 'approved', 'rejected')
    
    Returns:
        List of staged entries with their IDs
    """
    entries = []
    for path in STAGING_DIR.glob('*.json'):
        with open(path) as f:
            entry = json.load(f)
            entry_status = entry['metadata']['status']
            
            if status is None or entry_status == status:
                entries.append({
                    'id': path.stem,
                    'timestamp': entry['metadata']['timestamp'],
                    'source': entry['metadata']['source'],
                    'status': entry_status
                })
    
    # Sort by timestamp, newest first
    return sorted(entries, key=lambda x: x['timestamp'], reverse=True)

def preview_merge_changes(stage_id: str) -> Dict[str, List[Dict]]:
    """
    Preview what would change in the KB if this staged content was merged.
    
    Returns a dict of lists showing new entries that would be added to each KB file.
    """
    entry = get_staged_entry(stage_id)
    if not entry:
        raise ValueError(f"No staged entry found with ID: {stage_id}")
    
    changes = {
        'cv.json': [],
        'projects.json': [],
        'patents.json': [],
        'certifications.json': []
    }
    
    content = entry['content']
    
    # CV changes
    if content.get('experience') or content.get('summary'):
        changes['cv.json'].extend(content.get('experience', []))
        if content.get('summary'):
            changes['cv.json'].append({'summary': content['summary']})
    
    # Projects
    if content.get('projects'):
        changes['projects.json'].extend(content['projects'])
    
    # Patents
    if content.get('patents'):
        changes['patents.json'].extend(content['patents'])
    
    # Certifications
    if content.get('certifications'):
        changes['certifications.json'].extend(content['certifications'])
    
    return changes

def approve_staged_entry(stage_id: str) -> Dict:
    """
    Approve and merge a staged entry into the main knowledge base.
    
    Returns a summary of what was merged.
    """
    entry = get_staged_entry(stage_id)
    if not entry:
        raise ValueError(f"No staged entry found with ID: {stage_id}")
    
    if entry['metadata']['status'] == 'approved':
        raise ValueError(f"Entry {stage_id} was already approved")
    
    # Update status
    entry['metadata']['status'] = 'approved'
    entry['metadata']['approved_at'] = datetime.now().isoformat()
    
    # Save updated entry
    stage_path = STAGING_DIR / f'{stage_id}.json'
    with open(stage_path, 'w') as f:
        json.dump(entry, f, indent=2)
    
    # Merge into KB
    from .kb_ingest import merge_into_kb
    merge_summary = merge_into_kb(entry['content'])
    
    return {
        'stage_id': stage_id,
        'approved_at': entry['metadata']['approved_at'],
        'merge_summary': merge_summary
    }

def reject_staged_entry(stage_id: str, reason: str) -> Dict:
    """
    Reject a staged entry.
    
    Args:
        stage_id: The staging ID
        reason: Why the entry was rejected
    
    Returns:
        Dict with rejection details
    """
    entry = get_staged_entry(stage_id)
    if not entry:
        raise ValueError(f"No staged entry found with ID: {stage_id}")
    
    if entry['metadata']['status'] == 'rejected':
        raise ValueError(f"Entry {stage_id} was already rejected")
    
    # Update status
    entry['metadata']['status'] = 'rejected'
    entry['metadata']['rejected_at'] = datetime.now().isoformat()
    entry['metadata']['rejection_reason'] = reason
    
    # Save updated entry
    stage_path = STAGING_DIR / f'{stage_id}.json'
    with open(stage_path, 'w') as f:
        json.dump(entry, f, indent=2)
    
    return {
        'stage_id': stage_id,
        'rejected_at': entry['metadata']['rejected_at'],
        'reason': reason
    }

def cleanup_old_entries(max_age_days: int = 30) -> int:
    """
    Remove old staged entries that have been approved/rejected.
    
    Args:
        max_age_days: Maximum age in days for processed entries
    
    Returns:
        Number of entries removed
    """
    removed = 0
    now = datetime.now()
    
    for path in STAGING_DIR.glob('*.json'):
        with open(path) as f:
            entry = json.load(f)
        
        status = entry['metadata']['status']
        if status == 'pending':
            continue
            
        # Check age of processed entries
        processed_at = entry['metadata'].get('approved_at') or entry['metadata'].get('rejected_at')
        if not processed_at:
            continue
            
        processed_date = datetime.fromisoformat(processed_at)
        age_days = (now - processed_date).days
        
        if age_days > max_age_days:
            path.unlink()
            removed += 1
    
    return removed