from __future__ import annotations
import gzip, hashlib, json, re, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"
UA = "author-today-intelligence/0.2 (+https://github.com/Topleess/author-today-intelligence)"
DEFAULT_CC_INDEX = "CC-MAIN-2026-25"
WORK_PATH = re.compile(r"/(?:work|audiobook)/[1-9][0-9]*")
PROFILE_PATH = re.compile(r"/u/[A-Za-z0-9_-]{1,80}")
WARC_PATH = re.compile(r"crawl-data/(CC-MAIN-[0-9]{4}-[0-9]{2})/segments/[A-Za-z0-9.]+/warc/[A-Za-z0-9._-]+\.warc\.gz")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_target(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "author.today" or parsed.port is not None:
        raise ValueError("Only canonical https://author.today URLs are supported")
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError("Credentials and fragments are not supported")
    if "%2f" in parsed.path.lower() or "%5c" in parsed.path.lower() or "*" in parsed.path:
        raise ValueError("Encoded separators and wildcards are not supported")
    if not (WORK_PATH.fullmatch(parsed.path) or PROFILE_PATH.fullmatch(parsed.path)):
        raise ValueError("Only exact /work/<numeric-id>, /audiobook/<numeric-id> and /u/<slug-or-id> targets are supported")
    return urllib.parse.urlunparse(("https", "author.today", parsed.path, "", "", ""))


def get_json(url: str, timeout: int = 60):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Archive index returned HTTP {response.status}")
        return json.load(response)


def wayback_captures(target: str, limit: int = 20) -> list[dict]:
    target = validate_target(target)
    limit = max(1, min(int(limit), 25))
    query = urllib.parse.urlencode([
        ("url", target), ("matchType", "exact"), ("output", "json"),
        ("filter", "statuscode:200"), ("filter", "mimetype:text/html"),
        ("fl", "timestamp,original,statuscode,mimetype,digest"),
        ("limit", str(limit)), ("collapse", "digest"),
    ])
    query_url = f"{WAYBACK_CDX}?{query}"
    payload = get_json(query_url)
    if not payload:
        return []
    header, *rows = payload
    return [dict(zip(header, row)) | {
        "source_class": "wayback_capture", "query_url": query_url,
        "archive_url": f"https://web.archive.org/web/{row[0]}id_/{row[1]}",
    } for row in rows]


def commoncrawl_captures(target: str, limit: int = 20, index: str | None = None) -> list[dict]:
    target = validate_target(target)
    limit = max(1, min(int(limit), 25))
    chosen = index or DEFAULT_CC_INDEX
    if not re.fullmatch(r"CC-MAIN-[0-9]{4}-[0-9]{2}", chosen):
        raise ValueError("Common Crawl index name is invalid")
    query = urllib.parse.urlencode({"url": target, "output": "json", "matchType": "exact", "filter": "status:200", "pageSize": limit})
    url = f"https://index.commoncrawl.org/{chosen}-index?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/x-ndjson"})
    lines, last_error = [], None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise ValueError("Common Crawl index response exceeds 2 MB")
                lines = raw.decode("utf-8", "strict").splitlines()
            last_error = None
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return []
            last_error = exc
        except (TimeoutError, UnicodeError, urllib.error.URLError) as exc:
            last_error = exc
        if attempt == 0:
            time.sleep(2)
    if last_error is not None:
        raise RuntimeError(f"Pinned Common Crawl index unavailable after bounded retry: {last_error}")
    out = []
    for line in lines[:limit]:
        row = json.loads(line)
        out.append({
            "source_class": "commoncrawl_warc", "index": chosen, "query_url": url,
            "timestamp": row.get("timestamp"), "url": row.get("url"),
            "status": row.get("status"), "mime": row.get("mime"),
            "digest": row.get("digest"), "filename": row.get("filename"),
            "offset": int(row["offset"]), "length": int(row["length"]),
        })
    return out


def retrieve_cc_record(capture: dict, max_bytes: int = 2_000_000) -> dict:
    filename = str(capture.get("filename", ""))
    offset, length = int(capture.get("offset", -1)), int(capture.get("length", -1))
    match = WARC_PATH.fullmatch(filename)
    if not match or match.group(1) != capture.get("index") or offset < 0 or length <= 0 or length > max_bytes:
        raise ValueError("Invalid or oversized Common Crawl record coordinates")
    url = "https://data.commoncrawl.org/" + filename
    range_end = offset + length - 1
    request = urllib.request.Request(url, headers={
        "User-Agent": UA, "Range": f"bytes={offset}-{range_end}", "Accept-Encoding": "identity",
    })
    with urllib.request.urlopen(request, timeout=90) as response:
        if response.status != 206 or urllib.parse.urlparse(response.geturl()).hostname != "data.commoncrawl.org":
            raise ValueError("Common Crawl retrieval did not return same-origin HTTP 206")
        content_range = response.headers.get("Content-Range", "")
        if not content_range.startswith(f"bytes {offset}-{range_end}/"):
            raise ValueError("Unexpected Content-Range")
        compressed = response.read(max_bytes + 1)
    if len(compressed) != length:
        raise ValueError("Archive byte count differs from indexed length")
    raw = gzip.decompress(compressed)
    if b"WARC-Type: response" not in raw[:4096]:
        raise ValueError("WARC member is not a response record")
    marker = raw.find(b"\r\n\r\n")
    remainder = raw[marker + 4:] if marker >= 0 else raw
    http_marker = remainder.find(b"\r\n\r\n")
    http_headers = remainder[:http_marker] if http_marker >= 0 else b""
    body = remainder[http_marker + 4:] if http_marker >= 0 else remainder
    if b"text/html" not in http_headers.lower():
        raise ValueError("Embedded response is not HTML")
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "compressed_sha256": hashlib.sha256(compressed).hexdigest(),
        "payload_sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(raw), "compressed_bytes": len(compressed), "body": body,
        "content_range": content_range, "retrieved_from": url,
    }


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
        "schema_version": 1, "url_normalizer_version": 2,
        "target_url": target, "probed_at": utc_now(),
        "quality_note": "Archive captures are irregular control points, not continuous history or proof of what users saw.",
        "wayback": wayback, "commoncrawl": commoncrawl, "errors": errors,
    }
    path = Path(output); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
