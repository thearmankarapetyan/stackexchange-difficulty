# SEDE Pilot Export Checklist

This checklist must be completed before a real SEDE pilot export is processed.

## Before Export

- Use `sede_pilot_query.sql` as the query source.
- Confirm the target database is Stack Overflow.
- Confirm the export target is 5,000-10,000 question rows.
- Confirm the expected columns match `sede_expected_columns.tsv`.
- Do not edit downloaded raw exports manually.

## Record With Raw Export

- SEDE query text and query URL if saved publicly.
- Target site database.
- Query execution date.
- SEDE data refresh date if visible.
- Export filename.
- Raw export SHA-256 hash.
- Export row count.
- Filter or parameter changes from the committed query template.

## Processing Rule

The exported file must stay outside Git under `data/raw/stackexchange-difficulty/`.
Processed outputs must be regenerated through the CLI and documented in
provenance metadata.
