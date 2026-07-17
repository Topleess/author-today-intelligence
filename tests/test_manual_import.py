import json, tempfile, unittest
from pathlib import Path
from atintel.storage import connect, ingest_file

class ManualImportTest(unittest.TestCase):
    def test_comment_evidence_chain(self):
        with tempfile.TemporaryDirectory() as d:
            db=connect(Path(d)/"x.sqlite3")
            ingest_file(db, Path(__file__).parents[1]/"examples/manual_private_import.synthetic.json")
            comment=db.execute("SELECT source_url,profile_url,body FROM comments").fetchone()
            tag=db.execute("SELECT taxonomy_path,stance,evidence_excerpt,confidence,derivation,confirmed FROM comment_tags").fetchone()
            self.assertTrue(comment["source_url"].startswith("https://author.today/work/"))
            self.assertEqual(tag["derivation"],"human")
            self.assertEqual(tag["confirmed"],1)
            self.assertIn(tag["evidence_excerpt"],comment["body"])

    def test_invalid_tag_rejected(self):
        data=json.loads((Path(__file__).parents[1]/"examples/manual_private_import.synthetic.json").read_text())
        data["comments"][0]["tags"][0]["confidence"]=1.5
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.json"; p.write_text(json.dumps(data))
            with self.assertRaises(ValueError): ingest_file(connect(Path(d)/"x.sqlite3"),p)
