# Architecture

## Supported evidence layers

1. **Documented API** — default automated source for public catalog/work facts.
2. **Wayback/Common Crawl** — irregular historical control points with archive provenance.
3. **User-selected manual export** — local private-data path obtained through normal site navigation.
4. **Derived calculation** — deterministic formula linked to raw source records.
5. **Interpretation** — separately labelled hypothesis, never stored as raw fact.

Automated authenticated browser collection is not supported because the current public offer explicitly restricts script-based collection/interactions. See `RULES_AUDIT.md`.

## Pipeline

```text
public API ───────────────┐
archive indexes/WARC ────┼─> normalized evidence -> SQLite -> read-only API/UI -> optional agent
manual selected export ──┘
```

## Local deployment

```text
volume-init (one shot, CAP_CHOWN only)
           ↓
public-sync (opt-in, non-root) -> named volume
           ↓
controller (non-root, read-only rootfs) -> 127.0.0.1:8787
```

The controller API contains no arbitrary URL fetch, file read, SQL, credentials, browser state or write/action endpoints. All POST requests return HTTP 405.

## Why SQLite

SQLite makes the tracer-bullet portable, inspectable, restart-safe and easy to export. A hosted multi-user product is intentionally out of scope.

## Agent role

The application works without an agent. An agent may read the narrow local API to explain already visible records, but deterministic code calculates numbers. Every explanation must preserve fact/correlation/hypothesis labels and link to the same raw points shown to the human.

See `LOCAL_APP.md`, `API_CONTRACT.md`, `MANUAL_IMPORT.md` and `READER_OBSERVATIONS.md`.
