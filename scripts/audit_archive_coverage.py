#!/usr/bin/env python3
"""Bounded archive-coverage audit for an explicit list of Author.Today URLs."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
from datetime import datetime, timezone
from pathlib import Path

from atintel.archive import commoncrawl_captures, validate_target, wayback_captures


def audit_one(item: dict, limit: int) -> dict:
    target = validate_target(str(item["url"]))
    result = {"work_id": item.get("work_id"), "title": item.get("title"), "url": target, "wayback": [], "commoncrawl": [], "errors": []}
    for name, function in (("wayback", wayback_captures), ("commoncrawl", commoncrawl_captures)):
        try:
            result[name] = function(target, limit)
        except Exception as exc:  # preserve independent source failure as evidence
            result["errors"].append({"source": name, "type": type(exc).__name__, "message": str(exc)[:300]})
    timestamps = [row.get("timestamp") for source in ("wayback", "commoncrawl") for row in result[source] if row.get("timestamp")]
    result["capture_count"] = len(result["wayback"]) + len(result["commoncrawl"])
    result["first_capture"] = min(timestamps) if timestamps else None
    result["last_capture"] = max(timestamps) if timestamps else None
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path, help="JSON array of explicit {work_id,title,url} objects")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    items = json.loads(args.manifest.read_text(encoding="utf-8"))
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        raise SystemExit("manifest must contain 1..100 explicit targets")
    workers = max(1, min(args.workers, 4))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(lambda item: audit_one(item, args.limit), items))
    covered = sum(row["capture_count"] > 0 for row in rows)
    result = {
        "schema_version": 1,
        "audited_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "quality_note": "Index captures are irregular evidence points, not continuous history. This audit does not retrieve or parse every archived payload.",
        "target_count": len(rows),
        "covered_target_count": covered,
        "coverage_ratio": covered / len(rows),
        "targets": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"target_count": len(rows), "covered_target_count": covered, "coverage_ratio": result["coverage_ratio"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
