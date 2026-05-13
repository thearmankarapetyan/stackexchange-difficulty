# Stack Exchange Difficulty Corpus Scaffold

This repository implements the first local scaffold for the Stack Exchange
difficulty corpus workflow. It follows the methodological report in
`reports/stackexchange_exploitation_report.md`.

The repository does not contain a real Stack Exchange corpus. It provides schema
definitions, validation logic, derived indicators, JSONL export, provenance
helpers, fixture-based tests, and an opt-in Stack Exchange API smoke check that
stores metadata only.

## Scope

This version supports the construction protocol, not corpus collection. It does
not run a SEDE export, download the public Data Dump, scrape HTML, or collect
question, answer, comment, or user content from Stack Exchange.

## Commands

Install the package for local development:

```bash
source ~/venvs/stage/bin/activate
python -m pip install -e .
```

Run local checks:

```bash
python -m pytest
python -m ruff check .
```

Verify the installed console script:

```bash
stackexchange-difficulty --help
```

Credential safety: never paste, store, script, or commit Stack Exchange,
university, or browser credentials in this project. If SEDE requires login or
Cloudflare verification, complete that step manually in the browser. The tooling
only prepares the query, watches for the exported file, and processes local
files after the manual export.

Validate synthetic fixture data:

```bash
stackexchange-difficulty validate \
  --questions tests/fixtures/questions.tsv \
  --answers tests/fixtures/answers.tsv \
  --comments tests/fixtures/comments.tsv \
  --provenance tests/fixtures/provenance.json \
  --out /tmp/stackexchange-validation.json
```

Derive indicators and JSONL from fixtures:

```bash
stackexchange-difficulty derive \
  --questions tests/fixtures/questions.tsv \
  --answers tests/fixtures/answers.tsv \
  --comments tests/fixtures/comments.tsv \
  --provenance tests/fixtures/provenance.json \
  --out-dir /tmp/stackexchange-derived
```

Preflight a local SEDE pilot export before ingestion. Keep the real suffix from
SEDE, usually `.csv`, unless the export is actually tab-delimited:

```bash
export PILOT_DATE=$(date +%F)
export PILOT_EXT=csv
export PILOT_RAW="data/raw/stackexchange-difficulty/sede-pilot-${PILOT_DATE}.${PILOT_EXT}"

stackexchange-difficulty preflight-sede \
  --export "$PILOT_RAW"
```

Ingest the local export after preflight and JSON provenance are ready:

```bash
export PILOT_PROV="reports/datasets/stackexchange-difficulty/provenance_sede_pilot_${PILOT_DATE}.json"
export PILOT_OUT="data/processed/stackexchange-difficulty/pilot-${PILOT_DATE}"

stackexchange-difficulty ingest-sede \
  --export "$PILOT_RAW" \
  --provenance "$PILOT_PROV" \
  --out-dir "$PILOT_OUT"
```

Hash processed outputs and finalize provenance before deriving JSONL:

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

Then derive indicators and JSONL from the normalized local outputs:

```bash
export PILOT_DERIVED="data/processed/stackexchange-difficulty/pilot-${PILOT_DATE}-derived"

stackexchange-difficulty derive \
  --questions "$PILOT_OUT/questions.tsv" \
  --answers "$PILOT_OUT/answers.tsv" \
  --comments "$PILOT_OUT/comments.tsv" \
  --provenance "$PILOT_OUT/provenance.json" \
  --out-dir "$PILOT_DERIVED"
```

After the answerable Mathematics SEDE pilot has a `ready_for_data_dump_design`
audit, validate a manually extracted Stack Exchange Data Dump layout. The tool
does not download or extract `.7z` archives; put extracted XML files under
ignored `data/raw/` first:

```bash
stackexchange-difficulty preflight-dump \
  --dump-dir data/raw/stackexchange-difficulty/data-dump/math-YYYY-MM-DD \
  --site-slug math \
  --site-name Mathematics \
  --dump-date YYYY-MM-DD \
  --sample-profile answerable_pilot
```

For the v1 `answerable_pilot` profile, `Posts.xml` and `PostLinks.xml` are
required because duplicate exclusion depends on post links. `Comments.xml` and
`Tags.xml` are optional. `PostHistory.xml` is read only when explicitly requested
with `--include-post-history`, because it can be large and contains raw markdown
or event text.

