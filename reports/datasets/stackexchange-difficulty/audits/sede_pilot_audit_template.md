# SEDE Pilot Audit Template

Pilot date: `YYYY-MM-DD`

## Source And Scope

- Source: Stack Overflow SEDE.
- Query file: `reports/datasets/stackexchange-difficulty/sede_pilot_query.sql`.
- Raw export: `data/raw/stackexchange-difficulty/sede-pilot-YYYY-MM-DD.tsv`.
- Provenance file:
  `reports/datasets/stackexchange-difficulty/provenance_sede_pilot_YYYY-MM-DD.json`.
- Raw export hash: `sha256:<raw export hash>`.
- No API crawling, HTML scraping, Data Dump download, or real corpus release was
  performed for this pilot.

## Preflight

- Expected columns matched `sede_expected_columns.tsv`: yes/no.
- Row count was inside the 5,000-10,000 target: yes/no.
- `DECLARE` syntax accepted by SEDE, or literal fallback recorded: yes/no.
- Raw export and processed tables are ignored by Git: yes/no.

## Validation Summary

- Question rows:
- Answer rows:
- Comment rows:
- Duplicate `question_id` failures:
- Artificial post ID failures:
- Accepted-answer consistency failures:
- Missing-column failures:
- Provenance failures:

## Distribution Summary

- Answered/unanswered balance:
- Accepted/no-accepted balance:
- Closure coverage:
- Duplicate coverage:
- Tag-family coverage:
- Time-period coverage:
- Visibility or score skew:

## Derived Outputs

- `derived_thread_indicators.tsv` produced: yes/no.
- `threads.jsonl` produced: yes/no.
- Derived output hash summary:

## Manual Inspection

At least 100 local records were inspected without copying real post content into
this audit.

- Bodies readable: yes/no.
- Code and error messages preserved locally: yes/no.
- Answers linked correctly: yes/no.
- Accepted answers linked correctly: yes/no.
- Duplicate links meaningful when present: yes/no.
- Record-level provenance complete: yes/no.
- Comments included in this pilot export: no, unless a separate comment export is
  documented here.

## Decision

- Ready for larger Data Dump planning: yes/no.
- Required fixes before scaling:
