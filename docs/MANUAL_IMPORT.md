# Manual private-data import

Private Author.Today automation is not supported because the current public offer explicitly restricts script-based collection/interactions.

## Supported flow

1. The author uses normal Author.Today navigation.
2. The author obtains or prepares a local export they are permitted to use.
3. The author reviews the file.
4. The author runs the local importer:

```bash
atintel ingest /path/to/selected-export.json --db analytics.sqlite3
```

In Docker, send the reviewed file through stdin into the controller tmpfs, then import it. Do not mount a downloads directory containing unrelated files.

## Accepted boundary

The normalized JSON may contain:

- works and work snapshots;
- user-selected comments;
- source URLs and timestamps;
- observable profile URLs/display names;
- reviewable tags with evidence excerpts.

It must not contain:

- passwords or OTPs;
- cookies or Authorization headers;
- localStorage/sessionStorage;
- browser-profile files;
- manuscripts or paid book text;
- private messages;
- inferred sensitive traits.

Imports are limited to 10 MB. Missing provenance fields fail closed. Tags require `taxonomy_path`, `stance`, exact `evidence_excerpt`, confidence in `[0,1]`, derivation (`human`, `rule`, or `model`), and confirmation state.

See `examples/manual_private_import.synthetic.json` for a synthetic, non-customer example.
