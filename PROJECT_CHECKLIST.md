# Stack Exchange Difficulty Project Checklist

Last reviewed: **2026-07-12**

This is the canonical project roadmap and completion record. A checked item has
an evidence path, validation command, or recorded result. Authored project
material is English. Source XML values, proper names, URLs, and quoted research
material retain their original form.

## Release record

- Canonical private repository:
  `https://github.com/thearmankarapetyan/stackexchange-difficulty`.
- Repository-comprehension pull request: `#8`, merged as
  `c8577ce7a436be2ffa96e89f81fd3be1fcc4b2ce`.
- Post-merge GitHub Actions run: `29164761612` (**2 jobs passed**).
- Verified release tag: `verified-release-2026-07-11`.
- Diátaxis guide revision tag: `diataxis-guide-2026-07-11`.
- Detailed evidence: `docs/reference/release-verification.tsv`.
- Evidence matrix: **93 PASS, 0 FAIL** — **71 current-release** rows and
  **22 historical-transition** rows.
- Thirteen-task completion audit: **14 PASS, 0 FAIL**.

## Task 1 — Main project documentation

Status: **Complete**

- [x] `README.md` is the single technical documentation and handover page.
- [x] It explains the implemented scope, three result routes, components,
  inputs, outputs, workflow, current evidence, scientific and design context,
  and scope boundaries.
- [x] Its contents, task index, inline cross-references, and glossary links lead
  directly to the relevant same-page heading.
- [x] Supporting figures, spreadsheets, TSV evidence, examples, and scientific
  material remain linked in their appropriate formats.
- [x] The quick orientation identifies the normal run choices, explains command
  notation, and links directly to plain-language file-format definitions.
- [x] The opening presents a concise data-workflow statement and direct action
  links before the result routes, workflow, and detailed reference index. The
  index is grouped by task, interface, and evidence.
- [x] Maintained authored surfaces use an impersonal, descriptive tone.
  First- and second-person project voice, conversational prompts, and direct
  instructions are absent; source data and quoted material remain unchanged.

Evidence: `README.md`; checks `GUIDE-01`–`GUIDE-08`, `README-01`–`README-09`,
`HANDOVER-01`–`HANDOVER-03`, `T13-01`, and `TONE-01` in the release evidence.

## Task 2 — Project structure and architecture

Status: **Complete**

- [x] The README tree identifies every important source, configuration, data,
  notebook, documentation, dependency, contribution, and security location.
- [x] The architecture and component tables explain all five Python modules and
  the generic notebook, including their relationships.
- [x] One editable SVG and one 4800×3400 PNG show the sequence from Stack
  Exchange access through environment preparation, the three implemented
  routes, validation, EDA, and final results.
- [x] The diagram contains route decisions, data-flow arrows, execution order,
  completion checks, and the corrective path after a failed check.
- [x] Diagram labels use configurable concepts and contain no personal path,
  fixed production community, fixed period, or fixed question ID.

Evidence: `README.md#repository-structure`,
`README.md#architecture-and-components`,
`docs/project-workflow-overview.svg`, `docs/project-workflow-overview.png`,
checks `FLOW-01`–`FLOW-03`, and `T13-02`.

## Task 3 — Getting-started guide

Status: **Complete**

- [x] The README lists Git, archive extraction, Python, runtime libraries, and
  the permissions and storage required by the workflow.
- [x] It gives the repository URL, clone command, virtual-environment commands,
  dependency installation, and POSIX and PowerShell activation commands.
- [x] It explains official Stack Exchange dump origin, account access, archive
  extraction, required XML files, and source-data placement.
- [x] The fixed tutorial states the first command, generated files, expected
  totals, validation checks, metadata checks, notebook steps, and success
  indicators.
- [x] The tutorial starts with a small controlled run before any complete-period
  execution.
- [x] The access procedure shows where to select a community, obtain the dump
  date, place extracted XML, and find a question ID in its page address.

Evidence: `README.md#environment-and-installation`,
`README.md#data-dump-access-and-preparation`,
`README.md#bundled-analysis-tutorial`, `HANDOVER-03`, `HANDOVER-06`, and
`T13-03`.

## Task 4 — Script and notebook reference

Status: **Complete**

- [x] The component reference gives a dedicated, directly linkable section to
  each of the five Python modules and the generic notebook.
- [x] Each executable component documents its purpose, required source files,
  accepted settings, validation, outputs, side effects, handled failures,
  command, process status, and expected result.
