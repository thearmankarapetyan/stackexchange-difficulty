# Stack Exchange Difficulty Project Checklist

Last reviewed: **2026-07-11**

This is the canonical roadmap for the current project. It records concrete
deliverables and keeps recurring setup, example, and validation work in one
verification gate.

## How to use this checklist

- `[x]` means that the result exists and has been verified against the stated
  evidence.
- `[ ]` means that work or final verification remains.
- Check an item only after recording its evidence path or validation command.
- Update the **Last reviewed** date whenever a status changes.
- Keep authored project material in English. Preserve source XML values,
  proper names, and quoted research material in their original form.
- Keep paths, sites, dates, question IDs, periods, and output locations
  configurable.
- Prefer one clear canonical deliverable over several overlapping versions.
- Treat the verification gate at the end as a repeatable procedure rather
  than an additional project task.

## Verified baseline

- [x] Five focused Python modules implement XML extraction, characteristic
  construction, shared XML rules, and transparent question calculations.
- [x] `config/characteristics.tsv` defines one ordered 47-field
  characteristic schema.
- [x] `extract_threads.py` creates one XML file containing one or more
  questions, their direct question comments, and all their answers.
- [x] `extract_request_summary.py` creates the current project-defined summary
  for one or more question IDs.
- [x] `build_characteristics.py` creates `thread_characteristics.tsv`,
  `validation.tsv`, and `run_metadata.json` from compatible Stack Exchange
  dumps.
- [x] `notebooks/stackexchange_eda.ipynb` is the single generic EDA notebook
  and has executed from a clean kernel without cell errors.
- [x] Verified XML examples and two validated annual characteristic datasets
  exist under `data/`.
- [x] Superseded project material has an existing checksum-tracked archive.

Evidence: `src/`, `config/characteristics.tsv`, `data/examples/`,
`data/processed/*/validation.tsv`, `data/processed/*/run_metadata.json`,
`notebooks/stackexchange_eda.ipynb`, and
`../../archive/legacy-current-workflow-2026-07-10/manifest.tsv`.

## Task 1 — Finalize and integrate the canonical overview flowchart

Status: **In progress**

- [x] Define the required scope: Stack Exchange access, local preparation,
  three existing processing routes, verification, and generated results.
- [x] Keep the flowchart generic across compatible Stack Exchange
  communities, folders, snapshots, periods, and question selections.
- [x] Remove terminal commands and implementation-level algorithms from the
  visual overview.
- [x] Identify the real entry points and outputs in the diagram:
  `extract_threads.py`, `extract_request_summary.py`,
  `build_characteristics.py`, and `stackexchange_eda.ipynb`.
- [ ] Create one editable canonical flowchart source under `docs/`.
- [ ] Export one sharp, large-format PNG or PDF whose text is readable at
  normal page or slide size; the final raster export must be at least 3000
  pixels wide.
- [ ] Verify every label, filename, arrow, decision, and output against the
  current source and the official Stack Exchange data-dump instructions.
- [ ] Insert or link the final diagram from the central English project guide.
- [ ] Replace or archive superseded workflow representations and update README
  links.

Current evidence: `src/*.py`, `notebooks/stackexchange_eda.ipynb`,
`https://stackoverflow.com/help/data-dumps`, and the workflow drafts under
`docs/`.

Acceptance: one diagram presents the complete implemented workflow without a
specific site, date, question ID, personal directory, terminal command, or
future research stage.

## Task 2 — Create one central English project guide

Status: **Open**

- [ ] Create `docs/stackexchange-project-guide.docx` as the primary handover
  document.
- [ ] Explain the project purpose, current scope, components, inputs, outputs,
  workflow, validation, and current limitations.
- [ ] Include the canonical overview flowchart from Task 1.
- [ ] Include concise sections for environment preparation, dump access,
  complete-thread extraction, project-defined summary extraction,
  characteristic construction, and use of the existing EDA notebook.
- [ ] Include one component reference covering all five Python modules and the
  generic notebook.
