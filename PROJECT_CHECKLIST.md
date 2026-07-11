# Stack Exchange Difficulty Project Checklist

Last reviewed: **2026-07-11**

This is the canonical project roadmap and completion record. A checked item has
an evidence path, validation command, or recorded result. Authored project
material is English. Source XML values, proper names, URLs, and quoted research
material retain their original form.

## Release record

- Initial baseline commit:
  `97555e6cda56d9c76293d995d01e07cf2291e728`.
- Completed implementation commit:
  `53212ec15000635d17743a74a5c6adb3f7f9ac16`.
- Verified release tag: `verified-release-2026-07-11`.
- Diátaxis guide revision tag: `diataxis-guide-2026-07-11`.
- GitHub publication commit: `2e934430`.
- Canonical private repository:
  `https://github.com/thearmankarapetyan/stackexchange-difficulty`.
- GitHub Actions publication run: `29151176595` (**2 jobs passed**).
- GitHub Markdown migration commit: `fac76b617be420824ff4cd4a0d5dbcf38e8a1b79`.
- GitHub Markdown verification run: `29152702947` (**2 jobs passed**).
- Single-page README implementation commit:
  `f910e247b9865032d4d9b696e8b1f8045c183b88`.
- Single-page README pull request: `#6`.
- Single-page README verification run: `29156971069` (**2 jobs passed**).
- Detailed evidence: `docs/reference/release-verification.tsv`.
- Current evidence matrix: **69 PASS, 0 FAIL**.
- Final committed-state audit: **25 PASS, 0 FAIL**.
- Previous DOCX guide audit: **25 PASS, 0 FAIL**.
- GitHub Markdown documentation audit: **28 PASS, 0 FAIL**.
- Single-page README audit: **18 PASS, 0 FAIL**.

## Task 1 — Finalize and integrate the canonical overview flowchart

Status: **Complete**

- [x] One editable source exists at
  `docs/project-workflow-overview.svg`.
- [x] One 4800×3400 publication export exists at
  `docs/project-workflow-overview.png`.
- [x] The flowchart starts with community selection, account access, profile
  settings, data-dump access, download, extraction, and environment setup.
- [x] The three implemented routes identify their real entry points, required
  inputs, configurable settings, outputs, and completion checks.
- [x] The summary route uses `config/summary_fields.tsv` and supports a copied
  selection.
- [x] The diagram contains no terminal command, personal path, fixed community,
  fixed date, fixed period, or fixed question ID.
- [x] Every label and route was checked against current source and the official
  Stack Exchange data-dump help page.
- [x] The full-size PNG and its rendering in `README.md` were inspected for
  readability, clipping, arrow direction, and missing information.

Evidence: `docs/project-workflow-overview.svg`,
`docs/project-workflow-overview.png`, `README.md`, and checks `FLOW-01`–
`FLOW-03` in the release evidence.

## Task 2 — Create the single-page English GitHub documentation

Status: **Complete**

- [x] `README.md` is the single project-documentation and handover page.
- [x] Its contents, task index, inline cross-references, and glossary links lead
  directly to the relevant heading on the same page.
- [x] The README explains the research purpose, implemented scope, components,
  inputs, outputs, workflow, validation, current evidence, and limitations.
- [x] The canonical workflow image and editable SVG are available from the page.
- [x] Diátaxis is preserved as one fixed tutorial, six goal-oriented how-to
  sections, one system-shaped reference section, and one scientific and design
  explanation section.
- [x] The fixed tutorial produces visible results early, gives expected evidence,
  and includes a repeatability check.
- [x] The how-to sections cover official dump access, complete-thread XML,
  configurable summary XML, characteristic construction, generic notebook
  execution, and change verification.
- [x] The reference documents all five Python modules, the notebook, exact
  interfaces, XML and output contracts, configuration, errors, deliverables,
  verified results, and canonical locations.
- [x] Markdown linting, same-page anchor validation, local-link checks, heading
  and fence checks, rendering, command checks, and English/genericity checks
  pass.

