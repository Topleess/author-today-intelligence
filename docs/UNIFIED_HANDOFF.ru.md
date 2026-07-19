# Handoff: unified Author.Today analytics + rights monitoring

Date: 2026-07-17

## Canonical project

`/opt/data/projects/author-today-intelligence`

The legacy `/opt/data/author-today-analytics` directory was not modified. Byte-identical copies of both legacy SQLite databases and all JSON snapshots are preserved under `data/legacy/`.

## Implemented

- normalized `authors` and `work_authors` tables;
- collection of confirmed API coauthors;
- additive migration for old databases;
- preserved analytics author/campaign tables and evidence comments/archives;
- normalized `rights_candidates` linked to works;
- rights cases linked to work and candidate;
- enforced human review before `likely_infringement`;
- CLI ingest/report commands;
- read-only rights API and dashboard section;
- migrated Sergey pilot with two candidates and one neutral `unclear` case;
- integrated research, legal map, offer, pilot and example documents.

## Current canonical data

- 413 works;
- 364 normalized authors and 416 work-author links;
- 110 deduplicated work snapshots;
- 710 deduplicated ranking rows;
- 8 author snapshots;
- 53 archive captures;
- 2 comments and 1 confirmed tag;
- 2 rights candidates and 1 rights case.

Legacy databases remain preserved because their raw row counts include overlapping observations and schema-specific fields. Canonical uniqueness constraints intentionally deduplicate equivalent `(captured_at, work_id)` and ranking positions; this is not destructive because the source DBs and JSON remain byte-identical in `data/legacy/`.

## Sergey vertical slice

```text
work 563328
→ Сергей Насоновский + Сергей Щербатых
→ MoreKnig / CoolLib candidates
→ SHA-256 evidence metadata
→ human-reviewed status unclear
→ unified JSON report
→ example author/counsel documents
```

No legal notice was sent. No compensation was calculated. License status remains `unknown`.

## Reproduce

```bash
PYTHONPATH=src python scripts/migrate_legacy.py data/legacy/snapshots \
  --db data/unified.sqlite3 \
  --analytics-db data/legacy/author_today.sqlite3 \
  --evidence-db data/legacy/sergey-evidence.sqlite3

PYTHONPATH=src python -c 'from atintel.cli import main; main()' \
  rights-report SERGEY-563328-MOREKNIG-CASE-20260717 --db data/unified.sqlite3

PYTHONPATH=src python -m unittest discover -s tests -v
```

## Continue in the main analytics chat

1. Decide whether the current uncommitted diff should be reviewed and committed.
2. Obtain coauthor/rightsholder confirmation and a source text before upgrading any case from `unclear`.
3. Add scheduled public snapshots only where current platform terms permit.
4. Validate willingness to pay before expanding the rights workflow into a larger crawler or SaaS.