- [ ] Include one deliverables register containing each deliverable's purpose,
  canonical location, format, generator, inputs, expected contents, opening
  method, validation evidence, and version-control status.
- [ ] Incorporate useful, verified information from the four existing French
  DOCX files, rewrite it in clear English, and verify the resulting content.
- [ ] Link to the data dictionary, XML examples, processed examples, notebook,
  and scientific report without copying large artifacts into the guide.
- [ ] Update README and document cross-references after the guide is verified.

French source documents to consolidate:

- `docs/tutorials/premiere-analyse-guidee.docx`
- `docs/how-to/extraire-threads-et-champs-demandes.docx`
- `docs/reference/reference-commandes-et-fichiers.docx`
- `docs/explanation/choix-scientifiques-et-limites.docx`

Acceptance: the guide is concise, internally navigable, English-only, and
contains no undocumented knowledge required to understand or operate the
implemented project.

## Task 3 — Add the glossary and one verified practical walkthrough

Status: **Partially complete**

- [x] Small verified XML examples exist for complete-thread and summary
  extraction.
- [x] A pilot characteristic build and generic EDA workflow have already been
  executed.
- [ ] Add a concise glossary to the central guide defining: Stack Exchange
  community, data dump, dump snapshot, question period, thread, question ID,
  direct question comment, accepted answer, characteristic, characteristic
  specification, validation report, run metadata, EDA, source-data folder,
  and results folder.
- [ ] Add one uninterrupted walkthrough from a selected dump directory to the
  characteristic TSV, validation report, run metadata, notebook figures, and
  interpretation.
- [ ] Include short input and output excerpts and link to the existing complete
  XML and TSV examples.
- [ ] State how to recognize success and where each generated result is saved.
- [ ] Rerun every command shown in the walkthrough with generic paths and a
  small pilot limit.
- [ ] Conduct a handover check with someone unfamiliar with the implementation:
  ask them to identify the three routes, required inputs, generated outputs,
  question ID meaning, and success checks without verbal instructions.
- [ ] Record and correct every point that remains unclear.

Acceptance: the walkthrough can be completed from the guide without relying
on a personal path, a specific Stack Exchange site, or undocumented verbal
instructions.

## Task 4 — Make summary-field selection genuinely configurable

Status: **Open; current fixed behavior remains verified**

- [x] Record the current behavior accurately: `extract_request_summary.py`
  uses a fixed `OUTPUT_FIELDS` tuple and the current flowchart calls the result
  a **project-defined question summary**.
- [ ] Define a small documented catalogue of supported summary fields.
- [ ] Choose a simple, readable external field specification, preferably TSV,
  while preserving the current field set as the default.
- [ ] Allow one or more question IDs and a selected field specification without
  introducing a complex expression language.
- [ ] Reject unknown, duplicate, or incompatible field names with clear error
  messages.
- [ ] Preserve chronological first-comment and first-answer behavior, accepted
  answer lookup, empty-element behavior, safe XML writing, and current default
  output.
- [ ] Update CLI help, the central guide, examples, and validation evidence.
- [ ] Verify default-field output against the existing examples and verify one
  smaller alternative field selection.

Acceptance: changing supported summary fields uses a documented configuration
file. The present supervisor-requested field set remains the default.

## Task 5 — Finish the focused source and maintainability audit

Status: **Partially complete**

- [x] All five modules have English module docstrings.
- [x] Current functions have type annotations and concise docstrings.
- [x] The characteristic schema, calculations, validation, and generic EDA are
  separated into focused components.
- [ ] Review XML streaming, validation, filesystem writing, and orchestration
  functions for non-obvious exceptions, side effects, and assumptions.
- [ ] Review the nested writer callback in `build_characteristics.py` and keep
  it self-explanatory or add one concise explanation.
- [ ] Scan for stale paths, duplicate logic, dataset-specific constants, dead
  files, unclear error messages, and schema/dictionary disagreement.
- [ ] Confirm that every executable entry point works from a user-selected or
  temporary directory.
