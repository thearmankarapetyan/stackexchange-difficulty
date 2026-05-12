# Completion Criteria

The v1 scaffold is complete when:

- `python -m pytest` passes.
- `python -m ruff check .` passes.
- CLI help works through `python -m stackexchange_difficulty --help`.
- Editable installation exposes `stackexchange-difficulty --help`.
- Fixture validation produces a passing validation report.
- Fixture derivation writes `derived_thread_indicators.tsv`, `threads.jsonl`,
  and `validation_report.json`.
- Synthetic SEDE ingestion writes normalized question, answer, comment,
  provenance, and validation outputs.
- The opt-in API smoke check exists and stores metadata only.
- No real SEDE export, Data Dump download, HTML scrape, or corpus collection is
  performed by default.
- The implementation log records executed checks and their results.
- The private GitHub repository contains the initial scaffold commit.
- GitHub Actions passes on `main`.

Future corpus work is complete only after a real pilot also satisfies the manual
inspection and audit requirements in `validation_protocol.md`.

## First Real SEDE Pilot Gate

The first real SEDE pilot is ready for review only when:

- A raw export has been saved under `data/raw/stackexchange-difficulty/` and is
  ignored by Git.
- `stackexchange-difficulty preflight-sede` has confirmed required columns,
  the 5,000-10,000 row target, and the raw export hash.
- A dated JSON provenance file has been created from
  `provenance_sede_pilot_template.json`.
- `stackexchange-difficulty ingest-sede` has produced normalized local tables.
- `stackexchange-difficulty finalize-provenance` has replaced pending output
  hashes before derived JSONL is generated.
- `stackexchange-difficulty derive` has produced indicators and JSONL.
- The tracked audit under `audits/` contains aggregate validation results,
  processed-file hashes, and the manual-inspection summary.
- No real Stack Exchange post content has been committed.
