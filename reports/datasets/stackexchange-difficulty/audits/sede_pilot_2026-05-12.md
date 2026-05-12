# SEDE Pilot Audit

Pilot date: `2026-05-12`

## Source And Scope

- Source: Stack Overflow SEDE.
- Query file: `reports/datasets/stackexchange-difficulty/sede_pilot_query.sql`.
- Raw export: `data/raw/stackexchange-difficulty/sede-pilot-2026-05-12.csv`.
- Provenance file: `reports/datasets/stackexchange-difficulty/provenance_sede_pilot_2026-05-12.json`.
- Raw export hash: `sha256:fa827890fc13a069f83d58f6fbc8431df7a855930ee6e5162edc655c6eebe205`.
- No API crawling, HTML scraping, Data Dump download, credential handling, or real corpus release was performed for this pilot.

## Preflight

- Raw export suffix: `.csv`.
- Row count: 5000.
- Expected columns matched: yes.
- Row count inside target: yes.
- Raw export ignored by Git: yes.
- Processed question table ignored by Git: yes.
- Derived JSONL ignored by Git: yes.

## Validation Summary

- Question rows: 5000.
- Answer rows: 3551.
- Comment rows: 0.
- Duplicate `question_id` failures: 0.
- Artificial post ID failures: 0.
- Accepted-answer consistency failures: 0.
- Missing-column failures: 0.
- Provenance failures: 0.

## Distribution Summary

- Answered/unanswered balance: false=1669, true=3331.
- Accepted/no-accepted balance: false=3356, true=1644.
- Closure coverage: false=3243, true=1757.
- Duplicate coverage: false=4254, true=746.
- Tag-popularity buckets: high=4863, low=76, medium=61.
- Timing coverage: 3331/5000 with first-answer timing.

## Derived Outputs

- Pending provenance output hashes finalized before derivation: yes.
- `derived_thread_indicators.tsv` produced: yes.
- `threads.jsonl` produced: yes.
- Derived output hash summary: `data/processed/stackexchange-difficulty/pilot-2026-05-12-derived/derived-output.sha256`.

## Manual Inspection

Manual inspection is not automated. Inspect at least 100 local records before using this pilot as a scaling decision. This tracked audit must not include real titles, post bodies, answer text, code snippets, comments, usernames, credentials, or other copied user content.

- Comments included in this pilot export: no; the current SEDE pilot path writes an empty comments table unless a separate comment export is documented.

## Decision

- Decision: pipeline complete; manual inspection still required before larger Data Dump planning.