- [x] Library modules document their role, callers, inputs, returned values,
  assumptions, side effects, and error propagation.
- [x] Source XML, output XML, TSV, JSON, configuration, and notebook contracts
  state exact formats, fields, defaults, and ordering behavior.

Evidence: `README.md#component-reference` through
`README.md#validation-and-errors`, the three current `--help` outputs, and
`T13-04`.

## Task 5 — Python module introductions

Status: **Complete**

- [x] All five modules begin with English module docstrings.
- [x] Executable-module introductions state purpose, workflow role, required
  inputs, generated outputs, dependency source, a basic command, source-file
  safety, and important scope limitations.
- [x] Library-module introductions state their caller, responsibility,
  dependencies, data effects, and reason for existing; they do not invent a
  command-line interface.

Evidence: `src/*.py`, the module-docstring audit, and `T13-05`.

## Task 6 — Function and class documentation

Status: **Complete**

- [x] All 43 current functions have complete parameter and return type
  annotations and a concise English docstring; the project defines no classes.
- [x] Non-obvious streaming, row selection, schema loading, summary mapping,
  characteristic calculation, validation, orchestration, and atomic-writing
  functions explain their assumptions, returned result, side effects, and
  contextual failure behavior.
- [x] Obvious helpers retain short docstrings so documentation does not obscure
  simple code.
- [x] Module-level command examples cover behavior whose use is not evident from
  a function signature alone.

Evidence: `src/*.py`, AST documentation audit, compile and Ruff checks, and
`T13-06`.

## Task 7 — Process diagrams

Status: **Complete**

- [x] The integrated workflow diagram covers official data access, local input
  preparation, environment setup, route selection, complete-thread extraction,
  configurable summary extraction, characteristic construction, validation,
  EDA, outputs, and error recovery.
- [x] Inputs, processing stages, decisions, outputs, completion conditions, and
  principal failure corrections are visible in one non-repetitive diagram.
- [x] The editable SVG and publication PNG contain matching labels and have been
  inspected at full size and in the README.

Evidence: `docs/project-workflow-overview.svg`,
`docs/project-workflow-overview.png`, `README.md#workflow-overview`, checks
`FLOW-01`–`FLOW-03`, and `T13-07`.

## Task 8 — Notebook code organization

Status: **Complete**

- [x] One generic, self-contained notebook contains the analysis sequence,
  editable settings, direct pandas/Matplotlib/SciPy code, results, figures, and
  plain-language interpretations together.
- [x] The active project contains no site-specific notebook copy, notebook
  generator, large plotting-helper module, hidden display fallback, or stale
  legacy analysis path.
- [x] Logic shared by production routes lives in focused Python modules; code
  used only to explain the one notebook remains visible in that notebook.
- [x] A clean-kernel execution verifies cell order and independence from hidden
  state.
- [x] Saved tables and figures match a repeated clean execution of the current
  notebook and bundled pilot.

Evidence: `notebooks/stackexchange_eda.ipynb`, `src/`, checks `NB-01`,
`SRC-06`, `HANDOVER-05`, and `T13-08`.

## Task 9 — Script generalization and configuration

Status: **Complete**

- [x] Dump folders, output locations, community host, dump date, question
  period, row limit, schema, question IDs, summary selection, and notebook TSV
  are supplied through commands, configuration TSV files, or the visible
  notebook settings cell.
- [x] Production source contains no personal directory, verified-site constant,
  fixed production date, or fixed question ID.
- [x] The same source has been verified with compatible Super User and Software
  Engineering dumps and with temporary or selected output locations.
- [x] Defaults are limited to version-controlled project contracts and the
  bundled tutorial input.

Evidence: `src/`, `config/`, `notebooks/stackexchange_eda.ipynb`, cross-site
checks `BUILD-02`–`BUILD-04`, `SRC-03`, and `T13-09`.

## Task 10 — Reusability and code quality

Status: **Complete**

- [x] Five modules have focused responsibilities, common XML rules are shared,
  characteristic calculations follow one 47-field specification, and summary
  mappings follow one 27-field catalogue.
- [x] Names and errors are descriptive, inputs are validated, configuration is
  separated from processing, source XML is protected, and canonical files are
  written atomically.
- [x] Duplicate logic, stale helpers, notebook generators, previews, caches,
  bytecode, and obsolete active documentation paths are absent.
- [x] The repeatable change gate covers compilation, Ruff, controlled behavior,
  schema comparison, validation, metadata, clean-kernel execution, visual
  inspection, cleanup, and Git diff review.
