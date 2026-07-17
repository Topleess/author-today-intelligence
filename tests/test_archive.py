import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from atintel.archive import commoncrawl_captures, validate_target, wayback_captures

class ArchiveTest(unittest.TestCase):
    def test_target_allowlist(self):
        self.assertEqual(validate_target("https://author.today/work/123?x=1"), "https://author.today/work/123")
        for url in ("http://author.today/work/1", "https://evil.example/work/1", "https://author.today/account/"):
            with self.assertRaises(ValueError): validate_target(url)

    @patch("atintel.archive.get_json")
    def test_wayback_provenance(self, get_json):
        get_json.return_value=[["timestamp","original","statuscode","mimetype","digest"],["20200101000000","https://author.today/work/1","200","text/html","ABC"]]
        row=wayback_captures("https://author.today/work/1",1)[0]
        self.assertEqual(row["source_class"],"wayback_capture")
        self.assertIn("20200101000000",row["archive_url"])
