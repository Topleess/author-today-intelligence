import unittest
from atintel.api import normalize_search

class ApiTest(unittest.TestCase):
    def test_normalize_search(self):
        payload={"searchResults":[{"id":7,"title":"T","authorFIO":"A","viewCount":100,"likeCount":5,"commentCount":2,"reviewCount":1,"textLength":123,"status":"Free","price":0,"isExclusive":False}]}
        out=normalize_search(payload,"https://example.invalid/query","2026-01-01T00:00:00Z")
        self.assertEqual(out["schema_version"],1)
        self.assertEqual(out["works"][0]["work_id"],7)
        self.assertEqual(out["work_snapshots"][0]["likes"],5)
        self.assertEqual(out["rankings"][0]["position"],1)
    def test_missing_search_results_fails(self):
        with self.assertRaises(ValueError): normalize_search({},"x","t")

if __name__ == "__main__": unittest.main()
