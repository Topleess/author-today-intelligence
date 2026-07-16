from __future__ import annotations
import json, sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS works(
  work_id INTEGER PRIMARY KEY, title TEXT NOT NULL, author_name TEXT,
  author_slug TEXT, series_id INTEGER, series_title TEXT, url TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS work_snapshots(
  id INTEGER PRIMARY KEY, captured_at TEXT NOT NULL, work_id INTEGER NOT NULL,
  views INTEGER, likes INTEGER, comments INTEGER, reviews INTEGER,
  characters INTEGER, status TEXT, price_rub REAL, exclusive INTEGER,
  published_at TEXT, modified_at TEXT,
  FOREIGN KEY(work_id) REFERENCES works(work_id), UNIQUE(captured_at, work_id)
);
CREATE TABLE IF NOT EXISTS ranking_snapshots(
  id INTEGER PRIMARY KEY, captured_at TEXT NOT NULL, ranking_url TEXT NOT NULL,
  ranking_type TEXT NOT NULL, position INTEGER NOT NULL, work_id INTEGER NOT NULL,
  FOREIGN KEY(work_id) REFERENCES works(work_id),
  UNIQUE(captured_at, ranking_url, position)
);
CREATE INDEX IF NOT EXISTS idx_work_snapshots_work_time ON work_snapshots(work_id, captured_at);
"""

def connect(path: str | Path) -> sqlite3.Connection:
    db = sqlite3.connect(path); db.execute("PRAGMA foreign_keys=ON"); return db

def init(db: sqlite3.Connection) -> None:
    db.executescript(SCHEMA); db.commit()

def ingest(db: sqlite3.Connection, data: dict) -> None:
    init(db)
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported or missing schema_version")
    for w in data.get("works", []):
        cols = ["work_id","title","author_name","author_slug","series_id","series_title","url"]
        db.execute(f"INSERT INTO works({','.join(cols)}) VALUES({','.join('?' for _ in cols)}) ON CONFLICT(work_id) DO UPDATE SET title=excluded.title,author_name=excluded.author_name,author_slug=excluded.author_slug,series_id=excluded.series_id,series_title=excluded.series_title,url=excluded.url", [w.get(c) for c in cols])
    for s in data.get("work_snapshots", []):
        cols = ["captured_at","work_id","views","likes","comments","reviews","characters","status","price_rub","exclusive","published_at","modified_at"]
        db.execute(f"INSERT OR REPLACE INTO work_snapshots({','.join(cols)}) VALUES({','.join('?' for _ in cols)})", [s.get(c) for c in cols])
    for r in data.get("rankings", []):
        cols = ["captured_at","ranking_url","ranking_type","position","work_id"]
        db.execute(f"INSERT OR REPLACE INTO ranking_snapshots({','.join(cols)}) VALUES({','.join('?' for _ in cols)})", [r.get(c) for c in cols])
    db.commit()

def ingest_file(db: sqlite3.Connection, path: str | Path) -> None:
    ingest(db, json.loads(Path(path).read_text(encoding="utf-8")))

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
