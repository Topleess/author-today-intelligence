import tempfile
import unittest
from pathlib import Path

from atintel.storage import (
    connect,
    ingest,
    ingest_rights_candidate,
    ingest_rights_case,
    rights_case_report,
)


class RightsCaseStorageTest(unittest.TestCase):
    def test_human_reviewed_likely_infringement_is_stored_with_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            db = connect(Path(td) / "test.sqlite3")
            case = {
                "schema_version": 1,
                "case_id": "CASE-2026-0001",
                "work_title": "Example Book",
                "rights_holder": "Example Author",
                "source_url": "https://example.org/item/1",
                "captured_at": "2026-07-17T12:00:00Z",
                "qualification": "likely_infringement",
                "qualification_reason": "Full chapter matched exactly",
                "reviewed_by_human": True,
                "legal_review_status": "not_reviewed",
                "capture_sha256": "a" * 64,
            }

            ingest_rights_case(db, case)

            row = db.execute(
                "SELECT qualification, reviewed_by_human, capture_sha256 FROM rights_cases WHERE case_id=?",
                (case["case_id"],),
            ).fetchone()
            self.assertEqual(row["qualification"], "likely_infringement")
            self.assertEqual(row["reviewed_by_human"], 1)
            self.assertEqual(row["capture_sha256"], "a" * 64)

    def test_model_cannot_mark_case_as_likely_infringement_without_human_review(self):
        with tempfile.TemporaryDirectory() as td:
            db = connect(Path(td) / "test.sqlite3")
            case = {
                "schema_version": 1,
                "case_id": "CASE-2026-0002",
                "work_title": "Example Book",
                "rights_holder": "Example Author",
                "source_url": "https://example.org/item/2",
                "captured_at": "2026-07-17T12:00:00Z",
                "qualification": "likely_infringement",
                "qualification_reason": "Model prediction only",
                "reviewed_by_human": False,
                "legal_review_status": "not_reviewed",
            }

            with self.assertRaisesRegex(ValueError, "human review"):
                ingest_rights_case(db, case)

    def test_unified_work_authors_candidate_and_case_report(self):
        with tempfile.TemporaryDirectory() as td:
            db = connect(Path(td) / "test.sqlite3")
            ingest(db, {
                "schema_version": 1,
                "captured_at": "2026-07-17T12:00:00Z",
                "source": {"class": "official_work_page", "url": "https://author.today/work/563328"},
                "works": [{
                    "work_id": 563328,
                    "title": "Абиссинец 1889. Том 1",
                    "author_name": "Сергей Насоновский, Сергей Щербатых",
                    "authors": [
                        {"name": "Сергей Насоновский", "slug": "nasonovsky", "position": 1},
                        {"name": "Сергей Щербатых", "slug": None, "position": 2},
                    ],
                    "url": "https://author.today/work/563328",
                }],
                "work_snapshots": [],
                "rankings": [],
            })
            self.assertEqual(
                [r["name"] for r in db.execute(
                    "SELECT a.name FROM authors a JOIN work_authors wa USING(author_id) "
                    "WHERE wa.work_id=563328 ORDER BY wa.position"
                )],
                ["Сергей Насоновский", "Сергей Щербатых"],
            )
            ingest_rights_candidate(db, {
                "schema_version": 1,
                "candidate_id": "CAND-2026-0001",
                "work_id": 563328,
                "source_url": "https://example.org/book",
                "observed_at": "2026-07-17T12:30:00Z",
                "page_title": "читать и скачать fb2",
                "access_status": "public_200",
                "capture_sha256": "b" * 64,
                "license_status": "unknown",
            })
            ingest_rights_case(db, {
                "schema_version": 1,
                "case_id": "CASE-2026-0001",
                "work_id": 563328,
                "candidate_id": "CAND-2026-0001",
                "work_title": "Абиссинец 1889. Том 1",
                "rights_holder": "requires confirmation by coauthors",
                "source_url": "https://example.org/book",
                "captured_at": "2026-07-17T12:30:00Z",
                "qualification": "unclear",
                "qualification_reason": "Text and licence status require confirmation",
                "reviewed_by_human": True,
                "legal_review_status": "not_reviewed",
                "capture_sha256": "b" * 64,
            })
            report = rights_case_report(db, "CASE-2026-0001")
            self.assertEqual(report["work"]["work_id"], 563328)
            self.assertEqual(report["work"]["authors"], ["Сергей Насоновский", "Сергей Щербатых"])
            self.assertEqual(report["candidate"]["license_status"], "unknown")
            self.assertFalse(report["legal_determination_completed"])


if __name__ == "__main__":
    unittest.main()
