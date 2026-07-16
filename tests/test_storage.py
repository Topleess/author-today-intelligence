import json, sqlite3, tempfile, unittest
from pathlib import Path
from atintel.storage import connect, ingest_file, latest_report

class StorageTest(unittest.TestCase):
    def test_ingest_fixture_and_report(self):
        with tempfile.TemporaryDirectory() as td:
            db=connect(Path(td)/"test.sqlite3")
            fixture=Path(__file__).parents[1]/"examples"/"sample_snapshot.json"
            ingest_file(db,fixture)
            self.assertEqual(db.execute("select count(*) from works").fetchone()[0],1)
            self.assertEqual(db.execute("select comments from work_snapshots").fetchone()[0],10)
            self.assertIn("Example Book",latest_report(db))

if __name__ == "__main__": unittest.main()
