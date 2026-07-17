# Local application architecture

## Supported pipeline

```text
Documented Author.Today API ─┐
Wayback / Common Crawl ──────┼─> local CLI -> SQLite -> read-only HTTP API -> evidence UI / agent
User-selected manual export ─┘
```

The application is local-first. Docker publishes the controller only on `127.0.0.1:8787`. SQLite and raw public snapshots live in a named Docker volume.

## Why no authenticated Chrome worker ships

The current public offer prohibits using programs/scripts to collect information or interact with the site except its navigation tools. That explicit restriction triggers the project's stop condition. An automated authenticated browser worker remains rejected unless Author.Today grants written permission defining the allowed routes and retention.

The safe private-data path is a file the user obtained through normal site navigation and explicitly selected for local import. The importer accepts normalized JSON, not credentials or browser state.

## Containers

### `volume-init`

A one-shot container with only `CAP_CHOWN`. It changes the named volume owner to UID 10001 and exits. It has no network workflow and no long-lived process.

### `public-sync`

An opt-in Compose profile. It calls the documented guest API, writes one raw JSON snapshot and imports it into SQLite. It runs without Linux capabilities.

### `controller`

A non-root, read-only-root-filesystem container. It reads SQLite and serves the local UI/API. Runtime state is restricted to `/data` plus a small `noexec,nosuid,nodev` tmpfs. All HTTP POST requests return 405.

## Agent boundary

The agent may use only:

- `GET /api/health`
- `GET /api/summary`
- `GET /api/works`
- `GET /api/work/{id}/snapshots`
- `GET /api/archives`
- `GET /api/tags`
- `GET /api/comments[?tag=...]`
- `GET /api/comments/{id}`

The API has no credential, browser-profile, filesystem, arbitrary SQL, arbitrary URL fetch, publish, edit, or message endpoint.

## Future permission-gated extension

If written permission is obtained, a browser worker must be a separate service with its own profile volume and narrow typed protocol. The controller must never mount that volume. Login/CAPTCHA/2FA remain human-only, and the worker may return only schema-validated report data plus non-secret status metadata.
