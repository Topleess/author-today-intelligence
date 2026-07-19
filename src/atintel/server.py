from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from urllib.parse import parse_qs, urlparse

from .storage import connect, init, rights_case_report


def _rows(db, sql, params=()):
    return [dict(r) for r in db.execute(sql, params).fetchall()]


def dashboard_html() -> bytes:
    """Return the packaged, read-only dashboard document."""
    return files("atintel").joinpath("dashboard.html").read_bytes()


class Handler(BaseHTTPRequestHandler):
    server_version = "ATIntel/0.2"

    def log_message(self, fmt, *args):
        print("http", self.address_string(), fmt % args)

    def _json(self, value, status=200):
        raw = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            raw = dashboard_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'none'",
            )
            self.end_headers()
            self.wfile.write(raw)
            return

        db = connect(self.server.db_path)
        init(db)
        if parsed.path == "/api/health":
            return self._json(
                {
                    "status": "ok",
                    "private_browser_automation": "disabled_by_platform_terms",
                }
            )
        if parsed.path == "/api/summary":
            return self._json(
                {
                    "portfolio works": db.execute(
                        "SELECT COUNT(DISTINCT work_id) FROM work_snapshots"
                    ).fetchone()[0],
                    "snapshots": db.execute(
                        "SELECT COUNT(*) FROM work_snapshots"
                    ).fetchone()[0],
                    "rights candidates": db.execute(
                        "SELECT COUNT(*) FROM rights_candidates"
                    ).fetchone()[0],
                    "rights cases": db.execute(
                        "SELECT COUNT(*) FROM rights_cases"
                    ).fetchone()[0],
                    "archive captures": db.execute(
                        "SELECT COUNT(*) FROM archive_captures"
                    ).fetchone()[0],
                    "comments": db.execute(
                        "SELECT COUNT(*) FROM comments"
                    ).fetchone()[0],
                    "confirmed tags": db.execute(
                        "SELECT COUNT(*) FROM comment_tags WHERE confirmed=1"
                    ).fetchone()[0],
                    "hypotheses": "0 (not generated)",
                }
            )
        if parsed.path == "/api/authors":
            return self._json(
                _rows(
                    db,
                    "SELECT author_slug,profile_url,display_name,added_at FROM author_targets ORDER BY added_at",
                )
            )
        if parsed.path == "/api/works":
            return self._json(
                _rows(
                    db,
                    """SELECT w.work_id,w.title,w.url,s.views,s.likes,s.comments,s.captured_at,COALESCE(src.source_class,'unknown') source_class FROM works w JOIN work_snapshots s ON s.work_id=w.work_id AND s.captured_at=(SELECT MAX(s2.captured_at) FROM work_snapshots s2 WHERE s2.work_id=w.work_id) LEFT JOIN sources src ON src.source_id=s.source_id ORDER BY COALESCE(s.views,-1) DESC""",
                )
            )
        if parsed.path == "/api/rankings":
            return self._json(
                _rows(
                    db,
                    """SELECT replace(substr(r.ranking_type,7,instr(substr(r.ranking_type,7),':')-1),'-',' ') category,CASE WHEN r.ranking_type LIKE '%:popular' THEN 'popular' WHEN r.ranking_type LIKE '%:trending' THEN 'trending' ELSE 'other' END mode,r.position,w.title,r.captured_at,r.ranking_url FROM ranking_snapshots r JOIN works w USING(work_id) WHERE r.ranking_type LIKE 'genre:%' AND EXISTS(SELECT 1 FROM work_snapshots s WHERE s.work_id=r.work_id) ORDER BY r.captured_at DESC,r.ranking_type,r.position""",
                )
            )
        if parsed.path == "/api/source-quality":
            return self._json(
                _rows(
                    db,
                    """SELECT source_class,COUNT(*) count,CASE WHEN source_class='public_guest' THEN 'regular public snapshot' WHEN source_class LIKE 'archive%' OR source_class IN ('wayback','commoncrawl') THEN 'irregular archive point' WHEN source_class LIKE 'manual%' THEN 'selected manual evidence' ELSE 'source metadata available' END quality FROM sources GROUP BY source_class ORDER BY source_class""",
                )
            )

        match = re.fullmatch(r"/api/work/(\d+)/snapshots", parsed.path)
        if match:
            return self._json(
                _rows(
                    db,
                    """SELECT s.captured_at,s.views,s.likes,s.comments,COALESCE(src.source_class,'unknown') source_class,COALESCE(src.source_url,'') source_url FROM work_snapshots s LEFT JOIN sources src USING(source_id) WHERE s.work_id=? ORDER BY s.captured_at""",
                    (int(match.group(1)),),
                )
            )
        if parsed.path == "/api/archives":
            return self._json(
                _rows(
                    db,
                    "SELECT source_class,target_url,captured_at,archive_url,digest,locator_json FROM archive_captures ORDER BY captured_at DESC LIMIT 100",
                )
            )
        if parsed.path == "/api/rights/candidates":
            return self._json(
                _rows(db, "SELECT candidate_id,work_id,source_url,observed_at,page_title,access_status,capture_sha256,license_status FROM rights_candidates ORDER BY observed_at DESC")
            )
        if parsed.path == "/api/rights/cases":
            return self._json(
                _rows(db, "SELECT case_id,work_id,candidate_id,work_title,rights_holder,source_url,captured_at,qualification,qualification_reason,reviewed_by_human,legal_review_status FROM rights_cases ORDER BY captured_at DESC")
            )
        rights_match = re.fullmatch(r"/api/rights/cases/([^/]+)", parsed.path)
        if rights_match:
            try:
                return self._json(rights_case_report(db, rights_match.group(1)))
            except KeyError:
                return self._json({"error": "not found"}, 404)
        if parsed.path == "/api/tags":
            return self._json(
                _rows(
                    db,
                    "SELECT taxonomy_path,stance,COUNT(*) count,ROUND(AVG(confidence),2) avg_confidence FROM comment_tags GROUP BY taxonomy_path,stance ORDER BY count DESC",
                )
            )
        if parsed.path == "/api/profiles":
            return self._json(
                _rows(
                    db,
                    """SELECT c.profile_url,MAX(c.display_name) display_name,COUNT(DISTINCT c.comment_id) comment_count,COUNT(DISTINCT c.work_id) work_count,MIN(c.published_at) first_seen,MAX(c.published_at) last_seen,GROUP_CONCAT(DISTINCT t.taxonomy_path) observed_topics FROM comments c LEFT JOIN comment_tags t USING(comment_id) WHERE c.profile_url IS NOT NULL GROUP BY c.profile_url ORDER BY comment_count DESC LIMIT 200""",
                )
            )
        if parsed.path == "/api/comments":
            tag = parse_qs(parsed.query).get("tag", [None])[0]
            sql = """SELECT c.comment_id,c.work_id,c.chapter_ref,c.profile_url,c.body,c.source_url,c.published_at,c.parent_comment_id,c.thread_id,c.thread_level,c.statement_type,c.rating,t.taxonomy_path,t.stance,t.evidence_excerpt,t.confidence,t.derivation,t.confirmed FROM comments c LEFT JOIN comment_tags t USING(comment_id)"""
            return self._json(
                _rows(
                    db,
                    sql
                    + (" WHERE t.taxonomy_path=?" if tag else "")
                    + " ORDER BY c.published_at DESC LIMIT 200",
                    (tag,) if tag else (),
                )
            )

        match = re.fullmatch(r"/api/comments/([^/]+)", parsed.path)
        if match:
            row = db.execute(
                "SELECT * FROM comments WHERE comment_id=?", (match.group(1),)
            ).fetchone()
            if not row:
                return self._json({"error": "not found"}, 404)
            value = dict(row)
            value["tags"] = _rows(
                db,
                "SELECT taxonomy_path,stance,evidence_excerpt,confidence,derivation,confirmed FROM comment_tags WHERE comment_id=?",
                (match.group(1),),
            )
            return self._json(value)
        return self._json({"error": "not found"}, 404)

    def do_POST(self):
        return self._json(
            {
                "error": "API is read-only; use local CLI for public collection and user-selected manual imports"
            },
            405,
        )


def serve(db_path: str, host: str = "127.0.0.1", port: int = 8787):
    server = ThreadingHTTPServer((host, port), Handler)
    server.db_path = db_path
    print(f"Serving evidence UI on http://{host}:{port}")
    server.serve_forever()
