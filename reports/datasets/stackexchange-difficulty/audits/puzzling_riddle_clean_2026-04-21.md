# Puzzling Riddle Data Dump Pilot Audit

## Source And Scope

- Source: Puzzling Stack Exchange Data Dump.
- Site slug: `puzzling`.
- Pilot slug: `puzzling-riddle-clean`.
- Dump date: `2026-04-21`.
- Sample profile: `puzzling_riddle_clean`.
- Requested sample size: 2000.
- Puzzling accepted answers are treated as accepted or intended solution candidates.
- No API crawling, HTML scraping, archive download, PostHistory parsing, credential handling, or corpus release was performed.

## Preflight

- Dump directory: `data/raw/stackexchange-difficulty/data-dump/puzzling-2026-04-21`.
- XML files: Comments.xml=present, PostHistory.xml=missing, PostLinks.xml=present, Posts.xml=present, Tags.xml=present.
- Raw file hashes: Comments.xml=sha256:dbb43ad4bf9b8b14858655473ae9fd74f0505dfe92f6f2fccf5403671c28ee5e, PostLinks.xml=sha256:4aa85fac5fca29000600f096db88800667be36f308541240cd25d7e0c1af3c30, Posts.xml=sha256:eeb58bdfb22704c2f0c5c6876eadc3069000477ec2cd90c370ccfbabb19b8314, Tags.xml=sha256:3a3e94628d8e7dbe931a0ad7e8f740184a4066de901c9f9c2e0fdffae45072ac.
- Preflight issues: 0.
- Preflight warnings: 1.

## Selection Summary

- Total question rows scanned: 30131.
- Eligible question candidates: 8266.
- Selected questions: 2000.
- Target-tag candidates: riddle=666, word=609, enigmatic-puzzle=569, wordplay=510, lateral-thinking=343.
- Excluded-tag exclusions: mathematics=4056, visual=2055, cipher=1506, chess=630, computer-puzzle=387.
- Artificial ID exclusions: 0.
- Closed question exclusions: 2686.
- Unanswered exclusions: 417.
- No accepted-answer exclusions: 3591.
- Missing accepted-answer exclusions: 3.
- Accepted-answer parent mismatch exclusions: 0.
- Duplicate-link exclusions: 0.
- Missing target-tag exclusions: 7151.
- First-pass excluded-tag exclusions: 8017.

## Validation Summary

- Question rows: 2000.
- Answer rows: 4997.
- Comment rows: 19592.
- Validation issue count: 0.

## Distribution Summary

- Tag-family distribution: riddle=666, word=391, enigmatic-puzzle=365, lateral-thinking=316, wordplay=262.
- Time-period distribution: middle=1134, recent_pre_window=721, recent_window=145.
- Answer-latency distribution: under_1h=815, under_24h=696, under_7d=332, over_7d=157.
- Score buckets: high=773, medium=749, low=323, negative=155.
- View buckets: medium=1028, low=831, high=141.
- Comment-count buckets: low=833, none=663, high=504.
- Answer-count buckets: single_answer=939, several_answers=759, many_answers=302.
- Derived indicator rows: 2000.

## Derived Outputs

- Processed output directory: `data/processed/stackexchange-difficulty/puzzling-riddle-clean-2026-04-21`.
- Derived output directory: `data/processed/stackexchange-difficulty/puzzling-riddle-clean-2026-04-21-derived`.
- Processed hash manifest: `data/processed/stackexchange-difficulty/puzzling-riddle-clean-2026-04-21/processed-output.sha256`.
- Derived hash manifest: `data/processed/stackexchange-difficulty/puzzling-riddle-clean-2026-04-21-derived/derived-output.sha256`.

## Content Safety

- This audit contains aggregate counts and hashes only. It excludes Puzzling post titles, puzzle bodies, solution text, comments, URLs, handles, row-level review files, coding files, credentials, and release artifacts.

## Decision

- Decision: puzzling_parser_validated.
