from __future__ import annotations
import json, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_BASE = "https://api.author.today/v1"

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

def request_json(path: str, params: dict | None = None) -> dict:
    url = f"{API_BASE}/{path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer guest",
        "Accept": "application/json",
        "User-Agent": "author-today-intelligence/0.1 (+https://github.com/)"
    })
    with urllib.request.urlopen(req, timeout=45) as response:
        content_type = response.headers.get("Content-Type", "")
        if response.status != 200 or "json" not in content_type.lower():
            raise RuntimeError(f"Unexpected API response: HTTP {response.status}, {content_type}")
        return json.load(response)

def normalize_search(payload: dict, source_url: str, captured_at: str) -> dict:
    rows = payload.get("searchResults")
    if not isinstance(rows, list):
        raise ValueError("API response has no searchResults list")
    works, snapshots, rankings = [], [], []
    for position, item in enumerate(rows, 1):
        work_id = int(item["id"])
        authors = []
        if item.get("authorFIO"):
            authors.append({"name": item["authorFIO"], "slug": item.get("authorUserName"), "position": 1, "confirmed": True})
        for prefix in ("coAuthor", "secondCoAuthor"):
            if item.get(f"{prefix}FIO") and item.get(f"{prefix}Confirmed"):
                authors.append({"name": item[f"{prefix}FIO"], "slug": item.get(f"{prefix}UserName"), "position": len(authors) + 1, "confirmed": True})
        works.append({
            "work_id": work_id,
            "title": item.get("title") or f"work {work_id}",
            "author_name": ", ".join(a["name"] for a in authors) or None,
            "author_slug": item.get("authorUserName"),
            "authors": authors,
            "series_id": item.get("seriesId"),
            "series_title": item.get("seriesTitle"),
            "url": f"https://author.today/work/{work_id}"
        })
        snapshots.append({
            "captured_at": captured_at,
            "work_id": work_id,
            "views": item.get("viewCount"),
            "likes": item.get("likeCount"),
            "comments": item.get("commentCount"),
            "reviews": item.get("reviewCount"),
            "characters": item.get("textLength"),
            "status": item.get("status"),
            "price_rub": item.get("price"),
            "exclusive": item.get("isExclusive"),
            "published_at": item.get("publishTime"),
            "modified_at": item.get("lastModificationTime")
        })
        rankings.append({
            "captured_at": captured_at,
            "ranking_url": source_url,
            "ranking_type": "catalog_search",
            "position": position,
            "work_id": work_id
        })
    return {"schema_version": 1, "captured_at": captured_at, "source": {"class": "documented_api", "url": source_url}, "works": works, "work_snapshots": snapshots, "rankings": rankings}

def collect_catalog(output: str | Path, sorting: str = "popular", extra: dict | None = None) -> Path:
    params = {"sorting": sorting}
    if extra: params.update(extra)
    query = urllib.parse.urlencode(params)
    source_url = f"{API_BASE}/catalog/search?{query}"
    captured_at = utc_now()
    payload = request_json("catalog/search", params=params)
    normalized = normalize_search(payload, source_url, captured_at)
    path = Path(output); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
