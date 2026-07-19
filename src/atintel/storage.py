from __future__ import annotations
import json, sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS works(
  work_id INTEGER PRIMARY KEY, title TEXT NOT NULL, author_name TEXT,
  author_slug TEXT, series_id INTEGER, series_title TEXT, url TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS authors(
  author_id INTEGER PRIMARY KEY, name TEXT NOT NULL, slug TEXT UNIQUE,
  UNIQUE(name, slug)
);
CREATE TABLE IF NOT EXISTS work_authors(
  work_id INTEGER NOT NULL, author_id INTEGER NOT NULL, position INTEGER NOT NULL,
  PRIMARY KEY(work_id, author_id), UNIQUE(work_id, position),
  FOREIGN KEY(work_id) REFERENCES works(work_id), FOREIGN KEY(author_id) REFERENCES authors(author_id)
);
CREATE TABLE IF NOT EXISTS sources(
  source_id INTEGER PRIMARY KEY, source_class TEXT NOT NULL, source_url TEXT NOT NULL,
  captured_at TEXT NOT NULL, digest TEXT, metadata_json TEXT NOT NULL DEFAULT '{}',
  UNIQUE(source_class, source_url, captured_at)
);
CREATE TABLE IF NOT EXISTS work_snapshots(
  id INTEGER PRIMARY KEY, captured_at TEXT NOT NULL, work_id INTEGER NOT NULL,
  views INTEGER, likes INTEGER, comments INTEGER, reviews INTEGER,
  characters INTEGER, status TEXT, price_rub REAL, exclusive INTEGER,
  published_at TEXT, modified_at TEXT, source_id INTEGER,
  FOREIGN KEY(work_id) REFERENCES works(work_id), FOREIGN KEY(source_id) REFERENCES sources(source_id),
  UNIQUE(captured_at, work_id)
);
CREATE TABLE IF NOT EXISTS ranking_snapshots(
  id INTEGER PRIMARY KEY, captured_at TEXT NOT NULL, ranking_url TEXT NOT NULL,
  ranking_type TEXT NOT NULL, position INTEGER NOT NULL, work_id INTEGER NOT NULL,
  source_id INTEGER, FOREIGN KEY(work_id) REFERENCES works(work_id),
  FOREIGN KEY(source_id) REFERENCES sources(source_id), UNIQUE(captured_at, ranking_url, position)
);
CREATE TABLE IF NOT EXISTS archive_captures(
  capture_id INTEGER PRIMARY KEY, target_url TEXT NOT NULL, source_class TEXT NOT NULL,
  captured_at TEXT, archive_url TEXT, digest TEXT, locator_json TEXT NOT NULL,
  parser_version TEXT NOT NULL DEFAULT 'index-only-v1', UNIQUE(source_class, target_url, captured_at, digest)
);
CREATE TABLE IF NOT EXISTS reader_profiles(
  profile_url TEXT PRIMARY KEY, display_name TEXT, first_seen TEXT, last_seen TEXT
);
CREATE TABLE IF NOT EXISTS comments(
  comment_id TEXT PRIMARY KEY, work_id INTEGER, chapter_ref TEXT, profile_url TEXT,
  display_name TEXT, body TEXT NOT NULL, source_url TEXT NOT NULL,
  published_at TEXT, imported_at TEXT NOT NULL, source_id INTEGER,
  FOREIGN KEY(work_id) REFERENCES works(work_id), FOREIGN KEY(source_id) REFERENCES sources(source_id)
);
CREATE TABLE IF NOT EXISTS author_snapshots(
  id INTEGER PRIMARY KEY, captured_at TEXT NOT NULL, author_slug TEXT NOT NULL,
  subscribers INTEGER, dynamic_rating INTEGER, absolute_rating INTEGER,
  works INTEGER, series INTEGER, comments_written INTEGER,
  UNIQUE(captured_at, author_slug)
);
CREATE TABLE IF NOT EXISTS campaigns(
  campaign_id TEXT PRIMARY KEY, source TEXT, medium TEXT, campaign TEXT,
  content TEXT, landing_url TEXT, spend_rub REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS campaign_snapshots(
  id INTEGER PRIMARY KEY, captured_at TEXT NOT NULL, campaign_id TEXT NOT NULL,
  clicks INTEGER, work_views INTEGER, library_adds INTEGER, purchases INTEGER, revenue_rub REAL,
  FOREIGN KEY(campaign_id) REFERENCES campaigns(campaign_id), UNIQUE(captured_at, campaign_id)
);
CREATE TABLE IF NOT EXISTS comment_tags(
  comment_id TEXT NOT NULL, taxonomy_path TEXT NOT NULL, stance TEXT NOT NULL,
  evidence_excerpt TEXT NOT NULL, confidence REAL NOT NULL,
  derivation TEXT NOT NULL, confirmed INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY(comment_id, taxonomy_path, stance), FOREIGN KEY(comment_id) REFERENCES comments(comment_id)
);
CREATE TABLE IF NOT EXISTS rights_cases(
  case_id TEXT PRIMARY KEY,
  work_title TEXT NOT NULL,
  rights_holder TEXT NOT NULL,
  source_url TEXT NOT NULL,
  captured_at TEXT NOT NULL,
  qualification TEXT NOT NULL CHECK(qualification IN (
    'authorized','reference_only','quotation_review','likely_infringement','unclear'
  )),
  qualification_reason TEXT NOT NULL,
  reviewed_by_human INTEGER NOT NULL CHECK(reviewed_by_human IN (0,1)),
  legal_review_status TEXT NOT NULL,
  capture_sha256 TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS rights_candidates(
  candidate_id TEXT PRIMARY KEY, work_id INTEGER NOT NULL, source_url TEXT NOT NULL,
  observed_at TEXT NOT NULL, page_title TEXT, access_status TEXT NOT NULL,
  capture_sha256 TEXT, license_status TEXT NOT NULL CHECK(license_status IN ('authorized','unknown','denied')),
  metadata_json TEXT NOT NULL DEFAULT '{}', FOREIGN KEY(work_id) REFERENCES works(work_id)
);
CREATE INDEX IF NOT EXISTS idx_work_snapshots_work_time ON work_snapshots(work_id, captured_at);
CREATE INDEX IF NOT EXISTS idx_comments_work ON comments(work_id, published_at);
CREATE INDEX IF NOT EXISTS idx_rights_cases_status ON rights_cases(qualification, legal_review_status);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    db = sqlite3.connect(path); db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON"); return db


def init(db: sqlite3.Connection) -> None:
    db.executescript(SCHEMA)
    columns = {row[1] for row in db.execute("PRAGMA table_info(rights_cases)")}
    if "work_id" not in columns:
        db.execute("ALTER TABLE rights_cases ADD COLUMN work_id INTEGER REFERENCES works(work_id)")
    if "candidate_id" not in columns:
        db.execute("ALTER TABLE rights_cases ADD COLUMN candidate_id TEXT REFERENCES rights_candidates(candidate_id)")
    comment_columns = {row[1] for row in db.execute("PRAGMA table_info(comments)")}
    for name, definition in {"parent_comment_id": "TEXT", "thread_id": "TEXT", "thread_level": "INTEGER", "statement_type": "TEXT", "rating": "REAL"}.items():
        if name not in comment_columns:
            db.execute(f"ALTER TABLE comments ADD COLUMN {name} {definition}")
    db.commit()


def _source(db: sqlite3.Connection, data: dict) -> int | None:
    source = data.get("source") or {}
    source_class, url, captured = source.get("class"), source.get("url"), data.get("captured_at")
    if not all((source_class, url, captured)):
        return None
    db.execute("INSERT OR IGNORE INTO sources(source_class,source_url,captured_at,metadata_json) VALUES(?,?,?,?)",
               (source_class, url, captured, json.dumps(source, ensure_ascii=False)))
    return db.execute("SELECT source_id FROM sources WHERE source_class=? AND source_url=? AND captured_at=?",
                      (source_class, url, captured)).fetchone()[0]


def ingest(db: sqlite3.Connection, data: dict) -> None:
    init(db)
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported or missing schema_version")
    source_id = _source(db, data)
    for w in data.get("works", []):
        cols = ["work_id","title","author_name","author_slug","series_id","series_title","url"]
        db.execute(f"INSERT INTO works({','.join(cols)}) VALUES({','.join('?' for _ in cols)}) ON CONFLICT(work_id) DO UPDATE SET title=excluded.title,author_name=excluded.author_name,author_slug=excluded.author_slug,series_id=excluded.series_id,series_title=excluded.series_title,url=excluded.url", [w.get(c) for c in cols])
        authors = w.get("authors") or []
        if not authors and w.get("author_name"):
            authors = [{"name": w["author_name"], "slug": w.get("author_slug"), "position": 1}]
        db.execute("DELETE FROM work_authors WHERE work_id=?", (w["work_id"],))
        for position, author in enumerate(authors, 1):
            name, slug = author.get("name"), author.get("slug")
            if not name:
                raise ValueError("Work author misses name")
            row = db.execute("SELECT author_id FROM authors WHERE slug=?", (slug,)).fetchone() if slug else db.execute("SELECT author_id FROM authors WHERE name=? AND slug IS NULL", (name,)).fetchone()
            if row:
                author_id = row[0]
                db.execute("UPDATE authors SET name=? WHERE author_id=?", (name, author_id))
            else:
                author_id = db.execute("INSERT INTO authors(name,slug) VALUES(?,?)", (name, slug)).lastrowid
            db.execute("INSERT INTO work_authors(work_id,author_id,position) VALUES(?,?,?)", (w["work_id"], author_id, author.get("position", position)))
    for s in data.get("work_snapshots", []):
        cols = ["captured_at","work_id","views","likes","comments","reviews","characters","status","price_rub","exclusive","published_at","modified_at","source_id"]
        values = [s.get(c) for c in cols[:-1]] + [source_id]
        db.execute(f"INSERT OR REPLACE INTO work_snapshots({','.join(cols)}) VALUES({','.join('?' for _ in cols)})", values)
    for r in data.get("rankings", []):
        cols = ["captured_at","ranking_url","ranking_type","position","work_id","source_id"]
        values = [r.get(c) for c in cols[:-1]] + [source_id]
        db.execute(f"INSERT OR REPLACE INTO ranking_snapshots({','.join(cols)}) VALUES({','.join('?' for _ in cols)})", values)
    for c in data.get("comments", []):
        required = ("comment_id", "body", "source_url", "imported_at")
        if not all(c.get(k) is not None for k in required):
            raise ValueError("Manual comment import misses required provenance fields")
        if c.get("profile_url"):
            db.execute("INSERT INTO reader_profiles(profile_url,display_name,first_seen,last_seen) VALUES(?,?,?,?) ON CONFLICT(profile_url) DO UPDATE SET display_name=excluded.display_name,last_seen=excluded.last_seen",
                       (c["profile_url"], c.get("display_name"), c.get("published_at"), c.get("published_at")))
        cols = ["comment_id","work_id","chapter_ref","profile_url","display_name","body","source_url","published_at","imported_at","source_id"]
        db.execute(f"INSERT OR REPLACE INTO comments({','.join(cols)}) VALUES({','.join('?' for _ in cols)})", [c.get(k) for k in cols[:-1]] + [source_id])
        for t in c.get("tags", []):
            if t.get("derivation") not in ("human", "rule", "model"):
                raise ValueError("Tag derivation must be human, rule, or model")
            confidence = float(t.get("confidence", 0))
            if not 0 <= confidence <= 1:
                raise ValueError("Tag confidence must be between 0 and 1")
            db.execute("INSERT OR REPLACE INTO comment_tags(comment_id,taxonomy_path,stance,evidence_excerpt,confidence,derivation,confirmed) VALUES(?,?,?,?,?,?,?)",
                       (c["comment_id"], t["taxonomy_path"], t["stance"], t["evidence_excerpt"], confidence, t["derivation"], int(bool(t.get("confirmed")))))
    db.commit()


def ingest_file(db: sqlite3.Connection, path: str | Path, max_bytes: int = 10_000_000) -> None:
    path = Path(path)
    if path.stat().st_size > max_bytes:
        raise ValueError("Import exceeds 10 MB limit")
    ingest(db, json.loads(path.read_text(encoding="utf-8")))


def ingest_rights_case(db: sqlite3.Connection, data: dict) -> None:
    init(db)
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported or missing schema_version")
    required = (
        "case_id", "work_title", "rights_holder", "source_url", "captured_at",
        "qualification", "qualification_reason", "reviewed_by_human", "legal_review_status",
    )
    if any(data.get(key) is None for key in required):
        raise ValueError("Rights case misses required evidence fields")
    allowed = {"authorized", "reference_only", "quotation_review", "likely_infringement", "unclear"}
    if data["qualification"] not in allowed:
        raise ValueError("Unsupported rights case qualification")
    if data["qualification"] == "likely_infringement" and not data["reviewed_by_human"]:
        raise ValueError("likely_infringement requires human review")
    cols = list(required) + ["capture_sha256", "work_id", "candidate_id"]
    values = [int(bool(data.get(key))) if key == "reviewed_by_human" else data.get(key) for key in cols]
    db.execute(
        f"INSERT INTO rights_cases({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",
        values,
    )
    db.commit()


def ingest_rights_candidate(db: sqlite3.Connection, data: dict) -> None:
    init(db)
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported or missing schema_version")
    required = ("candidate_id", "work_id", "source_url", "observed_at", "access_status", "license_status")
    if any(data.get(key) is None for key in required):
        raise ValueError("Rights candidate misses required fields")
    if data["license_status"] not in {"authorized", "unknown", "denied"}:
        raise ValueError("Unsupported candidate license status")
    cols = list(required) + ["page_title", "capture_sha256", "metadata_json"]
    values = [data.get(key) for key in cols[:-1]] + [json.dumps(data.get("metadata", {}), ensure_ascii=False)]
    db.execute(f"INSERT INTO rights_candidates({','.join(cols)}) VALUES({','.join('?' for _ in cols)}) ON CONFLICT(candidate_id) DO UPDATE SET source_url=excluded.source_url,observed_at=excluded.observed_at,page_title=excluded.page_title,access_status=excluded.access_status,capture_sha256=excluded.capture_sha256,license_status=excluded.license_status,metadata_json=excluded.metadata_json", values)
    db.commit()


def rights_case_report(db: sqlite3.Connection, case_id: str) -> dict:
    init(db)
    case = db.execute("SELECT * FROM rights_cases WHERE case_id=?", (case_id,)).fetchone()
    if not case:
        raise KeyError(case_id)
    value = dict(case)
    work = db.execute("SELECT work_id,title,url FROM works WHERE work_id=?", (value.get("work_id"),)).fetchone()
    candidate = db.execute("SELECT * FROM rights_candidates WHERE candidate_id=?", (value.get("candidate_id"),)).fetchone()
    authors = [] if not work else [row[0] for row in db.execute("SELECT a.name FROM authors a JOIN work_authors wa USING(author_id) WHERE wa.work_id=? ORDER BY wa.position", (work["work_id"],))]
    return {"case": value, "work": ({**dict(work), "authors": authors} if work else None), "candidate": (dict(candidate) if candidate else None), "legal_determination_completed": value["legal_review_status"] == "completed", "safety_note": "Technical similarity does not establish infringement; legal review is separate."}


def ingest_archive_probe(db: sqlite3.Connection, path: str | Path) -> int:
    init(db); data = json.loads(Path(path).read_text(encoding="utf-8")); target = data["target_url"]; count = 0
    for key in ("wayback", "commoncrawl"):
        for c in data.get(key, []):
            captured = c.get("timestamp")
            db.execute("INSERT OR IGNORE INTO archive_captures(target_url,source_class,captured_at,archive_url,digest,locator_json) VALUES(?,?,?,?,?,?)",
                       (target, c["source_class"], captured, c.get("archive_url"), c.get("digest"), json.dumps(c, ensure_ascii=False)))
            count += db.execute("SELECT changes()").fetchone()[0]
    db.commit(); return count


def latest_report(db: sqlite3.Connection) -> str:
    lines = ["LATEST SNAPSHOTS"]
    query = """SELECT w.title,w.author_name,s.views,s.likes,s.comments,s.captured_at
    FROM work_snapshots s JOIN works w USING(work_id)
    JOIN (SELECT work_id,MAX(captured_at) AS m FROM work_snapshots GROUP BY work_id) x
      ON x.work_id=s.work_id AND x.m=s.captured_at
    ORDER BY COALESCE(s.views, -1) DESC"""
    for title, author, views, likes, comments, ts in db.execute(query):
        like_rate = None if not views or likes is None else 100 * likes / views
        rate = "n/a" if like_rate is None else f"{like_rate:.2f}%"
        lines.append(f"- {title} — {author or 'unknown'}: views={views}; likes={likes}; comments={comments}; like_rate={rate}; at={ts}")
    repeated = db.execute("SELECT COUNT(*) FROM (SELECT work_id FROM work_snapshots GROUP BY work_id HAVING COUNT(*) > 1)").fetchone()[0]
    lines += ["", f"works_with_2plus_snapshots={repeated}", "Repeated observations support deltas; they do not prove causation by themselves."]
    return "\n".join(lines)
