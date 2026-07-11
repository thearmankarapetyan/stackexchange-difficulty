# Contributing

This repository supports a documented research workflow. Changes should remain
small, understandable, reproducible, and compatible with Stack Exchange dumps
that follow the expected XML structure.

## Before making a change

1. Read `README.md`, `PROJECT_CHECKLIST.md`, and the relevant page linked from
   `docs/README.md`.
2. Create a short-lived branch from `main`, using a descriptive prefix such as
   `feature/`, `fix/`, or `docs/`.
3. Create and activate a virtual environment, then install the development
   requirements:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements-dev.txt
   ```

## Project rules

- Keep paths, communities, dates, question IDs, field selections, and output
  locations configurable.
- Keep authored material in English and preserve source content in its original
  form.
- Keep one generic, self-contained EDA notebook.
- Update schemas, the data dictionary, examples, and documentation together
  when a field contract changes.
- Keep raw dumps, credentials, local environments, caches, and regenerated
  annual outputs outside Git.
- Never commit a secret. Revoke it immediately if it enters Git history.

## Validate the change

Run the checks that cover the changed behavior. The minimum source checks are:

```bash
python -m compileall -q src
python -m ruff check src
python src/extract_threads.py --help
python src/extract_request_summary.py --help
python src/build_characteristics.py --help
npx --yes markdownlint-cli2@0.23.0 \
  '**/*.md' '.github/**/*.md'
git diff --check
```

For notebook changes, execute a copy from a clean kernel:

```bash
python -m nbconvert \
  --to notebook \
  --execute notebooks/stackexchange_eda.ipynb \
  --output-dir /tmp \
  --output stackexchange_eda.executed.ipynb \
  --ExecutePreprocessor.timeout=600
```

For extraction, schema, or calculation changes, also run the controlled pilot
described in the Markdown documentation and inspect its validation and metadata
files.
Record release-level evidence in `docs/reference/release-verification.tsv` and
update `PROJECT_CHECKLIST.md` when a verified completion claim changes.

## Submit the change

Open a pull request with a concise explanation of the purpose, affected
contracts, validation commands and results, and any data or documentation
impact. Keep unrelated changes in separate pull requests.
