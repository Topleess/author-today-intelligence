from __future__ import annotations
import gzip, hashlib, json, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"
CC_INDEXES = "https://index.commoncrawl.org/collinfo.json"
UA = "author-today-intelligence/0.2 (+https://github.com/Topleess/author-today-intelligence)"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_target(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "author.today":
        raise ValueError("Only https://author.today URLs are supported")
    if not (parsed.path.startswith("/work/") or parsed.path.startswith("/u/")):
        raise ValueError("Only /work/ and /u/ targets are supported")
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def get_json(url: str, timeout: int = 60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Archive index returned HTTP {response.status}")
        return json.load(response)


def wayback_captures(target: str, limit: int = 20) -> list[dict]:
    target = validate_target(target)
    limit = max(1, min(int(limit), 50))
    query = urllib.parse.urlencode({
        "url": target, "output": "json", "filter": "statuscode:200",
        "fl": "timestamp,original,statuscode,mimetype,digest", "limit": limit,
        "collapse": "digest",
    })
    payload = get_json(f"{WAYBACK_CDX}?{query}")
    if not payload:
        return []
    header, *rows = payload
    return [dict(zip(header, row)) | {
        "source_class": "wayback_capture",
        "archive_url": f"https://web.archive.org/web/{row[0]}/{row[1]}",
    } for row in rows]


def cc_indexes(limit: int = 3) -> list[str]:
    rows = get_json(CC_INDEXES)
    if not rows:
        raise RuntimeError("Common Crawl has no indexes")
    return [row["id"] for row in rows[:limit]]

def latest_cc_index() -> str:
    return cc_indexes(1)[0]


def commoncrawl_captures(target: str, limit: int = 20, index: str | None = None) -> list[dict]:
    target = validate_target(target)
    limit = max(1, min(int(limit), 50))
    candidates = [index] if index else cc_indexes(3)
    query = urllib.parse.urlencode({"url": target, "output": "json", "matchType": "exact", "filter": "status:200"})
    lines, chosen = [], candidates[0]
    last_error = None
    for candidate in candidates:
        chosen = candidate
        url = f"https://index.commoncrawl.org/{candidate}-index?{query}"
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/x-ndjson"})
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=90) as response:
                    lines = response.read(2_000_000).decode("utf-8", "replace").splitlines()
                last_error = None
                break
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    lines, last_error = [], None
                    break
                last_error = exc
            except (TimeoutError, urllib.error.URLError) as exc:
                last_error = exc
            if attempt == 0:
                time.sleep(2)
        if last_error is None and lines:
            break
    if last_error is not None and not lines:
        raise RuntimeError(f"Common Crawl indexes unavailable after bounded retries: {last_error}")
    out = []
    for line in lines[:limit]:
        row = json.loads(line)
        out.append({
            "source_class": "commoncrawl_warc", "index": chosen,
            "timestamp": row.get("timestamp"), "url": row.get("url"),
            "status": row.get("status"), "mime": row.get("mime"),
            "digest": row.get("digest"), "filename": row.get("filename"),
            "offset": int(row["offset"]), "length": int(row["length"]),
        })
    return out


def retrieve_cc_record(capture: dict, max_bytes: int = 2_000_000) -> dict:
    filename = str(capture.get("filename", ""))
    offset, length = int(capture.get("offset", -1)), int(capture.get("length", -1))
    if not filename.startswith("crawl-data/") or offset < 0 or length <= 0 or length > max_bytes:
        raise ValueError("Invalid or oversized Common Crawl record coordinates")
    url = "https://data.commoncrawl.org/" + filename
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Range": f"bytes={offset}-{offset + length - 1}"})
    with urllib.request.urlopen(request, timeout=90) as response:
        compressed = response.read(max_bytes + 1)
        if len(compressed) > max_bytes:
            raise ValueError("Archive record exceeds configured limit")
    raw = gzip.decompress(compressed)
    digest = hashlib.sha256(raw).hexdigest()
    marker = raw.find(b"\r\n\r\n")
    remainder = raw[marker + 4:] if marker >= 0 else raw
    http_marker = remainder.find(b"\r\n\r\n")
    body = remainder[http_marker + 4:] if http_marker >= 0 else remainder
    return {"sha256": digest, "bytes": len(raw), "body": body, "retrieved_from": url}


def probe(target: str, output: str | Path, limit: int = 20) -> Path:
    target = validate_target(target)
    errors = []
    try:
        wayback = wayback_captures(target, limit)
    except Exception as exc:
        wayback = []
        errors.append({"source": "wayback", "error_type": type(exc).__name__, "message": str(exc)[:300]})
    try:
        commoncrawl = commoncrawl_captures(target, limit)
    except Exception as exc:
        commoncrawl = []
        errors.append({"source": "commoncrawl", "error_type": type(exc).__name__, "message": str(exc)[:300]})
    result = {
        "schema_version": 1, "target_url": target, "probed_at": utc_now(),
        "quality_note": "Archive captures are irregular control points, not a continuous time series.",
        "wayback": wayback, "commoncrawl": commoncrawl, "errors": errors,
    }
    path = Path(output); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
