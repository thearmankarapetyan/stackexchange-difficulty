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

Use `provenance_sede_pilot_template.json` as the starting point for real pilot
metadata. The first real SEDE pilot uses JSON provenance; YAML remains available
for repository templates and synthetic fixtures.

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
