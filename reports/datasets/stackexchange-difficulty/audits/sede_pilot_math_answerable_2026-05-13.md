# SEDE Pilot Audit

Pilot date: `2026-05-13`

## Source And Scope

- Source: Mathematics SEDE.
- Pilot slug: `math-answerable`.
- Query file: `reports/datasets/stackexchange-difficulty/sede_pilot_query_math_answerable.sql`.
- Query URL: `https://data.stackexchange.com/math/query/new`.
- Raw export: `data/raw/stackexchange-difficulty/sede-pilot-math-answerable-2026-05-13.csv`.
- Provenance file: `reports/datasets/stackexchange-difficulty/provenance_sede_pilot_math_answerable_2026-05-13.json`.
- Raw export hash: `sha256:327ba38f652fff83e4f108f508d54b131fe27900660953f12e7b8c02b66edd32`.
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
- Answer rows: 5751.
- Comment rows: 0.
- Duplicate `question_id` failures: 0.
- Artificial post ID failures: 0.
- Accepted-answer consistency failures: 0.
- Missing-column failures: 0.
- Provenance failures: 0.

## Distribution Summary

- Answered/unanswered balance: true=5000.
- Accepted/no-accepted balance: true=5000.
- Closure coverage: false=5000.
- Duplicate coverage: false=5000.
- Tag-family distribution: abstract-algebra=70, algebra-precalculus=62, algebraic-geometry=51, algebraic-topology=48, calculus=71, combinatorics=73, complex-analysis=56, differential-geometry=51, elementary-number-theory=59, functional-analysis=53, general-topology=64, geometry=70, graph-theory=46, group-theory=60, inequality=51, integration=59, linear-algebra=66, logic=56, number-theory=53, ordinary-differential-equations=45, polynomials=47, probability=79, probability-theory=54, real-analysis=69, sequences-and-series=62, other=3525.
- Tag-popularity buckets: high=4936, low=26, medium=38.
- Time-period distribution: recent=5000.
- Timing coverage: 5000/5000 with first-answer timing.

## Derived Outputs

- Pending provenance output hashes finalized before derivation: yes.
- `derived_thread_indicators.tsv` produced: yes.
- `threads.jsonl` produced: yes.
- Derived output hash summary: `data/processed/stackexchange-difficulty/pilot-math-answerable-2026-05-13-derived/derived-output.sha256`.

## Inspection

Inspection is not completed by the SEDE pipeline. Inspect or LLM-label at least 100 local records before using this pilot as a scaling decision. This tracked audit must not include real titles, post bodies, answer text, code snippets, comments, usernames, credentials, or other copied user content.

- Comments included in this pilot export: no; the current SEDE pilot path writes an empty comments table unless a separate comment export is documented.

## Inspection Summary

- Inspection source: local ignored label file under `data/processed/stackexchange-difficulty/`.
- Labeling method: llm_assisted.
- Decision profile: answerable_pilot.
- Inspected records: 100.
- Suitable records: yes=93, no=3, uncertain=4.
- Answerability clear: yes=95, no=1, uncertain=4.
- Math notation readable: yes=100, no=0, uncertain=0.
- Needs comments: yes=4, no=96, uncertain=0.
- Top reason codes: good=93, still_missing_context=4, unclear_answerability=2, unsuitable=1.
- Recommendation: ready_for_data_dump_design.

## Decision

- Decision: ready_for_data_dump_design.
