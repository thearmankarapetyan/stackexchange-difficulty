# Data Dump Pilot Audit

## Source And Scope

- Source: Mathematics Stack Exchange Data Dump.
- Site slug: `math`.
- Pilot slug: `math-answerable-100k`.
- Dump date: `2026-04-20`.
- Sample profile: `answerable_pilot`.
- Requested sample size: 100000.
- No API crawling, HTML scraping, archive download, credential handling, or corpus release was performed.

## Preflight

- Dump directory: `data/raw/stackexchange-difficulty/data-dump/math-2026-04-20`.
- XML files: Comments.xml=present, PostHistory.xml=missing, PostLinks.xml=present, Posts.xml=present, Tags.xml=present.
- Raw file hashes: Comments.xml=sha256:2b141e1c7ad59b2607966aa00680b24d39adab3c673a0357729aa8b77cb9533c, PostLinks.xml=sha256:a44596801a90ee9ce96144ba11d1b2d9be6be98fc2759ad625349292ab153cfc, Posts.xml=sha256:73ffbb2edac21a92a8d05c877ebe597d30c92ef3f6030dfe76ac4e1067776899, Tags.xml=sha256:367628e5d83986b6f9f3a4dc16ee62b3639bfd0a963c5dec4fb88fd2130a204a.
- Preflight issues: 0.
- Preflight warnings: 1.

## Selection Summary

- Total question rows scanned: 1699538.
- Eligible question candidates: 835236.
- Selected questions: 100000.
- Artificial ID exclusions: 0.
- Closed question exclusions: 120221.
- Unanswered exclusions: 293859.
- No accepted-answer exclusions: 450205.
- Missing accepted-answer exclusions: 16.
- Accepted-answer parent mismatch exclusions: 1.
- Duplicate-link exclusions: 0.

## Validation Summary

- Question rows: 100000.
- Answer rows: 161112.
- Comment rows: 534698.
- Validation issue count: 0.

## Distribution Summary

- Answerability distribution: true=100000.
- Closure distribution: false=100000.
- Duplicate distribution: false=100000.
- Tag-family distribution: abstract-algebra=1344, calculus=1234, linear-algebra=1225, real-analysis=1211, probability=1196, geometry=1120, combinatorics=1085, algebra-precalculus=1078, general-topology=1032, integration=1023, algebraic-geometry=1002, number-theory=997, sequences-and-series=994, complex-analysis=992, algebraic-topology=961, analysis=942, elementary-number-theory=932, ordinary-differential-equations=928, group-theory=924, functional-analysis=901, differential-geometry=895, logic=887, matrices=887, probability-theory=882, graph-theory=867, other=74461.
- Time-period distribution: middle=45819, recent=29475, older=24706.
- Answer-latency distribution: under_1h=42413, under_24h=30043, under_7d=14997, over_7d=12547.
- Score buckets: low=50090, medium=32485, high=11156, negative=6269.
- View buckets: low=51005, medium=37961, high=11034.
- Comment-count buckets: low=36056, none=33334, high=30610.
- Derived indicator rows: 100000.

## Derived Outputs

- Processed output directory: `data/processed/stackexchange-difficulty/dump-math-answerable-100k-2026-04-20`.
- Derived output directory: `data/processed/stackexchange-difficulty/dump-math-answerable-100k-2026-04-20-derived`.
- Processed hash manifest: `data/processed/stackexchange-difficulty/dump-math-answerable-100k-2026-04-20/processed-output.sha256`.
- Derived hash manifest: `data/processed/stackexchange-difficulty/dump-math-answerable-100k-2026-04-20-derived/derived-output.sha256`.

## Content Safety

- This audit contains aggregate counts and hashes only. It does not include titles, bodies, formulas, code snippets, answers, comments, usernames, URLs, row IDs, labels, credentials, or copied Stack Exchange post content.

## Inspection Summary

- Inspection source: local ignored label file under `data/processed/stackexchange-difficulty/`.
- Labeling method: llm_assisted.
- Decision profile: target_scale_answerable.
- Inspected records: 100.
- Suitable records: yes=78, no=8, uncertain=14.
- Answerability clear: yes=79, no=5, uncertain=16.
- Math notation readable: yes=98, no=2, uncertain=0.
- Needs comments: yes=1, no=96, uncertain=3.
- Top reason codes: good=77, unclear_answerability=16, still_missing_context=3, unsuitable=3, notation_issue=1.
- Recommendation: target_scale_revise_sampling.

## Decision

- Decision: data_dump_parser_validated.
