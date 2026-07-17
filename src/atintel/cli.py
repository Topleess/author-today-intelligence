from __future__ import annotations
import argparse
from .api import collect_catalog
from .archive import probe
from .server import serve
from .storage import connect, init, ingest_archive_probe, ingest_file, latest_report


def main() -> None:
    parser = argparse.ArgumentParser(prog="atintel")
    sub = parser.add_subparsers(dest="command", required=True)
    collect = sub.add_parser("collect", help="Collect one documented-API catalog snapshot")
    collect.add_argument("--sorting", default="popular"); collect.add_argument("--output", required=True)
    bootstrap = sub.add_parser("bootstrap", help="Collect and ingest one public snapshot")
    bootstrap.add_argument("--sorting", default="popular"); bootstrap.add_argument("--output", required=True); bootstrap.add_argument("--db", default="analytics.sqlite3")
    create = sub.add_parser("init", help="Initialize SQLite")
    create.add_argument("--db", default="analytics.sqlite3")
    ingest = sub.add_parser("ingest", help="Ingest a normalized public or manually exported snapshot")
    ingest.add_argument("snapshot"); ingest.add_argument("--db", default="analytics.sqlite3")
    archive = sub.add_parser("archive", help="Probe bounded Wayback/Common Crawl evidence for one URL")
    archive.add_argument("url"); archive.add_argument("--output", required=True); archive.add_argument("--limit", type=int, default=20)
    archive_ingest = sub.add_parser("archive-ingest", help="Ingest archive probe evidence")
    archive_ingest.add_argument("probe"); archive_ingest.add_argument("--db", default="analytics.sqlite3")
    report = sub.add_parser("report", help="Print latest facts and readiness")
    report.add_argument("--db", default="analytics.sqlite3")
    server = sub.add_parser("serve", help="Run local read-only evidence UI/API")
    server.add_argument("--db", default="analytics.sqlite3"); server.add_argument("--host", default="127.0.0.1"); server.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    if args.command == "collect": print(collect_catalog(args.output, sorting=args.sorting))
    elif args.command == "bootstrap":
        path=collect_catalog(args.output, sorting=args.sorting); db=connect(args.db); ingest_file(db,path); print(path)
    elif args.command == "init":
        db=connect(args.db); init(db); print(args.db)
    elif args.command == "ingest":
        db=connect(args.db); ingest_file(db,args.snapshot); print(args.snapshot)
    elif args.command == "archive": print(probe(args.url,args.output,args.limit))
    elif args.command == "archive-ingest":
        db=connect(args.db); print(ingest_archive_probe(db,args.probe))
    elif args.command == "serve": serve(args.db,args.host,args.port)
    else:
        db=connect(args.db); print(latest_report(db))
