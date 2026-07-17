# Data model

Implemented entities:

- `works` — stable book identity and descriptive metadata;
- `sources` — source class, exact URL, capture time and metadata;
- `work_snapshots` — cumulative metrics at a UTC time linked to a source;
- `ranking_snapshots` — ordered cohort membership with full query and source;
- `archive_captures` — Wayback/Common Crawl timestamps, digests and locators;
- `reader_profiles` — public profile URL/display name and first/last imported evidence dates;
- `comments` — selected comment, book/chapter, full body, profile and original URL;
- `comment_tags` — taxonomy path, stance, exact excerpt, confidence, derivation and confirmation.

Future entities:

- `events` — chapter, cover, price, post, ad, completion;
- `experiments` — hypothesis, controlled change, target metric, result;
- `campaigns` — UTM, spend, intent events, verified revenue if available.

## Evidence invariants

- Use `NULL` for unavailable metrics; never convert a collection/parsing failure into zero.
- A time-series point links to a source record.
- Archive records retain the original target, capture timestamp, digest and retrievable locator.
- A comment tag retains the exact excerpt that supports it.
- Model tags are not facts; `confirmed=1` means a human reviewed the classification.
- Public comments may identify people and remain local by default.
- Cumulative counters should not fall silently; source/schema changes or reversible actions such as unlike must be investigated before interpretation.
