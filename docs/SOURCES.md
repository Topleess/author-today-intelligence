# Sources and connector status

Verified in July 2026:

- Official docs: https://api.author.today/help
- Authentication overview: https://api.author.today/home/maininfo
- API base: https://api.author.today/v1/
- `GET v1/catalog/search`
- `GET v1/work/{id}/details`
- `GET v1/work/{id}/meta-info`
- `GET v1/work/{id}/content`

Observed web surfaces such as comments and library-state totals are not documented contracts and are intentionally excluded from the core implementation. Verify terms, response status, MIME type, and schema before adding an optional connector.
