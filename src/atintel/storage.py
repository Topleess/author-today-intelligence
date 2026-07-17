from __future__ import annotations
import json, sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS works(
  work_id INTEGER PRIMARY KEY, title TEXT NOT NULL, author_name TEXT,
  author_slug TEXT, series_id INTEGER, series_title TEXT, url TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sources(
  source_id INTEGER PRIMARY KEY, source_class TEXT NOT NULL, source_url TEXT NOT NULL,
  captured_at TEXT NOT NULL, digest TEXT, metadata_json TEXT NOT NULL DEFAULT '{}',
  UNIQUE(source_class, source_url, captured_at)
);
CREATE TABLE IF NOT EXISTS author_targets(
  author_slug TEXT PRIMARY KEY, profile_url TEXT NOT NULL UNIQUE,
  display_name TEXT, added_at TEXT NOT NULL
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
  parent_comment_id TEXT, thread_id TEXT, thread_level INTEGER,
  statement_type TEXT, rating INTEGER,
  FOREIGN KEY(work_id) REFERENCES works(work_id), FOREIGN KEY(source_id) REFERENCES sources(source_id)
);
CREATE TABLE IF NOT EXISTS comment_tags(
  comment_id TEXT NOT NULL, taxonomy_path TEXT NOT NULL, stance TEXT NOT NULL,
  evidence_excerpt TEXT NOT NULL, confidence REAL NOT NULL,
  derivation TEXT NOT NULL, confirmed INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY(comment_id, taxonomy_path, stance), FOREIGN KEY(comment_id) REFERENCES comments(comment_id)
);
CREATE INDEX IF NOT EXISTS idx_work_snapshots_work_time ON work_snapshots(work_id, captured_at);
CREATE INDEX IF NOT EXISTS idx_comments_work ON comments(work_id, published_at);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    db = sqlite3.connect(path); db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON"); return db


def init(db: sqlite3.Connection) -> None:
    db.executescript(SCHEMA)
    existing = {row[1] for row in db.execute("PRAGMA table_info(comments)")}
    migrations = {
        "parent_comment_id": "TEXT", "thread_id": "TEXT", "thread_level": "INTEGER",
        "statement_type": "TEXT", "rating": "INTEGER",
    }
    for column, kind in migrations.items():
        if column not in existing:
            db.execute(f"ALTER TABLE comments ADD COLUMN {column} {kind}")
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
        statement_type = c.get("statement_type")
        if statement_type not in (None, "observation", "question", "praise", "criticism", "suggestion", "author_reply", "service"):
            raise ValueError("Unsupported comment statement_type")
        level = c.get("thread_level")
        if level is not None and (not isinstance(level, int) or level < 0 or level > 20):
            raise ValueError("thread_level must be an integer between 0 and 20")
        cols = ["comment_id","work_id","chapter_ref","profile_url","display_name","body","source_url","published_at","imported_at","parent_comment_id","thread_id","thread_level","statement_type","rating","source_id"]
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


def ingest_archive_probe(db: sqlite3.Connection, path: str | Path) -> int:
    init(db); data = json.loads(Path(path).read_text(encoding="utf-8")); target = data["target_url"]; count = 0
    for key in ("wayback", "commoncrawl"):
        for c in data.get(key, []):
            captured = c.get("timestamp")
            db.execute("INSERT OR IGNORE INTO archive_captures(target_url,source_class,captured_at,archive_url,digest,locator_json) VALUES(?,?,?,?,?,?)",
                       (target, c["source_class"], captured, c.get("archive_url"), c.get("digest"), json.dumps(c, ensure_ascii=False)))
            count += db.execute("SELECT changes()").fetchone()[0]
    db.commit(); return count


def add_author_target(db: sqlite3.Connection, profile_url: str, display_name: str | None = None, added_at: str | None = None) -> str:
    from datetime import datetime, timezone
    from urllib.parse import urlparse
    import re
    init(db)
    parsed = urlparse(profile_url.strip())
    if parsed.scheme != "https" or parsed.netloc.lower() != "author.today":
        raise ValueError("Author URL must use https://author.today")
    match = re.fullmatch(r"/u/([A-Za-z0-9_.-]+)/?", parsed.path)
    if not match or parsed.query or parsed.fragment:
        raise ValueError("Expected an Author.Today profile URL like https://author.today/u/name")
    slug = match.group(1)
    canonical = f"https://author.today/u/{slug}"
    timestamp = added_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    db.execute("INSERT INTO author_targets(author_slug,profile_url,display_name,added_at) VALUES(?,?,?,?) ON CONFLICT(author_slug) DO UPDATE SET profile_url=excluded.profile_url,display_name=COALESCE(excluded.display_name,author_targets.display_name)",
               (slug, canonical, display_name, timestamp))
    db.commit(); return slug


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
