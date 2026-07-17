import json, tempfile, unittest
from pathlib import Path
from atintel.storage import add_author_target, connect, ingest_file

class ManualImportTest(unittest.TestCase):
    def test_add_author_target_validates_and_canonicalizes(self):
        with tempfile.TemporaryDirectory() as d:
            db=connect(Path(d)/"x.sqlite3")
            self.assertEqual(add_author_target(db,"https://author.today/u/nasonovsky/","Сергей","2026-07-17T00:00:00Z"),"nasonovsky")
            self.assertEqual(tuple(db.execute("SELECT author_slug,profile_url,display_name FROM author_targets").fetchone()),("nasonovsky","https://author.today/u/nasonovsky","Сергей"))
            with self.assertRaises(ValueError): add_author_target(db,"https://evil.example/u/nasonovsky")

    def test_comment_evidence_chain(self):
        with tempfile.TemporaryDirectory() as d:
            db=connect(Path(d)/"x.sqlite3")
            ingest_file(db, Path(__file__).parents[1]/"examples/manual_private_import.synthetic.json")
            comment=db.execute("SELECT source_url,profile_url,body,parent_comment_id,thread_id,thread_level,statement_type,rating FROM comments").fetchone()
            tag=db.execute("SELECT taxonomy_path,stance,evidence_excerpt,confidence,derivation,confirmed FROM comment_tags").fetchone()
            self.assertTrue(comment["source_url"].startswith("https://author.today/work/"))
            self.assertEqual(tag["derivation"],"human")
            self.assertEqual(tag["confirmed"],1)
            self.assertIn(tag["evidence_excerpt"],comment["body"])

    def test_thread_and_statement_fields(self):
        data=json.loads((Path(__file__).parents[1]/"examples/manual_private_import.synthetic.json").read_text())
        comment=data["comments"][0]
        comment.update({"parent_comment_id":"parent-1","thread_id":"thread-1","thread_level":1,"statement_type":"observation","rating":3})
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"thread.json"; p.write_text(json.dumps(data))
            db=connect(Path(d)/"x.sqlite3"); ingest_file(db,p)
            row=db.execute("SELECT parent_comment_id,thread_id,thread_level,statement_type,rating FROM comments").fetchone()
            self.assertEqual(tuple(row),("parent-1","thread-1",1,"observation",3))

    def test_invalid_statement_type_rejected(self):
        data=json.loads((Path(__file__).parents[1]/"examples/manual_private_import.synthetic.json").read_text())
        data["comments"][0]["statement_type"]="psychological_profile"
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad-type.json"; p.write_text(json.dumps(data))
            with self.assertRaises(ValueError): ingest_file(connect(Path(d)/"x.sqlite3"),p)

    def test_invalid_tag_rejected(self):
        data=json.loads((Path(__file__).parents[1]/"examples/manual_private_import.synthetic.json").read_text())
        data["comments"][0]["tags"][0]["confidence"]=1.5
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.json"; p.write_text(json.dumps(data))
            with self.assertRaises(ValueError): ingest_file(connect(Path(d)/"x.sqlite3"),p)
