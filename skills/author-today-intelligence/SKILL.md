---
name: author-today-intelligence
description: Collect and reason about Author.Today catalog, work, ranking, and author analytics using an API-first evidence workflow.
version: 0.1.0
license: MIT
---

# Author.Today Intelligence

Use when an agent must monitor books, compare catalog cohorts, explain observed changes, analyze reader feedback, or design an author experiment.

## Workflow

1. Read `docs/SOURCES.md` and verify live documented API behavior.
2. Use `atintel collect` for a timestamped catalog snapshot.
3. Preserve the complete source query and source class.
4. Ingest into SQLite with `atintel ingest`.
5. Require repeated snapshots for deltas.
6. Label statements as observed fact, hypothesis, missing evidence, or experiment.
7. Never claim the ranking formula, exact advertising causality, unique readership from public views, or paid sales from order intent.
8. Keep private dashboards, cookies, credentials, manuscripts, and client datasets outside the repository.
9. Ask for explicit approval before publishing, messaging, changing a work, or launching an ad.

## Output contract

Return:

- **What changed** — evidence and period;
- **Why it may have changed** — bounded hypothesis;
- **What is unknown** — missing source;
- **What to do next** — one measurable experiment.
