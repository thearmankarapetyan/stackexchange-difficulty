# SEDE Pilot Export Checklist

This checklist must be completed before a real SEDE pilot export is processed.

## Before Export

- Use `sede_pilot_query.sql` as the query source.
- Confirm the target database is Stack Overflow.
- Confirm the export target is 5,000-10,000 question rows.
- Confirm the expected columns match `sede_expected_columns.tsv`.
- Do not edit downloaded raw exports manually.
- If SEDE rejects `DECLARE @RowsPerStratum`, replace the variable with a
  literal value in the query template and record that change before export.

## Record With Raw Export

- SEDE query text and query URL if saved publicly.
- Target site database.
- Query execution date.
- SEDE data refresh date if visible.
- Export filename.
- Raw export SHA-256 hash.
- Export row count.
- Filter or parameter changes from the committed query template.

Use the real export suffix from SEDE. For CSV:

```bash
export PILOT_DATE=$(date +%F)
export PILOT_EXT=csv
export PILOT_RAW="data/raw/stackexchange-difficulty/sede-pilot-${PILOT_DATE}.${PILOT_EXT}"

stackexchange-difficulty preflight-sede --export "$PILOT_RAW"
```

## Processing Rule

The exported file must stay outside Git under `data/raw/stackexchange-difficulty/`.
Processed outputs must be regenerated through the CLI and documented in
provenance metadata.

For the first real pilot, copy
`provenance_sede_pilot_template.json` to a dated JSON file and pass that file to
`stackexchange-difficulty ingest-sede`. Run `stackexchange-difficulty derive`
after ingestion; ingestion alone does not create derived indicators or JSONL.
Before deriving, finalize `processed_output_hash` and `output_hash` in both the
tracked pilot provenance JSON and the processed `provenance.json`:

```bash
sha256sum \
  "$PILOT_OUT/questions.tsv" \
  "$PILOT_OUT/answers.tsv" \
  "$PILOT_OUT/comments.tsv" \
  "$PILOT_OUT/validation_report.json" \
  > "$PILOT_OUT/processed-output.sha256"

stackexchange-difficulty finalize-provenance \
  --provenance "$PILOT_PROV" \
  --hash-file "$PILOT_OUT/processed-output.sha256" \
  --out "$PILOT_PROV"

stackexchange-difficulty finalize-provenance \
  --provenance "$PILOT_OUT/provenance.json" \
  --hash-file "$PILOT_OUT/processed-output.sha256" \
  --out "$PILOT_OUT/provenance.json"
```

The current pilot export path does not include comment text. Any audit produced
from it must state that comment usefulness is deferred unless a separate comment
export is added.

Tracked audit files belong under `audits/` and must contain aggregate results
only, with no question titles, post bodies, answer text, code snippets, comments,
or user profile content.
