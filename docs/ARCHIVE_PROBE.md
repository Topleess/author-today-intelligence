# Archive coverage probe — 2026-07-16

## Wayback Machine

Read-only CDX queries returned:

- Author.Today root snapshots beginning in 2017.
- Archived `/work/...` pages, including works and review pages.
- Archived `/u/...` pages, including profile, works, library, followers and some comments-related pages.
- A broad `*/comments` wildcard query returned no rows in the tested shape; comment coverage must be checked by exact/profile-specific URLs.

Interpretation: Wayback can provide historical control points and metadata, but not a guaranteed regular time series.

## Common Crawl

Index: `CC-MAIN-2026-25`.

Exact prefix queries returned:

- 1,301 records under `https://author.today/work/`.
- 1,453 records under `https://author.today/u/`.

Returned records include timestamp, original URL, HTTP status, MIME type, WARC filename, byte offset and length. This is sufficient to retrieve exact archived response records reproducibly.

Interpretation: Common Crawl is viable for historical HTML backfill/provenance. Coverage is irregular and extracted metrics must be schema-versioned and labelled as archive observations, never merged silently with live API snapshots.

## Evidence quality labels

- `live_official_api`: strongest public structured observation.
- `owner_private_report`: first-party authenticated observation; local-only.
- `wayback_capture`: historical archived page; may be incomplete/dynamic.
- `commoncrawl_warc`: historical archived response with WARC coordinates.
- `derived`: deterministic calculation linked to source records.
- `hypothesis`: non-factual interpretation requiring validation.

## Next probe

1. Implement bounded index queries for a supplied author/work URL.
2. Retrieve one WARC record by exact range request.
3. Parse only explicit metadata visible in the archived response.
4. Save source URL, capture timestamp, digest/WARC coordinates and parser version.
5. Compare one archive observation against a live official API record without claiming continuity between them.