Run the local Data Dump pilot parser after preflight:

```bash
stackexchange-difficulty run-data-dump-pilot \
  --dump-dir data/raw/stackexchange-difficulty/data-dump/math-YYYY-MM-DD \
  --site-slug math \
  --site-name Mathematics \
  --pilot-slug math-answerable \
  --dump-date YYYY-MM-DD \
  --sample-profile answerable_pilot \
  --sample-size 5000
```

The Data Dump workflow normalizes selected rows into ignored processed TSV
tables, finalizes provenance hashes before derivation, writes derived indicators
and `threads.jsonl`, and creates aggregate tracked provenance/audit files. The
tracked audit contains counts and hashes only; raw XML, processed post text,
comments, JSONL threads, and post history stay ignored under `data/`.

Run the browser-assisted SEDE pilot pipeline after manual browser export:

```bash
stackexchange-difficulty run-sede-pilot \
  --pilot-date auto \
  --download-dir "$HOME/Downloads" \
  --open-browser \
  --timeout-seconds 1800
```

This opens the Stack Overflow SEDE query page and prints the local query-file
location. The tool does not try to copy SQL to the clipboard. The user manually
opens the query file, pastes the SQL into SEDE, completes login or Cloudflare
verification if needed, runs the query, and exports the CSV/TSV file.
After the export appears, the command copies it unchanged into
`data/raw/stackexchange-difficulty/`, hashes it, preflights the row and schema
gate, creates dated JSON provenance, ingests normalized local tables, finalizes
processed hashes before derivation, writes JSONL, and creates an aggregate audit
without post text.

If the export already exists locally, skip browser watching:

```bash
stackexchange-difficulty run-sede-pilot \
  --export "data/raw/stackexchange-difficulty/sede-pilot-${PILOT_DATE}.csv" \
  --pilot-date "$PILOT_DATE"
```

Use `provenance_sede_pilot_template.json` as the starting point for real pilot
metadata. The first real SEDE pilot uses JSON provenance; YAML remains available
for repository templates and synthetic fixtures.

Prepare a metadata-only Hugging Face dataset release folder after a dated pilot
provenance file and aggregate audit exist:

```bash
stackexchange-difficulty prepare-hf-release \
  --pilot-date "$PILOT_DATE" \
  --repo-id "NAMESPACE/stackexchange-difficulty" \
  --out-dir "dist/huggingface/stackexchange-difficulty-${PILOT_DATE}"
```

The release folder contains only safe metadata: the dataset card, release
manifest, data dictionary, dated provenance, aggregate audit, protocol docs, and
the methodology report. It does not stage raw SEDE exports, processed Stack
Exchange post text, JSONL thread records, browser downloads, or credentials.
`dist/` remains ignored by Git.

Preview Hugging Face upload commands without network access:

```bash
stackexchange-difficulty upload-hf-release \
  --release-dir "dist/huggingface/stackexchange-difficulty-${PILOT_DATE}" \
  --repo-id "NAMESPACE/stackexchange-difficulty"
```

Apply the upload only after local review and authentication through `hf auth
login` or `HF_TOKEN`; the command verifies access with `hf auth whoami`:

```bash
stackexchange-difficulty upload-hf-release \
  --release-dir "dist/huggingface/stackexchange-difficulty-${PILOT_DATE}" \
  --repo-id "NAMESPACE/stackexchange-difficulty" \
  --apply
```

For source-tree development without installation, the module form remains
available with `PYTHONPATH=src python -m stackexchange_difficulty ...`.

Run the opt-in live API smoke check:

```bash
stackexchange-difficulty api-smoke \
  --live \
  --site stackoverflow \
  --out /tmp/stackexchange-api-smoke.json
```

The live smoke check calls Stack Exchange API v2.3 `/info?site=...` and writes
only endpoint metadata, status, quota fields, and any `backoff` value returned.

## Repository Layout

- `src/stackexchange_difficulty/`: package code and CLI.
- `tests/`: unit tests and synthetic fixtures.
- `data/raw/stackexchange-difficulty/`: placeholder for unedited source data.
- `data/processed/stackexchange-difficulty/`: placeholder for generated outputs.
- `reports/datasets/stackexchange-difficulty/`: provenance, validation protocol,
  completion criteria, SEDE pilot artifacts, and implementation log.
- `reports/`: copied report artifacts.
