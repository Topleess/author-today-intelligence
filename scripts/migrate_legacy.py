#!/usr/bin/env python3
"""Migrate preserved legacy Author.Today data into canonical SQLite."""
from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path
from atintel.storage import connect, ingest

OVERRIDES={563328:[{"name":"Сергей Насоновский","slug":"nasonovsky","position":1},{"name":"Сергей Щербатых","slug":"sherbatykh","position":2}]}

def legacy_authors(work):
    if int(work["work_id"]) in OVERRIDES:return OVERRIDES[int(work["work_id"])]
    names=[x.strip() for x in (work.get("author_name") or "").split(",") if x.strip()]
    return [{"name":name,"slug":work.get("author_slug") if position==1 else None,"position":position} for position,name in enumerate(names,1)]

def normalize(path):
    data=json.loads(path.read_text(encoding="utf-8"))
    if "error" in data:return None
    for w in data.get("works",[]):
        authors=legacy_authors(w)
        w["authors"]=authors
        if authors:w["author_name"]=', '.join(a['name'] for a in authors)
    return {"schema_version":1,"captured_at":data["captured_at"],"source":{"class":"legacy_public_snapshot","url":f"file://legacy/snapshots/{path.name}","original_sources":data.get("sources",{})},"works":data.get("works",[]),"work_snapshots":data.get("work_snapshots",[]),"rankings":data.get("rankings",[]),"comments":data.get("comments",[])}

def copy_analytics(db,path):
    src=sqlite3.connect(path);src.row_factory=sqlite3.Row
    tables={"author_snapshots":("captured_at","author_slug","subscribers","dynamic_rating","absolute_rating","works","series","comments_written"),"campaigns":("campaign_id","source","medium","campaign","content","landing_url","spend_rub"),"campaign_snapshots":("captured_at","campaign_id","clicks","work_views","library_adds","purchases","revenue_rub")}
    for table,cols in tables.items():
        for row in src.execute(f"SELECT {','.join(cols)} FROM {table}"):
            db.execute(f"INSERT OR REPLACE INTO {table}({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",tuple(row))
    db.commit()

def copy_evidence(db,path):
    src=sqlite3.connect(path);src.row_factory=sqlite3.Row;source_map={}
    for r in src.execute("SELECT * FROM sources"):
        db.execute("INSERT OR IGNORE INTO sources(source_class,source_url,captured_at,digest,metadata_json) VALUES(?,?,?,?,?)",(r['source_class'],r['source_url'],r['captured_at'],r['digest'],r['metadata_json']))
        source_map[r['source_id']]=db.execute("SELECT source_id FROM sources WHERE source_class=? AND source_url=? AND captured_at=?",(r['source_class'],r['source_url'],r['captured_at'])).fetchone()[0]
    for r in src.execute("SELECT * FROM works"):
        w=dict(r);authors=legacy_authors(w);w['authors']=authors
        if authors:w['author_name']=', '.join(a['name'] for a in authors)
        ingest(db,{"schema_version":1,"captured_at":"legacy","works":[w],"work_snapshots":[],"rankings":[]})
    for table,cols in {"work_snapshots":("captured_at","work_id","views","likes","comments","reviews","characters","status","price_rub","exclusive","published_at","modified_at","source_id"),"ranking_snapshots":("captured_at","ranking_url","ranking_type","position","work_id","source_id")}.items():
        for r in src.execute(f"SELECT {','.join(cols)} FROM {table}"):
            vals=list(r);vals[-1]=source_map.get(vals[-1]);db.execute(f"INSERT OR REPLACE INTO {table}({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",vals)
    direct={"archive_captures":("target_url","source_class","captured_at","archive_url","digest","locator_json","parser_version"),"reader_profiles":("profile_url","display_name","first_seen","last_seen"),"comment_tags":("comment_id","taxonomy_path","stance","evidence_excerpt","confidence","derivation","confirmed")}
    comments=("comment_id","work_id","chapter_ref","profile_url","display_name","body","source_url","published_at","imported_at","source_id","parent_comment_id","thread_id","thread_level","statement_type","rating")
    for r in src.execute(f"SELECT {','.join(comments)} FROM comments"):
        vals=list(r);vals[9]=source_map.get(vals[9]);db.execute(f"INSERT OR REPLACE INTO comments({','.join(comments)}) VALUES({','.join('?' for _ in comments)})",vals)
    for table,cols in direct.items():
        verb='INSERT OR IGNORE' if table=='archive_captures' else 'INSERT OR REPLACE'
        for r in src.execute(f"SELECT {','.join(cols)} FROM {table}"):db.execute(f"{verb} INTO {table}({','.join(cols)}) VALUES({','.join('?' for _ in cols)})",tuple(r))
    db.commit()

def main():
    p=argparse.ArgumentParser();p.add_argument('snapshot_dir',type=Path);p.add_argument('--db',required=True);p.add_argument('--analytics-db',type=Path);p.add_argument('--evidence-db',type=Path);a=p.parse_args();db=connect(a.db);imported=skipped=0
    for path in sorted(a.snapshot_dir.glob('*.json')):
        payload=normalize(path)
        if payload is None:skipped+=1;continue
        ingest(db,payload);imported+=1
    if a.analytics_db:copy_analytics(db,a.analytics_db)
    if a.evidence_db:copy_evidence(db,a.evidence_db)
    tables=("works","authors","work_authors","work_snapshots","ranking_snapshots","author_snapshots","archive_captures","comments","comment_tags","sources")
    print(json.dumps({"imported_files":imported,"skipped_error_files":skipped,"counts":{t:db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in tables}},ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()