Evidence: `README.md`; checks `GUIDE-01`–`GUIDE-08` and `README-01`–
`README-07` in the release evidence.

## Task 3 — Add the glossary and one verified practical walkthrough

Status: **Complete**

- [x] The README glossary defines community, dump, snapshot, question period,
  thread, question ID, direct question comment, accepted answer,
  characteristic, schemas, validation, metadata, EDA, source-data folder, and
  results folder.
- [x] Important terms in the overview and procedures link directly to their
  same-page definitions.
- [x] One uninterrupted tutorial covers the bundled 20-question input,
  environment creation, notebook execution, expected evidence,
  interpretation, and a repeatability check.
- [x] Generic placeholders explain what must be selected for each production
  run; production behavior remains independent of a personal machine or site.
- [x] `data/examples/characteristics_pilot.tsv` provides a real 20×47 notebook
  input and `characteristics_pilot_validation.tsv` records 9 PASS, 0 WARN, and
  0 FAIL.
- [x] The README links the complete-thread, default-summary,
  configurable-summary, characteristic, dictionary, notebook, and release
  examples.
- [x] Success indicators cover generated files, row and column counts,
  validation, metadata, conditional figures, interpretations, and cell errors.

Evidence: `README.md`, `data/examples/`, and checks `BUILD-01`–`BUILD-04`,
`NB-01`, `PATH-01`, `README-02`, and `README-03`.

## Task 4 — Make summary-field selection genuinely configurable

Status: **Complete**

- [x] `config/summary_fields.tsv` documents 27 supported fields, source records,
  source attributes, meanings, and default inclusion.
- [x] Its 12 enabled rows preserve the original requested output and order.
- [x] `--fields` accepts a copied TSV whose TRUE/FALSE values and row order
  select the XML elements.
- [x] One or more question IDs remain supported in requested order with
  deduplication.
- [x] Unknown fields, duplicate fields, changed source mappings, invalid include
  values, and empty selections produce contextual errors.
- [x] Chronological first-comment and first-answer selection, accepted-answer
  lookup, empty elements, safe writing, and source protection remain intact.
- [x] `data/examples/summary_fields_compact.tsv` and
  `configurable_request_summary_example.xml` demonstrate a six-field result.
- [x] Real default outputs match both original examples byte for byte; the
  configured output matches its new example byte for byte.

Evidence: `src/extract_request_summary.py`, `config/summary_fields.tsv`,
`config/README.md`, `data/examples/`, and checks `XML-02`–`XML-04`.

## Task 5 — Finish the focused source and maintainability audit

Status: **Complete**

- [x] All five modules compile and pass Ruff static checks.
- [x] Every current function has a concise docstring and complete type
  annotations.
- [x] Production source contains no personal path, verified-site constant,
  fixed analysis year, or fixed dump date.
- [x] The duplicate characteristic comment reader was removed and the shared
  bounded-memory reader is used.
- [x] Exact-time question sorting now includes the documented numeric ID
  tie-break.
- [x] Schema header, position, empty-name, and duplicate-name errors now include
  the schema path and a clear explanation.
- [x] The nested TSV writer callback has a direct name and concise explanation.
- [x] The notebook audit corrected source-column reporting, empty-tag behavior,
  input validation, and the Figure 2 legend overlap.
- [x] Thirteen temporary characterization tests covered public behavior,
  configuration errors, source-date errors, output preservation, ordering,
  multiple IDs, and bounded-memory scaling; the full suite passed repeatedly
  and was removed.
- [x] The independent committed-state audit passed 25 of 25 checks.

Evidence: `src/`, `notebooks/stackexchange_eda.ipynb`, checks `SRC-01`–`SRC-06`,
`TEST-01`–`TEST-02`, and `AUDIT-01`.

## Task 6 — Consolidate and archive duplicate project artifacts

Status: **Complete**

- [x] The active project keeps one editable workflow source and one publication
  export.