- [ ] Perform a readability review of the main public functions with someone
  unfamiliar with the implementation and record unclear terminology or flow.
- [ ] Add examples only where signatures and concise docstrings do not explain
  behavior adequately.

Acceptance: the active source remains simple enough to maintain, has no hidden
personal or dataset-specific dependency, and explains non-obvious risks without
repetitive documentation boilerplate.

## Task 6 — Consolidate and archive duplicate project artifacts

Status: **Partially complete**

- [x] A non-destructive checksum-tracked archive process exists.
- [ ] Inventory overlapping workflow files, documentation versions, previews,
  caches, and scratch outputs.
- [ ] Keep one editable workflow source and one publication export; archive
  superseded HTML, spreadsheet, image, or document variants that no longer
  serve a distinct purpose.
- [ ] After Task 2 is verified, archive the four superseded French documents
  and update every cross-reference.
- [ ] Classify raw public XML dumps as external inputs.
- [ ] Classify temporary tests, previews, caches, and scratch outputs as
  disposable verification material.
- [ ] Validate every retained relative path and archive checksum.

Acceptance: each active artifact has one clear purpose and canonical location;
no one must guess which of several similarly named workflow or documentation
files is current.

## Task 7 — Create and record the first Git baseline

Status: **Open**

- [ ] Review `.gitignore` so raw dumps, regenerated outputs, environments,
  caches, and disposable previews are excluded appropriately.
- [ ] Review the complete staged file list before committing.
- [ ] Create the initial baseline before beginning further structural source
  refactors.
- [ ] Record the commit identifier and verification date in this checklist.
- [ ] Use later commits or tags for supervisor-reviewed and final-release
  states and preserve continuous version history.

Acceptance: the active project has a reproducible version-control baseline and
future changes can be reviewed against a known state.

## Task 8 — Perform final clean-environment release verification

Status: **Final-release task**

- [ ] Install `requirements.txt` in a clean Python 3.10+ environment.
- [ ] Record the verified Python and package versions.
- [ ] Run a controlled complete-thread extraction.
- [ ] Run the default project-defined summary extraction and one configured
  field-selection example after Task 4 is complete.
- [ ] Run a controlled characteristic build and confirm that
  `validation.tsv` contains no `FAIL` result.
- [ ] Review every `WARN` and confirm `run_metadata.json` describes the intended
  sources, period, schema, and settings.
- [ ] Execute the generic notebook from a clean kernel and confirm that every
  cell completes without error.
- [ ] Visually inspect the final flowchart, DOCX guide, workbook, notebook
  figures, and example outputs at normal reading size.
- [ ] Verify every path in the deliverables register.
- [ ] Remove temporary tests, previews, caches, `__pycache__`, and notebook
  checkpoints.
- [ ] Run `git diff --check`, review the complete release change list, and
  record the final commit or tag.

Acceptance: a clean environment reproduces the documented outputs and every
published artifact passes its stated validation check.

## Repeatable change verification gate

These checks support tasks; they are not additional project deliverables. Run
the relevant subset after each verified change and the complete set before a
release.

- [ ] Compile every changed `src/*.py` file without leaving bytecode in the
  project.
- [ ] Run a small controlled extraction for each changed extractor.
- [ ] Run a small characteristic build after schema or calculation changes.
- [ ] Compare the generated TSV header with `config/characteristics.tsv` after
  schema changes.
- [ ] Confirm that `validation.tsv` has no `FAIL`; review all `WARN` entries.
- [ ] Execute the notebook from a clean kernel after notebook or schema changes.
- [ ] Visually inspect changed images, DOCX files, XLSX files, and notebook
  figures at normal reading size.
- [ ] Use temporary characterization tests for risky refactors and remove them
  after all required checks pass.
- [ ] Remove temporary previews, caches, bytecode, and notebook checkpoints.
- [ ] Run `git diff --check` and review the complete change list.
- [ ] Update evidence, affected checkboxes, and the **Last reviewed** date in
  this file.
