# Author.Today Intelligence

A local-first, evidence-first research tool for Author.Today. It collects public snapshots through the documented API, stores them in SQLite, probes Wayback/Common Crawl for historical control points, imports only user-selected private exports, and exposes a read-only local UI/API.

> **Status:** verified tracer-bullet, not a production SaaS. It shows facts, formulas and provenance. It does not reverse-engineer rankings or invent causal explanations.

## What works now

- documented Author.Today guest API collection;
- timestamped raw JSON plus SQLite history;
- bounded per-URL Wayback/Common Crawl probe;
- exact Common Crawl WARC-range retrieval library with SHA-256 evidence;
- local manual import for author-selected reports/comments;
- drilldown: tag → evidence excerpt → full comment → profile/original URL;
- deterministic graph/table UI at `http://127.0.0.1:8787`;
- read-only agent API with no credential/browser/filesystem endpoints;
- Docker restart-safe storage and tests.

## Important private-access boundary

The current Author.Today public offer explicitly restricts using programs/scripts to collect information or interact with the site. Therefore this repository **does not ship automated authenticated Chrome collection**. Local execution does not override that restriction.

Private data is supported only through a file the user obtained through normal navigation and explicitly selected for local import. Passwords, cookies, OTPs, Authorization headers, browser profiles and storage state are not accepted. See [RULES_AUDIT.md](docs/RULES_AUDIT.md) and [MANUAL_IMPORT.md](docs/MANUAL_IMPORT.md).

## Docker onboarding

Requirements: Docker Engine with Compose.

```bash
git clone https://github.com/Topleess/author-today-intelligence.git
cd author-today-intelligence

# One public snapshot: collect + ingest into the local named volume
docker compose --profile sync run --rm public-sync

# Start read-only local UI/API
docker compose up -d controller
```

Open: <http://127.0.0.1:8787>

Verify:

```bash
curl http://127.0.0.1:8787/api/health
curl http://127.0.0.1:8787/api/summary
```

Collect another point later:

```bash
docker compose --profile sync run --rm public-sync
```

Stop without deleting data:

```bash
docker compose down
```

Delete the local database and snapshots:

```bash
docker compose down -v
```

## Python CLI

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .

atintel bootstrap --sorting popular --output raw/popular.json --db analytics.sqlite3
atintel archive https://author.today/work/100705 --limit 10 --output raw/archive.json
atintel archive-ingest raw/archive.json --db analytics.sqlite3
atintel ingest examples/manual_private_import.synthetic.json --db analytics.sqlite3
atintel serve --db analytics.sqlite3
```

No third-party Python runtime dependency is required.

## Architecture

```text
Documented API ──────────────┐
Wayback / Common Crawl ──────┼─> CLI -> local SQLite -> read-only API/UI -> agent
User-selected manual export ─┘
```

See:

- [Local application](docs/LOCAL_APP.md)
- [API contract](docs/API_CONTRACT.md)
- [Archive evidence](docs/ARCHIVE_PROBE.md)
- [Reader observations](docs/READER_OBSERVATIONS.md)
- [Permission-gated browser design](docs/PERMISSION_GATED_BROWSER.md)
- [Agent workflow](docs/AGENT_WORKFLOW.md)
- [Data model](docs/DATA_MODEL.md)

## Trust model

- numbers are calculated by deterministic code;
- raw points and source URLs remain visible;
- one point is not a trend;
- correlation is not causation;
- archive captures are irregular control points, not continuous history;
- model tags are unconfirmed until reviewed;
- the UI reports zero generated hypotheses by default.

## Agent reuse

The portable skill at [`skills/author-today-intelligence/SKILL.md`](skills/author-today-intelligence/SKILL.md) instructs an agent to use documented sources first, preserve evidence, separate facts from hypotheses and avoid unsupported sales/ranking claims. The skill is optional; the local application works without an agent.

## License

MIT. Author.Today, its website, API, content and trademarks belong to their respective owners. Respect current platform terms, privacy rights and rate limits.
