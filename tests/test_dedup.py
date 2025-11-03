import unittest
from datetime import datetime
from ..src.dedup import DuplicateResolver

class TestDuplicateResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = DuplicateResolver()
        
    def test_exact_duplicate_detection(self):
        """Test exact duplicate detection"""
        entry1 = {"title": "Software Engineer", "company": "Tech Corp"}
        entry2 = {"title": "Software Engineer", "company": "Tech Corp"}
        
        is_duplicate, matching = self.resolver.is_duplicate_entry(entry1, [entry2])
        self.assertTrue(is_duplicate)
        
    def test_fuzzy_duplicate_detection(self):
        """Test fuzzy matching for similar entries"""
        entry1 = {"title": "Senior Software Engineer", "company": "Tech Corp"}
        entry2 = {"title": "Sr. Software Engineer", "company": "Tech Corp"}
        
        is_duplicate, matching = self.resolver.is_duplicate_entry(entry1, [entry2])
        self.assertTrue(is_duplicate)
        
    def test_non_duplicate_detection(self):
        """Test different entries are not marked as duplicates"""
        entry1 = {"title": "Software Engineer", "company": "Tech Corp"}
        entry2 = {"title": "Product Manager", "company": "Different Corp"}
        
        is_duplicate, matching = self.resolver.is_duplicate_entry(entry1, [entry2])
        self.assertFalse(is_duplicate)
        
    def test_conflict_resolution_timestamps(self):
        """Test conflict resolution with timestamps"""
        old_entry = {
            "title": "Engineer",
            "timestamp": datetime(2020, 1, 1),
            "skills": ["Python"]
        }
        new_entry = {
            "title": "Senior Engineer",
            "timestamp": datetime(2021, 1, 1),
            "skills": ["Python", "Java"]
        }
        
        resolved = self.resolver.resolve_conflicts(new_entry, old_entry)
        self.assertEqual(resolved["title"], "Senior Engineer")
        self.assertEqual(set(resolved["skills"]), {"Python", "Java"})
        
    def test_deduplication_with_merging(self):
        """Test deduplication of a list with merging"""
        entries = [
            {
                "title": "Software Engineer",
                "skills": ["Python", "Java"],
                "timestamp": datetime(2020, 1, 1)
            },
            {
                "title": "Sr. Software Engineer",
                "skills": ["Python", "Kubernetes"],
                "timestamp": datetime(2021, 1, 1)
            }
        ]
        
        deduplicated = self.resolver.deduplicate_entries(entries)
        self.assertEqual(len(deduplicated), 1)
        self.assertEqual(set(deduplicated[0]["skills"]), {"Python", "Java", "Kubernetes"})
        self.assertEqual(deduplicated[0]["title"], "Sr. Software Engineer")
        
    def test_edge_cases(self):
        """Test edge cases"""
        # Empty entries
        self.assertEqual(self.resolver.deduplicate_entries([]), [])
        
        # None values
        entry = {"title": None, "company": "Tech Corp"}
        self.assertFalse(self.resolver.is_duplicate_entry(entry, [])[0])
        
        # Missing fields
        entry1 = {"title": "Engineer"}
        entry2 = {"company": "Tech Corp"}
        self.assertFalse(self.resolver.is_duplicate_entry(entry1, [entry2])[0])
        
        # Special characters
        entry1 = {"title": "Software Engineer (AI/ML)"}
        entry2 = {"title": "Software Engineer [AI/ML]"}
        self.assertTrue(self.resolver.is_duplicate_entry(entry1, [entry2])[0])

if __name__ == '__main__':
    unittest.main()