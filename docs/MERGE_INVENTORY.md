# Merge inventory and decision

Date: 2026-07-17

## Canonical repository

`/opt/data/projects/author-today-intelligence`

Reasons:

- it is the Git repository on `main`;
- it has the packaged `atintel` application, tests, Docker configuration, read-only API/UI and provenance model;
- the rights research, pilot and artifacts already live here;
- it provides the safer base for migrations than the unversioned prototype directory.

## Legacy working directory

`/opt/data/author-today-analytics`

Useful assets to preserve:

- `author_today.sqlite3`: works, work/ranking/author/campaign snapshots;
- `sergey-evidence.sqlite3`: evidence-first works, snapshots, comments and archives;
- timestamped JSON snapshots under `snapshots/`;
- `collect_live.py`: public HTML/profile collector that exposed missing coauthors;
- client brief, audit and UI concepts.

The legacy directory is not a Git repository. It remains untouched as a rollback source.

## Schema gaps

The canonical schema already has provenance, comments, archives and a minimal `rights_cases` table. It lacks:

- normalized authors and many-to-many work authors;
- author snapshots/campaign data from the legacy analytics prototype;
- normalized rights candidates and evidence records;
- a rights-case relationship to `work_id` and candidate;
- API/CLI endpoints for the rights workflow.

## Merge strategy

1. Extend the canonical schema additively; do not mutate the legacy databases.
2. Add a legacy snapshot normalizer/importer rather than copying SQLite files blindly.
3. Preserve original JSON snapshots under a clearly labelled imported-data directory or ingest them into canonical SQLite with source provenance.
4. Resolve authors from official work-page metadata; profile ownership must not be treated as exhaustive authorship.
5. Add a local vertical-slice fixture for Sergey and the two candidates.
6. Integrate rights API/UI and docs.
7. Verify counts and produce a migration manifest.

## Rollback

All changes are currently uncommitted in the canonical repository. Legacy files are read-only sources and are not deleted or overwritten.
