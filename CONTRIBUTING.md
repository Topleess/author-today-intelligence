# Contributing

1. Open an issue describing the data source and user outcome.
2. Prefer documented API methods over HTML parsing.
3. Add fixture-based tests; live network calls must not be required by the test suite.
4. Label every field as documented API, observed web surface, authenticated first-party report, or interpretation.
5. Never add client datasets, raw comment dumps, or secrets.
6. Run `python3 -m unittest discover -s tests -v` before submitting a change.
