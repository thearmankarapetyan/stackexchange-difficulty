# Contributing

This repository supports a documented research workflow. Changes should remain
small, understandable, reproducible, and compatible with Stack Exchange dumps
that follow the expected XML structure.

## Change preparation

1. The README [quick orientation](README.md#quick-orientation) and
   [`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md) establish the applicable
   scope. The README contents and reference index identify the affected section.
2. Each change uses a short-lived branch from `main` with a descriptive prefix
   such as `feature/`, `fix/`, or `docs/`.
3. Development uses an activated virtual environment containing the declared
   requirements:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements-dev.txt
   ```

## Project requirements

- Paths, communities, dates, question IDs, field selections, and output
  locations remain configurable.
- Authored material remains in English, and source content retains its original
  form.
- Authored project prose remains impersonal and descriptive. First- and
  second-person project voice, conversational prompts, and direct imperatives
  remain absent.
- One generic, self-contained EDA notebook remains canonical.
- A field-contract change includes corresponding catalogue, schema,
  data-dictionary, example, notebook, and documentation updates.
- Raw dumps, credentials, local environments, caches, and regenerated annual
  outputs remain outside Git.
- Secrets remain outside Git. Any exposed secret is revoked at its source and
  removed from repository history.

## Change validation

Validation commands run from the project root. The selected checks cover the
changed behavior. The minimum source checks are:

```bash
PYTHONPYCACHEPREFIX=/tmp/stackexchange-pycache python -m compileall -q src
python -m ruff check src
python src/extract_threads.py --help
python src/extract_request_summary.py --help
python src/build_characteristics.py --help
python src/build_data_dictionary.py --help
python src/build_data_dictionary.py --check
npx --yes markdownlint-cli2@0.23.0 \
  '**/*.md' '.github/**/*.md'
git diff --check
```

A notebook change requires execution of a copy from a clean kernel:

```bash
python -m nbconvert \
  --to notebook \
  --execute notebooks/stackexchange_eda.ipynb \
  --output-dir /tmp \
  --output stackexchange_eda.executed.ipynb \
  --ExecutePreprocessor.timeout=600
```

Extraction, schema, and calculation changes also require the
[controlled pilot](README.md#bundled-analysis-tutorial) plus inspection of its
validation and metadata files. Release-level evidence is recorded in
`docs/reference/release-verification.tsv`, and a verified completion-status
change is reflected in `PROJECT_CHECKLIST.md`.

## Change submission

Each pull request contains a concise explanation of its purpose, affected
contracts, validation commands and results, and data or documentation impact.
Unrelated changes remain in separate pull requests.
