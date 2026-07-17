# Current rules and automation boundary audit

Date: 2026-07-16

## Sources checked

- `https://author.today/robots.txt` — HTTP 200.
- `https://author.today/pages/rules` — HTTP 200, title `Правила / Author.Today`.
- `https://api.author.today/help` — HTTP 200.
- `https://api.author.today/home/maininfo` — HTTP 200.
- `/terms` and `/legal` returned HTTP 404 and are not treated as policy sources.

## Findings

1. The public community rules page did not contain an explicit automation, scraper, bot, or parser prohibition in the extracted text checked on this date.
2. The public offer at `https://author.today/pages/offer` does contain an explicit restriction: in the buyer obligations section it prohibits using programs/scripts to collect information and/or interact with the site and its services, except navigation tools available on the site.
3. This explicit restriction triggers the project's stop condition for an automated authenticated browser connector. Local execution and first-party credentials do not remove the restriction.
4. `robots.txt` additionally disallows `/account/`, `/home`, login-return routes, search, library-state routes, and many parameterized URLs. Public work/profile routes are not categorically disallowed.
5. Robots directives are operational crawler evidence, not contractual authorization.
6. The rules prohibit publishing another person's personal information without permission, and the privacy policy treats directly or indirectly identifiable information as personal data.
7. Official API documentation and guest access exist and remain the preferred automated public-data path.

## Product decision

**Automated authenticated browser collection is rejected pending written platform permission.** The public tracer-bullet will not ship a controller-accessible browser profile, cookie store, DOM scraper, or internal-endpoint observer.

## Safe product boundary

- Public catalog/work collection uses the documented API wherever possible.
- Archive backfill uses Wayback/Common Crawl indexes and preserves archive provenance.
- Private author analytics enter through a local manual import selected by the user from an export/copy they obtained through normal site navigation.
- The importer accepts data files, not credentials, cookies, localStorage, OTPs, or browser profiles.
- No automatic publishing, messaging, account modification, private-page navigation, or concealed retries.
- Reader-level observations remain local, evidence-linked, and are not published as personal dossiers.
- A future browser-worker integration point may be documented but remains disabled until written Author.Today permission defines routes, rate limits, retention, and allowed storage.

## Remaining uncertainty

The offer language is broad and this is not legal advice. Before any authenticated automation, obtain written platform permission or an official partner/API scope. Until then, the manual/offline import boundary is the only supported private-data path.
