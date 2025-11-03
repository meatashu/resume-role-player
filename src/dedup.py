from typing import Dict, List, Any, Tuple
import difflib
from datetime import datetime
import hashlib
import re

class DuplicateResolver:
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold

    def get_content_hash(self, content: Dict[str, Any]) -> str:
        """Generate a stable hash of content for comparison"""
        # Sort and stringify the content
        content_str = str(sorted(str(content.items()).encode('utf-8')))
        return hashlib.md5(content_str.encode('utf-8')).hexdigest()

    def text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        return difflib.SequenceMatcher(None, text1, text2).ratio()

    def is_duplicate_entry(self, new_entry: Dict, existing_entries: List[Dict]) -> Tuple[bool, Dict]:
        """
        Check if an entry is a duplicate using fuzzy matching
        Returns: (is_duplicate, matching_entry)
        """
        new_hash = self.get_content_hash(new_entry)
        
        # First check exact hash matches
        for entry in existing_entries:
            if self.get_content_hash(entry) == new_hash:
                return True, entry

        # Then check fuzzy matches on text content
        for entry in existing_entries:
            similarity_score = 0
            matches = 0
            
            # Compare common text fields
            for key in ['title', 'description', 'summary', 'role', 'company']:
                if key in new_entry and key in entry:
                    similarity_score += self.text_similarity(str(new_entry[key]), str(entry[key]))
                    matches += 1
            
            # Calculate average similarity if we found matching fields
            if matches > 0:
                avg_similarity = similarity_score / matches
                if avg_similarity > self.similarity_threshold:
                    return True, entry

        return False, {}

    def resolve_conflicts(self, new_entry: Dict, existing_entry: Dict) -> Dict:
        """
        Resolve conflicts between duplicate entries
        Strategy:
        1. Keep newer timestamps
        2. Merge unique items in lists
        3. Keep longer/more detailed text fields
        """
        resolved = existing_entry.copy()
        
        # Compare timestamps if available
        new_time = new_entry.get('timestamp', datetime.min)
        old_time = existing_entry.get('timestamp', datetime.min)
        
        # If new entry is newer, use it as base instead
        if new_time > old_time:
            resolved = new_entry.copy()
        
        # Merge lists (like skills, achievements)
        for key, value in new_entry.items():
            if isinstance(value, list):
                existing_list = resolved.get(key, [])
                merged = list(set(existing_list + value))  # Remove duplicates
                resolved[key] = sorted(merged)
            
            # Keep longer text fields
            elif isinstance(value, str):
                existing_text = resolved.get(key, "")
                if len(value) > len(existing_text):
                    resolved[key] = value
        
        return resolved

    def deduplicate_entries(self, entries: List[Dict]) -> List[Dict]:
        """Deduplicate a list of entries"""
        unique_entries = []
        
        for entry in entries:
            is_duplicate, matching_entry = self.is_duplicate_entry(entry, unique_entries)
            if is_duplicate:
                # Find and update the matching entry in our results
                idx = unique_entries.index(matching_entry)
                unique_entries[idx] = self.resolve_conflicts(entry, matching_entry)
            else:
                unique_entries.append(entry)
        
        return unique_entries