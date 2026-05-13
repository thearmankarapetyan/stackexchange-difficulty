# SEDE Pilot Export Checklist

This checklist must be completed before a real SEDE pilot export is processed.

## Before Export

- For site-selected pilots, use `sede_pilot_query_site_generic.sql` as the
  query source. The SEDE site picker controls the forum; for Mathematics, use
  `https://data.stackexchange.com/math/query/new`.
- For the cleaner answerable Mathematics pilot, use
  `sede_pilot_query_math_answerable.sql` with `--site-slug math` and
  `--pilot-slug math-answerable`. The site slug identifies the Stack Exchange
  site; the pilot slug identifies this second, answerable-first pilot.
- Keep `sede_pilot_query.sql` as the historical/default Stack Overflow
  technical pilot query.
- Treat `sede_pilot_query_non_code.sql` and `sede_pilot_query_non_coding.sql`
  as optional Stack Overflow experiments, not the preferred route for changing
  forums.
- Confirm the selected SEDE site before running the query.
- Confirm the export target is 5,000-10,000 question rows.
- Confirm the expected columns match `sede_expected_columns.tsv`.
- Do not edit downloaded raw exports manually.
- Do not paste, store, script, or commit credentials. Login and Cloudflare
  verification are browser-only manual steps.
- The committed query limits candidate questions before ranking and answer-body
  joins. If SEDE still times out, reduce the `SELECT TOP 20000` seed size first,
  then rerun before changing output columns.
- Do not try to diagnose timeout by changing only the final output size; the
  expensive part is the work done before export rows are returned.

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

For browser-assisted automation, run:

```bash
stackexchange-difficulty run-sede-pilot \
  --pilot-date auto \
  --download-dir "$HOME/Downloads" \
  --open-browser \
  --timeout-seconds 1800
```

The command opens SEDE and watches for the exported CSV/TSV, but the user must
complete login, Cloudflare verification, query execution, and export manually.

For a Mathematics pilot, use explicit site metadata so filenames, provenance,
audits, and later Hugging Face metadata remain separate from Stack Overflow:

```bash
stackexchange-difficulty run-sede-pilot \
  --pilot-date auto \
  --site-slug math \
  --site-name Mathematics \
  --query-file reports/datasets/stackexchange-difficulty/sede_pilot_query_site_generic.sql \
  --download-dir "$HOME/Downloads" \
  --open-browser \
  --timeout-seconds 1800
```

For the second, cleaner Mathematics pilot, keep the SEDE source site as
`math` and add the pilot identity separately:

```bash
stackexchange-difficulty run-sede-pilot \
  --pilot-date auto \
  --site-slug math \
  --site-name Mathematics \
  --pilot-slug math-answerable \
  --query-file reports/datasets/stackexchange-difficulty/sede_pilot_query_math_answerable.sql \
  --download-dir auto \
  --open-browser \
  --timeout-seconds 1800
```

This produces artifact names such as
`sede-pilot-math-answerable-YYYY-MM-DD.csv`,
`pilot-math-answerable-YYYY-MM-DD/`, and
`sede_pilot_math_answerable_YYYY-MM-DD.md`, while provenance still records
`source_site_slug: math`.

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

For comment enrichment, first process the question/answer pilot, then generate
the ID-locked comment query from local pilot IDs:

```bash
stackexchange-difficulty run-sede-comment-enrichment \
  --pilot-date 2026-05-13 \
  --site-slug math \
  --site-name Mathematics \
  --questions data/processed/stackexchange-difficulty/pilot-math-2026-05-13/questions.tsv \
  --answers data/processed/stackexchange-difficulty/pilot-math-2026-05-13/answers.tsv \
  --download-dir auto \
  --open-browser \
  --timeout-seconds 1800
```

For a named pilot such as `math-answerable`, pass the same pilot slug to comment
enrichment. Do not replace `--site-slug math` with `--site-slug
math-answerable`; that would mislabel the source site.

The rendered comment query is written under ignored `data/processed/` because
it contains real post IDs. Do not commit that rendered query, the raw comment
export, comment-enriched TSV files, JSONL, or local reinspection files.

Tracked audit files belong under `audits/` and must contain aggregate results
only, with no question titles, post bodies, answer text, code snippets, comments,
or user profile content.
