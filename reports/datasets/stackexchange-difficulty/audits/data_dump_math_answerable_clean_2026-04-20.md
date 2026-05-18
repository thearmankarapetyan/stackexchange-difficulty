# Data Dump Pilot Audit

## Source And Scope

- Source: Mathematics Stack Exchange Data Dump.
- Site slug: `math`.
- Pilot slug: `math-answerable-clean`.
- Dump date: `2026-04-20`.
- Sample profile: `answerable_clean`.
- Requested sample size: 5000.
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
- Selected questions: 5000.
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

- Question rows: 5000.
- Answer rows: 8693.
- Comment rows: 27916.
- Validation issue count: 0.

## Distribution Summary

- Answerability distribution: true=5000.
- Closure distribution: false=5000.
- Duplicate distribution: false=5000.
- Tag-family distribution: calculus=227, combinatorics=218, abstract-algebra=209, algebra-precalculus=193, algebraic-geometry=178, algebraic-topology=177, analysis=177, category-theory=163, algorithms=157, asymptotics=129, algebraic-number-theory=128, arithmetic=120, analytic-geometry=118, circles=100, approximation=99, binomial-coefficients=91, 3d=90, boolean-algebra=84, automata=81, banach-spaces=72, calculus-of-variations=72, analytic-number-theory=71, coding-theory=70, brownian-motion=67, average=65, other=1844.
- Time-period distribution: middle=2186, recent=1455, older=1359.
- Answer-latency distribution: under_1h=2277, under_24h=1723, under_7d=1000.
- Score buckets: low=2583, medium=1707, high=710.
- View buckets: low=2329, medium=1914, high=757.
- Comment-count buckets: low=1790, none=1686, high=1524.
- Derived indicator rows: 5000.

## Derived Outputs

- Processed output directory: `data/processed/stackexchange-difficulty/dump-math-answerable-clean-2026-04-20`.
- Derived output directory: `data/processed/stackexchange-difficulty/dump-math-answerable-clean-2026-04-20-derived`.
- Processed hash manifest: `data/processed/stackexchange-difficulty/dump-math-answerable-clean-2026-04-20/processed-output.sha256`.
- Derived hash manifest: `data/processed/stackexchange-difficulty/dump-math-answerable-clean-2026-04-20-derived/derived-output.sha256`.

## Content Safety

- This audit contains aggregate counts and hashes only. It does not include record-level Stack Exchange content, per-record identifiers, annotation files, credentials, or release artifacts.

## Inspection Summary

- Inspection source: local ignored label file under `data/processed/stackexchange-difficulty/`.
- Labeling method: llm_assisted_xhigh.
- Decision profile: target_scale_answerable.
- Inspected records: 100.
- Suitable records: yes=87, no=8, uncertain=5.
- Answerability clear: yes=88, no=6, uncertain=6.
- Math notation readable: yes=98, no=2, uncertain=0.
- Needs comments: yes=2, no=98, uncertain=0.
- Top reason codes: good=87, still_missing_context=8, unsuitable=3, notation_issue=1, unclear_answerability=1.
- Recommendation: target_scale_sample_accepted.

## Decision

- Decision: data_dump_parser_validated.
