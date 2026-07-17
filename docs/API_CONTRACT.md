# Local read-only API contract

Base URL: `http://127.0.0.1:8787`

| Route | Purpose |
|---|---|
| `GET /api/health` | Readiness and private-automation policy status |
| `GET /api/summary` | Counts by evidence class |
| `GET /api/works` | Works with latest deterministic snapshot |
| `GET /api/work/{id}/snapshots` | Raw time-series points and source URLs |
| `GET /api/archives` | Wayback/Common Crawl locators and timestamps |
| `GET /api/tags` | Aggregated reviewable comment tags |
| `GET /api/profiles` | Local observable activity only: comment/work counts, dates and evidence-linked topics |
| `GET /api/comments?tag=...` | Tag drilldown to excerpt, full comment, profile and original |
| `GET /api/comments/{id}` | One comment and all derived tags |

All POST requests return HTTP 405. There are no endpoints for credentials, browser state, arbitrary paths/SQL/URLs, publishing, editing, messaging, or model-generated insights.

The UI calculates visible deltas from the raw points returned by `/api/work/{id}/snapshots`. A single point explicitly displays that at least two observations are required. The application reports zero generated hypotheses by default.
