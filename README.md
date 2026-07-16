# Author.Today Intelligence

API-first snapshots, SQLite storage, and reusable agent workflows for researching Author.Today books and catalog cohorts.

> **Status:** research prototype. It collects observable facts and calculates changes. It does **not** reverse-engineer the ranking formula or prove why a book grew.

## What it does

- calls the documented Author.Today API with guest access;
- stores timestamped raw JSON evidence;
- normalizes books and cumulative metrics into SQLite;
- keeps ranking/cohort position together with the full query;
- compares repeated snapshots;
- gives AI agents a safe workflow for facts, hypotheses, and next experiments.

## What it does not do

- bypass authentication, CAPTCHA, paywalls, or access controls;
- publish, edit, or message on behalf of an author;
- expose client cookies, dashboards, manuscripts, or private analytics;
- claim that correlation proves causation;
- guarantee stable access to undocumented web endpoints.

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .

atintel collect --sorting popular --output raw/popular.json
atintel init --db analytics.sqlite3
atintel ingest raw/popular.json --db analytics.sqlite3
atintel report --db analytics.sqlite3
```

No third-party Python dependency is required for the API-first core.

## Architecture

```text
Documented API -> append-only raw snapshot -> normalization -> SQLite
                                                        |
                                                        v
                              deltas -> evidence -> hypothesis -> experiment
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/AGENT_WORKFLOW.md](docs/AGENT_WORKFLOW.md), and [docs/ROADMAP.md](docs/ROADMAP.md).

## Agent reuse

A portable skill lives at [`skills/author-today-intelligence/SKILL.md`](skills/author-today-intelligence/SKILL.md). An agent can use it to:

1. choose documented API before HTML;
2. preserve raw evidence and timestamps;
3. separate facts from interpretations;
4. recommend a measurable next experiment;
5. avoid presenting `createOrder` or public totals as confirmed sales.

## Data ethics

Public comments are user-generated content. Store only what is necessary, quote minimally, preserve provenance, and provide deletion/export controls in any user-facing product. Private author reports require the author's informed permission.

## Русское описание

Проект собирает регулярные снимки публичных показателей книг Author.Today и сохраняет историю. Один снимок отвечает «что сейчас», серия снимков — «что изменилось». Причину роста можно обсуждать только после сопоставления изменений с выходом глав, рекламой, ценой и другими событиями.

## License

MIT. The website, API, content, and trademarks belong to their respective owners. Respect Author.Today terms and rate limits.
