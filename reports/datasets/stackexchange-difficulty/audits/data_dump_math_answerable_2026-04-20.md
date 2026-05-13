# Data Dump Pilot Audit

## Source And Scope

- Source: Mathematics Stack Exchange Data Dump.
- Site slug: `math`.
- Pilot slug: `math-answerable`.
- Dump date: `2026-04-20`.
- Sample profile: `answerable_pilot`.
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
- Eligible question candidates: 835236.
- Selected questions: 5000.
- Artificial ID exclusions: 0.
- Closed question exclusions: 120221.
- Unanswered exclusions: 293859.
- No accepted-answer exclusions: 450205.
- Missing accepted-answer exclusions: 16.
- Accepted-answer parent mismatch exclusions: 1.
- Duplicate-link exclusions: 0.

## Validation Summary

- Question rows: 5000.
- Answer rows: 8314.
- Comment rows: 27014.
- Validation issue count: 0.

## Distribution Summary

- Answerability distribution: true=5000.
- Closure distribution: false=5000.
- Duplicate distribution: false=5000.
- Tag-family distribution: calculus=341, abstract-algebra=315, algebra-precalculus=282, algebraic-geometry=252, analysis=247, algebraic-topology=245, algorithms=212, algebraic-number-theory=167, arithmetic=166, asymptotics=165, analytic-geometry=154, approximation=120, boolean-algebra=108, automata=106, binomial-coefficients=106, 3d=104, analytic-number-theory=94, calculus-of-variations=89, banach-spaces=83, brownian-motion=81, average=74, binary=65, area=57, binomial-theorem=56, c-star-algebras=54, other=1257.
- Time-period distribution: middle=2190, recent=1451, older=1359.
- Answer-latency distribution: under_1h=1984, under_24h=1432, under_7d=828, over_7d=756.
- Score buckets: low=2286, medium=1619, high=689, negative=406.
- View buckets: low=2396, medium=1897, high=707.
- Comment-count buckets: low=1802, none=1611, high=1587.
- Derived indicator rows: 5000.

## Derived Outputs

- Processed output directory: `data/processed/stackexchange-difficulty/dump-math-answerable-2026-04-20`.
- Derived output directory: `data/processed/stackexchange-difficulty/dump-math-answerable-2026-04-20-derived`.
- Processed hash manifest: `data/processed/stackexchange-difficulty/dump-math-answerable-2026-04-20/processed-output.sha256`.
- Derived hash manifest: `data/processed/stackexchange-difficulty/dump-math-answerable-2026-04-20-derived/derived-output.sha256`.

## Content Safety

- This audit contains aggregate counts and hashes only. It does not include titles, bodies, formulas, code snippets, answers, comments, usernames, URLs, row IDs, labels, credentials, or copied Stack Exchange post content.

## Decision

- Decision: data_dump_parser_validated.
