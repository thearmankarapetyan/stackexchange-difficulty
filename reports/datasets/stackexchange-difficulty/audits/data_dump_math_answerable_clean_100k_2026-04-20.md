# Data Dump Pilot Audit

## Source And Scope

- Source: Mathematics Stack Exchange Data Dump.
- Site slug: `math`.
- Pilot slug: `math-answerable-clean-100k`.
- Dump date: `2026-04-20`.
- Sample profile: `answerable_clean`.
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
- Eligible question candidates: 792888.
- Selected questions: 100000.
- Artificial ID exclusions: 0.
- Closed question exclusions: 120221.
- Unanswered exclusions: 293859.
- No accepted-answer exclusions: 450205.
- Missing accepted-answer exclusions: 16.
- Accepted-answer parent mismatch exclusions: 1.
- Duplicate-link exclusions: 0.
- Clean negative-score exclusions: 14879.
- Clean missing-tag exclusions: 0.
- Clean missing first-answer timing exclusions: 0.
- Clean long-answer-latency exclusions: 27469.

## Validation Summary

- Question rows: 100000.
- Answer rows: 168253.
- Comment rows: 546586.
- Validation issue count: 0.

## Distribution Summary

- Answerability distribution: true=100000.
- Closure distribution: false=100000.
- Duplicate distribution: false=100000.
- Tag-family distribution: calculus=1220, real-analysis=1199, linear-algebra=1183, probability=1133, geometry=1118, combinatorics=1097, abstract-algebra=1092, integration=1057, general-topology=1052, number-theory=1024, complex-analysis=1018, differential-geometry=960, group-theory=952, elementary-number-theory=934, ordinary-differential-equations=931, functional-analysis=929, algebra-precalculus=924, logic=903, matrices=902, probability-theory=901, graph-theory=892, sequences-and-series=878, algebraic-geometry=873, algebraic-topology=857, analysis=836, other=75135.
- Time-period distribution: middle=45514, recent=28591, older=25895.
- Answer-latency distribution: under_1h=48176, under_24h=34631, under_7d=17193.
- Score buckets: low=54831, medium=33866, high=11303.
- View buckets: low=49451, medium=38495, high=12054.
- Comment-count buckets: low=35931, none=34239, high=29830.
- Derived indicator rows: 100000.

## Derived Outputs

- Processed output directory: `data/processed/stackexchange-difficulty/dump-math-answerable-clean-100k-2026-04-20`.
- Derived output directory: `data/processed/stackexchange-difficulty/dump-math-answerable-clean-100k-2026-04-20-derived`.
- Processed hash manifest: `data/processed/stackexchange-difficulty/dump-math-answerable-clean-100k-2026-04-20/processed-output.sha256`.
- Derived hash manifest: `data/processed/stackexchange-difficulty/dump-math-answerable-clean-100k-2026-04-20-derived/derived-output.sha256`.

## Content Safety

- This audit contains aggregate counts and hashes only. It does not include record-level Stack Exchange content, per-record identifiers, annotation files, credentials, or release artifacts.

## Inspection Summary

- Inspection source: local ignored label file under `data/processed/stackexchange-difficulty/`.
- Labeling method: llm_assisted_xhigh.
- Decision profile: target_scale_answerable.
- Inspected records: 100.
- Suitable records: yes=87, no=7, uncertain=6.
- Answerability clear: yes=89, no=5, uncertain=6.
- Math notation readable: yes=100, no=0, uncertain=0.
- Needs comments: yes=5, no=95, uncertain=0.
- Top reason codes: good=87, still_missing_context=7, unclear_answerability=4, unsuitable=2.
- Recommendation: target_scale_sample_accepted.

## Decision

- Decision: data_dump_parser_validated.
