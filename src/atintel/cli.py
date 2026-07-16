from __future__ import annotations
import argparse
from .api import collect_catalog
from .storage import connect, init, ingest_file, latest_report

def main() -> None:
    parser = argparse.ArgumentParser(prog="atintel")
    sub = parser.add_subparsers(dest="command", required=True)
    collect = sub.add_parser("collect", help="Collect one documented-API catalog snapshot")
    collect.add_argument("--sorting", default="popular")
    collect.add_argument("--output", required=True)
    create = sub.add_parser("init", help="Initialize SQLite")
    create.add_argument("--db", default="analytics.sqlite3")
    ingest = sub.add_parser("ingest", help="Ingest a normalized snapshot")
    ingest.add_argument("snapshot"); ingest.add_argument("--db", default="analytics.sqlite3")
    report = sub.add_parser("report", help="Print latest facts and readiness")
    report.add_argument("--db", default="analytics.sqlite3")
    args = parser.parse_args()
    if args.command == "collect": print(collect_catalog(args.output, sorting=args.sorting))
    elif args.command == "init":
        db=connect(args.db); init(db); print(args.db)
    elif args.command == "ingest":
        db=connect(args.db); ingest_file(db,args.snapshot); print(args.snapshot)
    else:
        db=connect(args.db); print(latest_report(db))