- [x] Git history, pull requests, CI, dependency automation, security guidance,
  and checksum archives preserve maintainable project evolution.
- [x] Release evidence separates current-release checks from historical
  transition records, and the documented path succeeds from a fresh clone.

Evidence: `src/`, `config/`, `AGENTS.md`, `CONTRIBUTING.md`, `.github/`, the
repeatable gate below, checks `SRC-01`–`SRC-06`, `AUDIT-01`, `GH-01`–`GH-07`,
`HANDOVER-01`–`HANDOVER-07`, and `T13-10`.

## Task 11 — Practical example

Status: **Complete**

- [x] `data/examples/pilot_dump/` contains a small real XML subset with 20
  questions, 74 question-or-answer rows, 75 direct question comments, 12
  acceptance-vote rows, and a provenance manifest.
- [x] The fixed tutorial gives one uninterrupted sequence from bundled
  `Posts.xml`, `Comments.xml`, and `Votes.xml` through characteristic building,
  validation, metadata inspection, notebook execution, figures, and
  interpretation.
- [x] Generated pilot characteristics and validation match their tracked targets
  byte for byte: 20 rows, 47 columns, 9 PASS, 0 WARN, and 0 FAIL.
- [x] The tutorial identifies inputs, locations, commands, intermediate outputs,
  final results, success indicators, and the expected repeatability boundary for
  metadata timestamps and paths.
- [x] The uninterrupted tutorial succeeds from a fresh remote clone and a newly
  created Python environment.

Evidence: `data/examples/pilot_dump/`,
`data/examples/characteristics_pilot.tsv`,
`data/examples/characteristics_pilot_validation.tsv`,
`README.md#bundled-analysis-tutorial`, `HANDOVER-04`, `HANDOVER-06`, and
`T13-11`.

## Task 12 — Deliverables register

Status: **Complete**

- [x] The README separately registers maintained project artifacts and input,
  example, or generated artifacts.
- [x] Every registered deliverable states its canonical location, format,
  purpose, maintainer or generator, required input, opening or use method, and
  version-control status where applicable.
- [x] Source, configuration, documentation, workflow, XML examples, pilot XML,
  characteristic tables, validation, metadata, notebook, dictionary,
  statistics, scientific review, dependencies, and release evidence are
  covered.
- [x] Raw dumps are identified as external inputs, regenerated analytical runs
  as ignored outputs, and temporary verification material as disposable.

Evidence: `README.md#deliverables-register`, `.gitignore`, canonical-location
checks `PATH-01`, and `T13-12`.

## Task 13 — Installation and dependency files

Status: **Complete**

- [x] `requirements.txt` declares compatible ranges for every runtime, XML,
  notebook, numerical, plotting, and statistical dependency.
- [x] `requirements-dev.txt` includes the runtime set and declares Ruff for
  repository checks.
- [x] The README documents Python 3.10 or newer, environment creation,
  installation, shell activation, permissions, storage, and external tools.
- [x] Installation and execution were verified in a clean Python 3.12.3
  environment, and the exact observed package versions remain recorded.
- [x] Development-only Node.js and npm requirements for the Markdown check are
  stated in the environment reference.
- [x] GitHub CI repeats installation and source/interface checks on Python 3.10
  and 3.12 and executes the notebook on Python 3.12.

Evidence: `requirements.txt`, `requirements-dev.txt`,
`README.md#environment-and-installation`, checks `ENV-01`–`ENV-02`, `GH-06`,
`HANDOVER-06`, `HANDOVER-07`, and `T13-13`.

## Repeatable change verification gate

The gate applies to later changes, with an evidence-file update whenever
release behavior changes.

- [x] Changed Python modules compile outside the project tree.
- [x] Every affected extractor receives a controlled extraction.
- [x] Calculation or schema changes receive a small characteristic build.
- [x] Generated columns match `config/characteristics.tsv`.
- [x] Validation contains no FAIL, and every WARN receives review.
- [x] The notebook executes from a clean kernel.
- [x] Changed Markdown, XLSX, SVG, PNG, XML, TSV, and notebook figures receive
  inspection.
- [x] Risky behavior receives temporary tests that are removed after
  verification.
- [x] Previews, caches, bytecode, office locks, and checkpoints are absent.
- [x] `git diff --check`, complete-change review, checklist synchronization,
  and release-evidence synchronization complete the gate.
