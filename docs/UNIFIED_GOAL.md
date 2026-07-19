# Goal: unified Author.Today intelligence and rights monitoring

Status: active, approved 2026-07-17.

## Outcome

Use `/opt/data/projects/author-today-intelligence` as the canonical Git repository. Merge the useful local datasets and workflows from `/opt/data/author-today-analytics` into one evidence-first product that supports both author analytics and rights-monitoring.

## Vertical slice

```text
work + all official authors
→ candidate external publication
→ evidence capture
→ human classification
→ case card
→ author/counsel package
```

## Safety boundaries

- Technical similarity is not a legal determination.
- `likely_infringement` requires recorded human review.
- Retailers/libraries remain authorized or unclear until checked.
- No automatic legal notice, compensation calculation, or external sending.
- No bypass of access controls or rate limits.
- No commit or publication without user approval.

## Verification

- compare source and migrated record counts;
- test schema, ingest, API and CLI;
- verify the Sergey work preserves both official authors;
- execute one local end-to-end rights case;
- check links/artifacts and `git diff --check`;
- produce a handoff for the main analytics chat.