- [x] One canonical README replaces the former central DOCX, language-specific
  copies, and split Markdown documentation pages.
- [x] Superseded HTML, spreadsheet, image, overview, tutorial, how-to,
  reference, and explanation variants were copied before removal.
- [x] Ten archived files have matching recorded sizes and SHA-256 values.
- [x] The two superseded DOCX files and eleven superseded Markdown pages have
  matching recorded sizes and SHA-256 values in their migration archives.
- [x] The initial Git baseline also preserves the pre-consolidation state.
- [x] Raw public dumps are classified as external ignored inputs.
- [x] Regenerated annual outputs are ignored and remain reproducible from source
  dumps and recorded metadata.
- [x] Temporary tests, generators, previews, caches, bytecode, office locks, and
  notebook checkpoints are classified as disposable and absent from the active
  project.

Evidence:
`../../archive/canonical-project-consolidation-2026-07-11/manifest.tsv`,
`../../archive/github-markdown-documentation-2026-07-11/manifest.tsv`,
`../../archive/single-page-readme-2026-07-11/manifest.tsv`, `.gitignore`,
`.gitattributes`, and checks `ARCHIVE-01`–`ARCHIVE-04`, `README-04`, and
`CLEAN-01`.

## Task 7 — Create and record the first Git baseline

Status: **Complete**

- [x] `.gitignore` excludes raw dumps, regenerated outputs, Python environments,
  caches, editor settings, lock files, and temporary verification material.
- [x] `.gitattributes` preserves meaningful whitespace in copied source-content
  examples while allowing strict checks on authored text.
- [x] The complete initial file list passed `git diff --cached --check` before
  the baseline commit.
- [x] Baseline commit
  `97555e6cda56d9c76293d995d01e07cf2291e728` preserves the recovered canonical
  project before this release pass.
- [x] Implementation commit
  `53212ec15000635d17743a74a5c6adb3f7f9ac16` records the completed code,
  documentation, notebook, examples, and consolidation.
- [x] The final verified state is tagged `verified-release-2026-07-11`.

Evidence: Git history, `.gitignore`, `.gitattributes`, and checks `GIT-01`–
`GIT-02`.

## Task 8 — Perform final clean-environment release verification

Status: **Complete**

- [x] `requirements.txt` installed in a new Python 3.12.3 environment.
- [x] Direct versions were recorded for lxml, Beautiful Soup, NumPy, pandas,
  Matplotlib, SciPy, IPython, ipykernel, JupyterLab, and nbconvert.
- [x] A controlled real complete-thread extraction matched its tracked example.
- [x] Two real default summaries and one configured summary matched their
  tracked examples.
- [x] A controlled 20-question characteristic build produced 47 columns, 9 PASS,
  0 WARN, and 0 FAIL; metadata matches its intended source and settings.
- [x] Existing annual metadata and validation were rechecked for 950 Software
  Engineering rows and 11,578 Super User rows with no FAIL.
- [x] The notebook executed through the clean environment kernel with 21 cells,
  10 executed code cells, and no error.
- [x] Flowchart, Markdown documentation, notebook figures, data dictionary,
  statistics workbook, XML examples, TSV examples, and archives were visually
  or structurally inspected.
- [x] Every canonical deliverable path exists or is explicitly classified as an
  external/ignored input or regenerated output.
- [x] Cleanup removed all disposable project material.
- [x] `git diff --check` passed and the release change list was reviewed.

Evidence: `docs/reference/release-verification.tsv` and final tag
`verified-release-2026-07-11`.

## Task 9 — Publish and configure the canonical GitHub repository

Status: **Complete**

- [x] The canonical project is available in the private repository
  `https://github.com/thearmankarapetyan/stackexchange-difficulty`.
- [x] `main` contains only the current verified extraction, characteristic,
  validation, documentation, and generic EDA workflow.
- [x] The superseded 44-commit corpus scaffold remains recoverable on
  `archive/legacy-corpus-scaffold` and at tag
  `legacy-corpus-scaffold-2026-05-18`; it was not merged into active history.
