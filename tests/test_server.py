import json
import re
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from atintel.server import Handler, ThreadingHTTPServer
from atintel.storage import connect, ingest_file


class ServerContractTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "x.sqlite3"
        ingest_file(
            connect(self.db),
            Path(__file__).parents[1]
            / "examples"
            / "manual_private_import.synthetic.json",
        )
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.db_path = str(self.db)
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=3) as response:
            return response.status, json.load(response)

    def get_text(self, path):
        with urllib.request.urlopen(self.base + path, timeout=3) as response:
            return response.status, dict(response.headers), response.read().decode("utf-8")

    def add_snapshot(self, captured_at, views):
        db = connect(self.db)
        source_id = db.execute(
            "SELECT source_id FROM sources ORDER BY source_id LIMIT 1"
        ).fetchone()[0]
        db.execute(
            """INSERT INTO work_snapshots(
                captured_at,work_id,views,likes,comments,source_id
            ) VALUES(?,?,?,?,?,?)""",
            (captured_at, 900001, views, 10, 1, source_id),
        )
        db.commit()
        db.close()

    def test_decision_first_dashboard_structure_contract(self):
        status, headers, html = self.get_text("/")
        self.assertEqual(status, 200)
        self.assertTrue(headers["Content-Type"].startswith("text/html"))
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])

        for section_id, label in (
            ("overview", "Обзор"),
            ("books", "Книги"),
            ("rankings", "Топы"),
            ("readers", "Читатели"),
            ("sources", "Источники"),
        ):
            self.assertIn(f'<section id="{section_id}"', html)
            self.assertIn(f'data-go-section="{section_id}"', html)
            self.assertIn(label, html)

        desktop = re.search(
            r'<nav class="desktop-nav".*?</nav>', html, re.DOTALL
        ).group()
        mobile = re.search(
            r'<nav class="mobile-nav".*?</nav>', html, re.DOTALL
        ).group()
        self.assertEqual(desktop.count("data-go-section="), 5)
        self.assertEqual(mobile.count("data-go-section="), 4)
        self.assertNotIn('data-go-section="sources"', mobile)
        self.assertIn('aria-label="Основные разделы"', mobile)

        self.assertIn('class="skip-link"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn(":focus-visible", html)
        self.assertIn("@media (max-width: 390px)", html)
        self.assertIn("overflow-x: hidden", html)
        self.assertIn("overflow-wrap: anywhere", html)
        self.assertIn("viewport-fit=cover", html)
        self.assertNotIn(" onclick=", html)

    def test_progressive_evidence_and_deterministic_attention_contract(self):
        _, _, html = self.get_text("/")
        self.assertIn("Сначала ответ, затем доказательство", html)
        self.assertIn("Показать данные", html)
        self.assertGreaterEqual(html.count('<details class="evidence">'), 8)
        self.assertIn("Проверить источник и ограничения", html)
        self.assertIn("function buildAttention()", html)
        self.assertIn("return signals.slice(0, 3);", html)
        self.assertIn("function workSignals()", html)
        self.assertIn("function rankSignals()", html)
        self.assertIn("collator.compare", html)
        self.assertIn("популярные", html)
        self.assertIn("-е место в top-25", html)
        self.assertIn("Архивные точки не соединяются с регулярными", html)

    def test_sparse_state_copy_contract(self):
        _, _, html = self.get_text("/")
        for state_name in ("0", "1", "2+"):
            self.assertIn(f'data-sparse-state="{state_name}"', html)
        self.assertIn("Данных пока нет", html)
        self.assertIn("Динамику считать рано", html)
        self.assertIn("Две точки, это ещё не устойчивый тренд", html)
        self.assertIn('data-state="${count === 0 ? "0" : count === 1 ? "1" : "2+"}"', html)

    def test_snapshot_route_supplies_zero_one_and_two_plus_states(self):
        status, rows = self.get("/api/work/900001/snapshots")
        self.assertEqual((status, rows), (200, []))

        self.add_snapshot("2026-07-17T00:00:00Z", 100)
        _, rows = self.get("/api/work/900001/snapshots")
        self.assertEqual(len(rows), 1)

        self.add_snapshot("2026-07-17T06:00:00Z", 125)
        _, rows = self.get("/api/work/900001/snapshots")
        self.assertEqual(len(rows), 2)
        self.assertEqual([row["views"] for row in rows], [100, 125])
        self.assertEqual(
            set(rows[0]),
            {"captured_at", "views", "likes", "comments", "source_class", "source_url"},
        )

    def test_existing_read_only_api_shapes_are_preserved(self):
        expected_summary = {
            "portfolio works",
            "snapshots",
            "rights candidates",
            "rights cases",
            "archive captures",
            "comments",
            "confirmed tags",
            "hypotheses",
        }
        _, summary = self.get("/api/summary")
        self.assertEqual(set(summary), expected_summary)

        _, comments = self.get("/api/comments")
        self.assertEqual(
            set(comments[0]),
            {
                "comment_id", "work_id", "chapter_ref", "profile_url", "body",
                "source_url", "published_at", "parent_comment_id", "thread_id",
                "thread_level", "statement_type", "rating", "taxonomy_path",
                "stance", "evidence_excerpt", "confidence", "derivation", "confirmed",
            },
        )
        _, tags = self.get("/api/tags")
        self.assertEqual(
            set(tags[0]),
            {"taxonomy_path", "stance", "count", "avg_confidence"},
        )
        _, profiles = self.get("/api/profiles")
        self.assertEqual(
            set(profiles[0]),
            {
                "profile_url", "display_name", "comment_count", "work_count",
                "first_seen", "last_seen", "observed_topics",
            },
        )
        _, quality = self.get("/api/source-quality")
        self.assertEqual(set(quality[0]), {"source_class", "count", "quality"})

    def test_read_only_and_no_secret_fields(self):
        status, health = self.get("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(
            health["private_browser_automation"],
            "disabled_by_platform_terms",
        )
        payload = []
        for path in (
            "/api/health", "/api/summary", "/api/works", "/api/archives",
            "/api/tags", "/api/profiles", "/api/comments",
            "/api/comments/synthetic-comment-1", "/api/authors",
            "/api/rankings", "/api/source-quality", "/api/rights/candidates",
            "/api/rights/cases",
        ):
            payload.append(self.get(path)[1])
        text = json.dumps(payload).lower()
        for forbidden in (
            '"password"', '"cookie"', '"cookies"', '"authorization"',
            '"localstorage"', '"otp"', '"token"', '"session"',
        ):
            self.assertNotIn(forbidden, text)
        request = urllib.request.Request(
            self.base + "/api/summary", data=b"{}", method="POST"
        )
        with self.assertRaises(urllib.error.HTTPError) as context:
            urllib.request.urlopen(request, timeout=3)
        self.assertEqual(context.exception.code, 405)


if __name__ == "__main__":
    unittest.main()
