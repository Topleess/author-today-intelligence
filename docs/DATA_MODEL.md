# Data model

Core entities:

- `works` — stable book identity and current descriptive metadata;
- `work_snapshots` — cumulative metrics at a UTC time;
- `ranking_snapshots` — ordered cohort membership with full query;
- future `events` — chapter, cover, price, post, ad, completion;
- future `comments` / `comment_themes` — evidence and derived classifications;
- future `experiments` — hypothesis, controlled change, target metric, result;
- future `campaigns` — UTM, spend, intent events, verified revenue if available.

Use `NULL` for unavailable metrics. Never convert a parsing failure into zero. Cumulative counters should not fall silently; flag a source/schema anomaly.
