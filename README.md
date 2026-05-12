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

Run local checks:

```bash
python -m pytest
python -m ruff check .
```

Validate synthetic fixture data:

```bash
PYTHONPATH=src python -m stackexchange_difficulty validate \
  --questions tests/fixtures/questions.tsv \
  --answers tests/fixtures/answers.tsv \
  --comments tests/fixtures/comments.tsv \
  --provenance tests/fixtures/provenance.json \
  --out /tmp/stackexchange-validation.json
```

Derive indicators and JSONL from fixtures:

```bash
PYTHONPATH=src python -m stackexchange_difficulty derive \
  --questions tests/fixtures/questions.tsv \
  --answers tests/fixtures/answers.tsv \
  --comments tests/fixtures/comments.tsv \
  --provenance tests/fixtures/provenance.json \
  --out-dir /tmp/stackexchange-derived
```

Run the opt-in live API smoke check:

```bash
PYTHONPATH=src python -m stackexchange_difficulty api-smoke \
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
  completion criteria, and implementation log.
- `reports/`: copied report artifacts.

