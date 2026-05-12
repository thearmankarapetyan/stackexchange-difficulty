# Completion Criteria

The v1 scaffold is complete when:

- `python -m pytest` passes.
- `python -m ruff check .` passes.
- CLI help works through `python -m stackexchange_difficulty --help`.
- Fixture validation produces a passing validation report.
- Fixture derivation writes `derived_thread_indicators.tsv`, `threads.jsonl`,
  and `validation_report.json`.
- The opt-in API smoke check exists and stores metadata only.
- No real SEDE export, Data Dump download, HTML scrape, or corpus collection is
  performed by default.
- The implementation log records executed checks and their results.
- The private GitHub repository contains the initial scaffold commit.

Future corpus work is complete only after a real pilot also satisfies the manual
inspection and audit requirements in `validation_protocol.md`.

