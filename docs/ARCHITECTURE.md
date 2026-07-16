# Architecture

## Evidence layers

1. **Documented API** — default source for catalog and work metadata.
2. **Observed public web surface** — fallback for fields absent from the API; unstable and separately labelled.
3. **Authenticated first-party report** — only with informed author permission.
4. **Interpretation** — agent hypothesis, never stored as raw fact.

## Pipeline

```text
collector -> raw normalized JSON -> SQLite -> delta query -> evidence bundle -> agent conclusion
```

Raw captures are append-only. A normalized snapshot records source class, URL, and UTC capture time. Ranking position is meaningless without the complete query/cohort.

## Why SQLite

SQLite makes the prototype portable, inspectable, and easy for agents to query. A hosted multi-user product can later move to PostgreSQL without changing the conceptual model.

## Production boundary

A future web application should place a backend between browser UI and agent runtime. The browser must never receive Author.Today cookies, API secrets, shell access, or raw privileged tools.
