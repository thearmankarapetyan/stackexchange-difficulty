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

## Inspection

The 100-record inspection was completed through LLM-assisted labeling over local ignored review files. This tracked audit contains aggregate labels only and does not include real titles, post bodies, answer text, code snippets, comments, usernames, credentials, or other copied user content.

- Comments included in this pilot export: no; the current SEDE pilot path writes an empty comments table unless a separate comment export is documented.

## Inspection Summary

- Inspection source: local ignored label file under `data/processed/stackexchange-difficulty/`.
- Labeling method: llm_assisted.
- Inspected records: 100.
- Suitable records: yes=61, no=22, uncertain=17.
- Answerability clear: yes=70, no=10, uncertain=20.
- Math notation readable: yes=100, no=0, uncertain=0.
- Needs comments: yes=21, no=79, uncertain=0.
- Top reason codes: good=55, closed_unsuitable=10, too_ambiguous=8, needs_comments=6, duplicate_useful=5, duplicate_not_useful=4, insufficient_answer_context=4, too_specialized=4, not_difficulty_related=3, bad_formatting=1.
- Recommendation: needs_comment_enrichment.

## Comment Enrichment

- Source: Mathematics SEDE comment export.
- Generated query file: `data/processed/stackexchange-difficulty/pilot-math-2026-05-13-comment-enrichment/sede_comments_query.sql`.
- Raw comment export: `data/raw/stackexchange-difficulty/sede-comments-math-2026-05-13.csv`.
- Comment provenance file: `reports/datasets/stackexchange-difficulty/provenance_sede_comments_math_2026-05-13.json`.
- Raw comment export hash: `sha256:1c834bec4ea534af66711d8e1fab4048389821b30f920d39c341fb05860f2dfb`.
- Comment rows: 20269.
- Covered questions: 4126.
- Covered included answer posts: 1741.
- Validation issues: none.
- Processed output: `data/processed/stackexchange-difficulty/pilot-math-2026-05-13-comment-enriched`.
- Derived output: `data/processed/stackexchange-difficulty/pilot-math-2026-05-13-comment-enriched-derived`.
- Content-safety status: aggregate audit only; no copied titles, bodies, answers, comments, code snippets, URLs, usernames, or credentials.

## Comment-Enriched LLM Reinspection

- Reinspection source: local ignored comment-enriched label file under `data/processed/stackexchange-difficulty/`.
- Labeling method: llm_assisted_comment_enriched.
- Reinspected records: 21.
- Suitable records: yes=6, no=12, uncertain=3.
- Answerability clear: yes=9, no=6, uncertain=6.
- Math notation readable: yes=21, no=0, uncertain=0.
- Still needs comments: yes=10, no=11, uncertain=0.
- Top reason codes: still_missing_context=7, resolved_with_comments=6, duplicate_or_closed=5, unclear_answerability=3.
- Content-safety status: aggregate counts only; row IDs, titles, bodies, answers, comments, URLs, usernames, notes, and code snippets are not copied into this audit.
- Recommendation: needs_more_comment_coverage.

## Comment-Enriched Decision

- Decision: needs_more_comment_coverage.

## Decision

- Decision: Comment-enriched reinspection complete; the Mathematics pilot needs
  more comment coverage or query revision before larger Data Dump planning.
