# SEDE Pilot Audit

Pilot date: `2026-05-13`

## Source And Scope

- Source: Mathematics SEDE.
- Query file: `reports/datasets/stackexchange-difficulty/sede_pilot_query_site_generic.sql`.
- Query URL: `https://data.stackexchange.com/math/query/new`.
- Raw export: `data/raw/stackexchange-difficulty/sede-pilot-math-2026-05-13.csv`.
- Provenance file: `reports/datasets/stackexchange-difficulty/provenance_sede_pilot_math_2026-05-13.json`.
- Raw export hash: `sha256:6b2800cc53654c0ce3653e713dddead873653382757f62ff8992128d0bcb9788`.
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
- Answer rows: 3386.
- Comment rows: 0.
- Duplicate `question_id` failures: 0.
- Artificial post ID failures: 0.
- Accepted-answer consistency failures: 0.
- Missing-column failures: 0.
- Provenance failures: 0.

## Distribution Summary

- Answered/unanswered balance: false=1857, true=3143.
- Accepted/no-accepted balance: false=3295, true=1705.
- Closure coverage: false=3530, true=1470.
- Duplicate coverage: false=4423, true=577.
- Tag-family distribution: abstract-algebra=70, algebra-precalculus=63, algebraic-geometry=46, algebraic-topology=50, calculus=73, combinatorics=67, complex-analysis=61, discrete-mathematics=46, elementary-number-theory=72, elementary-set-theory=53, functional-analysis=56, general-topology=68, geometry=61, group-theory=59, inequality=56, integration=61, limits=44, linear-algebra=67, logic=59, number-theory=56, ordinary-differential-equations=44, probability=70, real-analysis=72, sequences-and-series=69, trigonometry=44, other=3513.
- Tag-popularity buckets: high=4942, low=25, medium=33.
- Time-period distribution: recent=5000.
- Timing coverage: 3143/5000 with first-answer timing.

## Derived Outputs

- Pending provenance output hashes finalized before derivation: yes.
- `derived_thread_indicators.tsv` produced: yes.
- `threads.jsonl` produced: yes.
- Derived output hash summary: `data/processed/stackexchange-difficulty/pilot-math-2026-05-13-derived/derived-output.sha256`.

## Manual Inspection

Manual inspection is not automated. Inspect at least 100 local records before using this pilot as a scaling decision. This tracked audit must not include real titles, post bodies, answer text, code snippets, comments, usernames, credentials, or other copied user content.

- Comments included in this pilot export: no; the current SEDE pilot path writes an empty comments table unless a separate comment export is documented.

## Decision

- Decision: pipeline complete; manual inspection still required before larger Data Dump planning.
