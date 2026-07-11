# Stack Exchange human–model difficulty

This project prepares reproducible Stack Exchange evidence for studying
question difficulty. It reconstructs complete question threads, extracts
configurable XML summaries, builds one documented 47-field question table,
validates each analytical run, and provides one generic exploratory notebook.

The production workflow accepts compatible Stack Exchange community dumps and
user-selected paths, dates, question IDs, field selections, schemas, and output
locations. Its behavior has been verified with Super User and Software
Engineering data.

## Get the repository

The repository is private during active project work. After access has been
granted, clone it and enter its root folder:

```bash
git clone https://github.com/thearmankarapetyan/stackexchange-difficulty.git
cd stackexchange-difficulty
```

## Start here

1. Read the complete operating guide:
   [`docs/stackexchange-project-guide.docx`](docs/stackexchange-project-guide.docx).
2. Open the canonical workflow:
   [`docs/project-workflow-overview.png`](docs/project-workflow-overview.png).
   Its editable source is
   [`docs/project-workflow-overview.svg`](docs/project-workflow-overview.svg).
3. Check current status and evidence in
   [`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md).

The guide applies Diátaxis inside one document. A short orientation points to
four deliberately separated parts: one fixed first-run tutorial, goal-oriented
how-to guides, system-shaped reference material, and explanations of the
scientific and technical choices.

## Implemented routes

| Need | Entry point | Inputs | Result |
|---|---|---|---|
| Complete question threads | `src/extract_threads.py` | `Posts.xml`, `Comments.xml`, one or more question IDs | One XML file containing each question, its direct question comments, and all available answers |
| Configurable question summaries | `src/extract_request_summary.py` | `Posts.xml`, `Comments.xml`, question IDs, optional field-selection TSV | One XML file containing the selected fields in the configured order |
| Characteristics and EDA | `src/build_characteristics.py`, then `notebooks/stackexchange_eda.ipynb` | `Posts.xml`, `Comments.xml`, `Votes.xml`, run settings, characteristic schema | Characteristic TSV, validation TSV, run metadata JSON, tables, figures, and interpretations |

The default summary field file is `config/summary_fields.tsv`. Its twelve
enabled rows reproduce the original requested summary. Copy the TSV and change
its `TRUE`/`FALSE` values or row order to select another supported output.

## First runnable example

The notebook opens with the tracked 20-question pilot:

```text
data/examples/characteristics_pilot.tsv
```

Create an environment and run the notebook from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m nbconvert --to notebook --execute --inplace notebooks/stackexchange_eda.ipynb
```

The project guide explains how to download a community dump, build a new pilot,
read `validation.tsv` and `run_metadata.json`, and switch the notebook to the
new TSV.

## Canonical structure

- `src/` — five focused Python modules;
- `config/` — the characteristic schema and summary field catalogue;
- `data/examples/` — small verified XML, TSV, and field-selection examples;
- `data/raw/` — ignored location available for local source dumps;
- `data/processed/` — ignored location for regenerated analytical runs;
- `notebooks/stackexchange_eda.ipynb` — the single generic, self-contained EDA;
- `docs/reference/` — data dictionary, published statistics, and release evidence;
- `docs/explanation/` — recovery audit and scientific review;
- `docs/stackexchange-project-guide.docx` — the central project guide.

## Verification and version control

- Initial baseline commit: `97555e6cda56d9c76293d995d01e07cf2291e728`.
- Final verification evidence:
  `docs/reference/release-verification.tsv`.
- Raw dumps and regenerated annual tables stay outside version control.
- Replaced documentation and workflow drafts are preserved in the
  checksum-verified archive under
  `../../archive/canonical-project-consolidation-2026-07-11/`.

The current comparable annual evidence uses questions created from 1 January
through 31 December 2024 and the 20 April 2026 dump snapshot. The local annual
runs contain 950 Software Engineering questions and 11,578 Super User
questions, with no validation failure.

## Collaboration on GitHub

`main` is the canonical branch. Develop changes on a short-lived branch and
submit a pull request. GitHub Actions compiles the source, runs Ruff, checks the
three command-line interfaces, and executes the bundled pilot notebook on the
supported Python versions.

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before changing code, schemas,
documentation, or notebook behavior. Raw dumps, credentials, environments, and
regenerated annual outputs must remain outside version control.
