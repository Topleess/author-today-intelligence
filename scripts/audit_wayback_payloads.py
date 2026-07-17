#!/usr/bin/env python3
"""Retrieve a bounded set of Wayback captures and audit metric availability."""
from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import html
import json
import re
import urllib.request
from pathlib import Path

UA = "author-today-intelligence/0.2 (+https://github.com/Topleess/author-today-intelligence)"


def number(value: str | None) -> int | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", html.unescape(value))
    return int(digits) if digits else None


def first(patterns: tuple[str, ...], text: str) -> int | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.I | re.S)
        if match:
            return number(match.group(1))
    return None


def retrieve(item: dict) -> dict:
    request = urllib.request.Request(item["archive_url"], headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=90) as response:
        raw = response.read(2_000_001)
        status = response.status
    if len(raw) > 2_000_000:
        raise ValueError("capture exceeds 2 MB compressed")
    compressed_sha256 = hashlib.sha256(raw).hexdigest()
    if raw.startswith(b"\x1f\x8b"):
        raw = gzip.decompress(raw)
    if len(raw) > 8_000_000:
        raise ValueError("capture exceeds 8 MB decoded")
    text = raw.decode("utf-8", "replace")
    metrics = {
        "views": first((r'data-hint=["\']Просмотры\s*·\s*([^"\']+)',), text),
        "likes": first((r'likeCount\s*:\s*(\d+)', r'data-hint=["\']Понравилось\s*·\s*([^"\']+)'), text),
        # The work page often archives commentTotalCount=0 as a JS placeholder.
        # Only a server-rendered data-hint is admissible as historical evidence.
        "comments": first((r'data-hint=["\']Комментарии\s*·\s*([^"\']+)',), text),
        "reviews": first((r'href=["\'][^"\']+/reviews["\'][^>]*>.*?<span>Рецензии</span>\s*<span[^>]*>·</span>\s*([^<\s]+)', r'data-hint=["\']Рецензии\s*·\s*([^"\']+)'), text),
    }
    title_match = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
    return {
        "timestamp": item.get("timestamp"),
        "original": item.get("original"),
        "archive_url": item["archive_url"],
        "status": status,
        "decoded_bytes": len(raw),
        "compressed_sha256": compressed_sha256,
        "decoded_sha256": hashlib.sha256(raw).hexdigest(),
        "title": html.unescape(re.sub(r"\s+", " ", title_match.group(1))).strip() if title_match else None,
        "metrics": metrics,
        "metric_count": sum(value is not None for value in metrics.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("coverage", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-captures", type=int, default=100)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    coverage = json.loads(args.coverage.read_text(encoding="utf-8"))
    jobs = []
    for target in coverage["targets"]:
        for capture in target["wayback"]:
            jobs.append((target, capture))
    if len(jobs) > max(1, min(args.max_captures, 100)):
        raise SystemExit(f"refusing {len(jobs)} captures above explicit cap")

    def run(job: tuple[dict, dict]) -> dict:
        target, capture = job
        base = {"work_id": target.get("work_id"), "work_title": target.get("title")}
        try:
            return base | retrieve(capture)
        except Exception as exc:
            return base | {"timestamp": capture.get("timestamp"), "archive_url": capture.get("archive_url"), "error": {"type": type(exc).__name__, "message": str(exc)[:300]}}

    workers = max(1, min(args.workers, 3))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        captures = list(pool.map(run, jobs))
    usable = sum(row.get("metrics", {}).get("views") is not None and row.get("metrics", {}).get("likes") is not None for row in captures)
    result = {
        "schema_version": 1,
        "quality_note": "Archived metrics are sparse control points. They must not be treated as a continuous time series.",
        "capture_count": len(captures),
        "usable_capture_count": usable,
        "captures": captures,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"capture_count": len(captures), "usable_capture_count": usable, "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
