# Execution checkpoint

Updated: 2026-07-16

## Completed in the active goal

- Approved goal and security boundaries saved.
- Official rules, privacy policy, offer, robots and API docs checked.
- Explicit script-collection restriction found in the offer; automated authenticated browser connector rejected pending written permission.
- Safe private-data fallback implemented as a user-selected local manual import.
- Wayback/Common Crawl exact-URL probe implemented and tested live.
- One Common Crawl WARC range retrieved, decompressed and SHA-256 verified.
- Docker Compose local application implemented with non-root controller, read-only rootfs and loopback-only port.
- Public API sync, SQLite, restart persistence, archive evidence, comment tags and evidence UI verified.
- Tag drilldown preserves excerpt, full comment, profile and original URL.
- Read-only local API contract and privacy scanner added.

## Current verification evidence

- Unit tests: 8 passing before final quality gate.
- Docker public sync: 2 runs, 50 work snapshots.
- Example deterministic delta: `4,568,305 - 4,568,019 = 286`.
- Archive target `/work/100705`: 2 Wayback captures + 1 Common Crawl record.
- WARC raw bytes: 70,018; SHA-256: `51e50b71c1b2b74458214a58e3ac958b88e21e84dffa29a30bf3398ea26d314e`.
- Container restart preserved summary state.
- Browser console: zero JavaScript errors.

## Final publication

- External security/archive reviews integrated.
- Clean clone from the public GitHub URL installed version `0.2.0`; 8 tests and privacy scan passed.
- Docker clean-clone smoke passed: health OK and POST denied with HTTP 405.
- Public repository HEAD: `12a0564a226f72ac3232df558f64f231367a28de` before this checkpoint-only commit.
- Release `v0.2.0` published with verified PDF asset.
- GitHub Actions runs for the release completed successfully.

## Standing follow-up

The separate 14-day public monitoring remains active, with final report due 2026-07-30. Automated authenticated browser collection remains blocked pending written Author.Today permission; the supported private-data path is manual local import.