- [x] Gitleaks 8.30.1 found no secret in the complete active history or the
  publication tree, and the local commit identity now uses the GitHub no-reply
  address.
- [x] Raw dumps, regenerated annual outputs, environments, caches, credentials,
  keys, and local secret files are excluded from version control.
- [x] The largest object in active history is far below GitHub's warning and
  rejection limits, so this repository does not need Git LFS.
- [x] GitHub Actions uses read-only workflow permissions, allows GitHub-owned
  actions only, requires full commit-SHA action references, and retains logs for
  30 days.
- [x] The clean CI matrix passed on Python 3.10 and 3.12; it compiled all source,
  ran Ruff, checked all three command-line interfaces, and executed the bundled
  pilot notebook on Python 3.12.
- [x] Dependabot checks GitHub Actions weekly. Python vulnerability alerts and
  automated security fixes are enabled; compatibility ranges are reviewed on
  both supported Python versions through the clean-environment gate.
- [x] `CONTRIBUTING.md`, `SECURITY.md`, `CODEOWNERS`, a pull-request template,
  and focused issue labels support controlled collaboration.
- [x] `main` is the default branch, squash is the only merge method, branches
  are deleted after merging, the wiki and unused project board are disabled,
  and repository purpose and topics are recorded.
- [x] Branch-protection compatibility was tested. GitHub returned the documented
  private-repository plan restriction, so the repository remains private and
  the successful CI checks remain available for pull-request review.
- [x] No public software license or citation authorship file was inferred. Those
  require an explicit institutional and authorship decision before a public
  release.

Evidence: publication commit `2e934430`, GitHub Actions run `29151176595`,
`.github/`, `CONTRIBUTING.md`, `SECURITY.md`, repository settings, and checks
`GH-01`–`GH-07` in the release evidence.

## Task 10 — Consolidate the project documentation into one linked README

Status: **Complete**

- [x] `README.md` contains the project overview, workflow, tutorial, six
  procedures, system reference, scientific and design explanation, glossary,
  deliverables, evidence, and canonical locations.
- [x] A linked contents list and a task-and-term index provide direct same-page
  navigation.
- [x] Important terms link to exact glossary definitions, and procedural text
  links to exact interface and contract sections.
- [x] Diátaxis roles remain visibly separated within the single page.
- [x] Commands use fenced Bash blocks and the XML hierarchy uses a text block.
- [x] The workflow uses the tracked PNG and SVG, with no duplicate extracted
  image or temporary absolute media path.
- [x] The eleven superseded Markdown pages were copied to a checksum-verified
  archive before removal from the active repository.
- [x] The active `docs/` tree retains supporting SVG, PNG, XLSX, TSV, and PDF
  artifacts and contains no competing Markdown documentation page.
- [x] Project instructions, contributor guidance, checklist evidence, and
  canonical locations identify the root README as the documentation source.
- [x] Markdownlint, heading hierarchy, fence balance, local links and anchors,
  rendering, English and genericity scans, and documented command checks pass.

Evidence: `README.md`,
`../../archive/single-page-readme-2026-07-11/manifest.tsv`, and checks
`README-01`–`README-07` in the release evidence.

## Repeatable change verification gate

Apply this gate to later changes and update the evidence file when release
behavior changes.

- [x] Compile changed Python modules outside the project tree.
- [x] Run a controlled extraction for each affected extractor.
- [x] Run a small characteristic build after calculation or schema changes.
- [x] Compare generated columns with `config/characteristics.tsv`.
- [x] Confirm validation has no FAIL and review every WARN.
- [x] Execute the notebook from a clean kernel.
- [x] Inspect changed Markdown, XLSX, SVG, PNG, XML, TSV, and notebook figures.
- [x] Use temporary tests for risky behavior and remove them after verification.
- [x] Remove previews, caches, bytecode, office locks, and checkpoints.
- [x] Run `git diff --check`, review the complete change list, and update this
  checklist and the release evidence.
