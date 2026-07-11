# System reference

[Documentation home](../README.md) · [Tutorial](../tutorials/first-analysis.md) · [How-to guides](../how-to/access-data-dump.md) · [Reference](../reference/system-reference.md) · [Explanation](../explanation/design-and-scope.md)

## System architecture and components

| **Route**                   | **Required XML**                   | **Entry point**                                                      | **Primary output**                                          |
|-----------------------------|------------------------------------|----------------------------------------------------------------------|-------------------------------------------------------------|
| A — Complete thread         | Posts.xml, Comments.xml            | src/extract_threads.py                                               | One complete-thread XML file                                |
| B — Selected summary        | Posts.xml, Comments.xml            | src/extract_request_summary.py                                       | One configurable summary XML file                           |
| C — Characteristics and EDA | Posts.xml, Comments.xml, Votes.xml | src/build_characteristics.py, then notebooks/stackexchange_eda.ipynb | TSV, validation, metadata, tables, figures, interpretations |

| **Component**                     | **Responsibility**                                                                                      | **Input**                                                                    | **Output / interface**                                        |
|-----------------------------------|---------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|---------------------------------------------------------------|
| src/stackexchange_xml.py          | Shared streaming XML, row validation, ordering, question-comment reading, and atomic XML writing rules. | XML paths and selected question IDs.                                         | Copied row dictionaries and library helpers.                  |
| src/extract_threads.py            | Complete-thread reconstruction.                                                                         | Posts.xml, Comments.xml, question IDs.                                       | One XML file; command and extract_threads function.           |
| src/extract_request_summary.py    | Configurable summary extraction.                                                                        | Posts.xml, Comments.xml, question IDs, summary TSV.                          | One XML file; command and extract_request_summaries function. |
| src/question_characteristics.py   | Transparent 47-field calculations.                                                                      | Selected question, answer, comment, and acceptance rows plus run provenance. | One characteristic dictionary per question.                   |
| src/build_characteristics.py      | Question selection, orchestration, validation, and publication.                                         | Three XML files, run settings, and schema.                                   | TSV, validation, metadata; command and run function.          |
| notebooks/stackexchange_eda.ipynb | Generic exploratory analysis.                                                                           | Compatible thread_characteristics.tsv.                                       | Tables, figures, interpretations, and inspection cases.       |

## Environment and dependencies

| **Requirement** | **Supported project range** | **Role**                                     |
|-----------------|-----------------------------|----------------------------------------------|
| Python          | 3.10 or newer               | Runtime for source modules and notebook.     |
| lxml            | \>=5.2,\<6                  | XML processing.                              |
| beautifulsoup4  | \>=4.12,\<5                 | Rendered HTML text processing.               |
| numpy           | \>=1.26,\<3                 | Numerical notebook operations.               |
| pandas          | \>=2.1,\<3                  | TSV loading, cleaning, grouping, and tables. |
| matplotlib      | \>=3.6,\<4                  | Notebook figures.                            |
| scipy           | \>=1.11,\<2                 | Spearman correlation calculations.           |
| IPython         | \>=8.20,\<10                | Notebook display support.                    |
| ipykernel       | \>=6.29,\<7                 | Jupyter kernel.                              |
| jupyterlab      | \>=4.2,\<5                  | Interactive notebook interface.              |
| nbconvert       | \>=6.5,\<8                  | Automated notebook execution and conversion. |
| Ruff            | \>=0.15,\<1                 | Repository source checks.                    |

`requirements.txt` defines the runtime and notebook environment.
`requirements-dev.txt` includes those dependencies and adds Ruff for repository checks.
The project requires filesystem read access to source XML and write access to selected
output locations. No project-specific environment variable is required.

| **Shell**          | **Virtual-environment activation command** |
|--------------------|--------------------------------------------|
| POSIX shell        | source .venv/bin/activate                  |
| Windows PowerShell | .venv\Scripts\Activate.ps1                 |

## GitHub repository

| Property | Current contract |
|---|---|
| Repository | `https://github.com/thearmankarapetyan/stackexchange-difficulty` |
| Visibility | Private during active project work. |
| Default branch | `main` |
| Change route | Short-lived branch, pull request, successful checks, squash merge. |
| Continuous integration | Python 3.10 and 3.12 source and CLI checks; Markdown checks and pilot notebook execution on Python 3.12. |
| Dependency automation | Weekly GitHub Actions updates; Python vulnerability alerts and automated security fixes. |
| Historical branch | `archive/legacy-corpus-scaffold` preserves the superseded remote scaffold. |

Contribution rules are in [`CONTRIBUTING.md`](../../CONTRIBUTING.md). The pull-request
template, ownership rules, CI workflow, and dependency policy are in `.github/`.

## Command-line interfaces

### Complete-thread extractor

```bash
python src/extract_threads.py \
  --dump-dir DUMP_DIR \
  --output OUTPUT \
  QUESTION_ID [QUESTION_ID ...]
```

| **Argument**        | **Requirement** | **Definition**                                                                                    |
|---------------------|-----------------|---------------------------------------------------------------------------------------------------|
| --dump-dir DUMP_DIR | Required        | Folder containing Posts.xml and Comments.xml.                                                     |
| --output OUTPUT     | Required        | Destination XML file.                                                                             |
| QUESTION_ID         | One or more     | Positive decimal question post IDs. Request order is preserved and repeated IDs are written once. |
| -h, --help          | Optional        | Display command help and exit.                                                                    |

### Selected-summary extractor

```bash
python src/extract_request_summary.py \
  --dump-dir DUMP_DIR \
  --output OUTPUT \
  [--fields FIELDS] \
  QUESTION_ID [QUESTION_ID ...]
```

| **Argument**        | **Requirement** | **Definition**                                                                                    |
|---------------------|-----------------|---------------------------------------------------------------------------------------------------|
| --dump-dir DUMP_DIR | Required        | Folder containing Posts.xml and Comments.xml.                                                     |
| --output OUTPUT     | Required        | Destination XML file.                                                                             |
| --fields FIELDS     | Optional        | Summary-field TSV. The default is config/summary_fields.tsv.                                      |
| QUESTION_ID         | One or more     | Positive decimal question post IDs. Request order is preserved and repeated IDs are written once. |
| -h, --help          | Optional        | Display command help and exit.                                                                    |

### Characteristic builder

```bash
python src/build_characteristics.py \
  --dump-dir DUMP_DIR \
  --site SITE \
  --dump-date DUMP_DATE \
  --start-date START_DATE \
  --end-date END_DATE \
  --output-dir OUTPUT_DIR \
  [--schema SCHEMA] [--limit LIMIT] [--overwrite]
```

| **Argument**            | **Requirement** | **Definition**                                                         |
|-------------------------|-----------------|------------------------------------------------------------------------|
| --dump-dir DUMP_DIR     | Required        | Folder containing Posts.xml, Comments.xml, and Votes.xml.              |
| --site SITE             | Required        | Community host for URLs and provenance, without a scheme or path.      |
| --dump-date DUMP_DATE   | Required        | Snapshot date represented by the dump, in YYYY-MM-DD form.             |
| --start-date START_DATE | Required        | First included question creation date, inclusive, in YYYY-MM-DD form.  |
| --end-date END_DATE     | Required        | Last included question creation date, inclusive, in YYYY-MM-DD form.   |
| --output-dir OUTPUT_DIR | Required        | Folder receiving the canonical TSV, validation, and metadata files.    |
| --schema SCHEMA         | Optional        | Characteristic specification TSV. Default: config/characteristics.tsv. |
| --limit LIMIT           | Optional        | Positive chronological question-row limit for a controlled run.        |
| --overwrite             | Optional        | Permit replacement of existing canonical outputs in OUTPUT_DIR.        |
| -h, --help              | Optional        | Display command help and exit.                                         |

All three command entry points return 0 after successful completion and 1 for handled
file, value, validation, or XML errors. Argument-parsing errors use argparse behavior
and a nonzero exit status.

## Source XML contracts

| **File**     | **Role in the project**                                                                                                                              | **Route use** |
|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------|---------------|
| Posts.xml    | Questions and answers share this file. PostTypeId 1 identifies questions; PostTypeId 2 identifies answers; ParentId links an answer to its question. | A, B, C       |
| Comments.xml | PostId links a comment to a post. The implemented routes select comments whose PostId is the selected question ID.                                   | A, B, C       |
| Votes.xml    | VoteTypeId 1 rows supply the recorded calendar day of an acceptance action for a currently accepted answer.                                          | C             |

- IDs used for selection and ordering are positive decimal integers.

- Selected source timestamps use YYYY-MM-DDTHH:MM:SS with an optional decimal fraction.

- The complete fractional timestamp participates in chronological ordering.

- Numeric ID resolves an exact timestamp tie.

- XML rows are streamed and cleared after their attributes are copied.

- Source attributes copied into complete-thread XML preserve their original names and
  values.

## Output contracts

### Complete-thread XML

Element hierarchy:

```text
threads
└── thread
    └── question [all source question attributes]
        ├── comments
        │   └── comment [all source comment attributes]
        └── answers
            └── answer [all source answer attributes]
```

Each distinct requested ID produces one thread in request order. Comments belong
directly to the question. Answers belong to the question through ParentId. Comments and
answers are ordered by complete CreationDate and then numeric ID. Empty comments and
answers containers remain present.

### Selected-summary XML

The root element is requests. Each distinct requested question produces one request
child in request order. Each request contains the enabled fields in summary TSV row
order. An unavailable selected value produces an empty XML element.

| **Default element**  | **Definition**                                                       |
|----------------------|----------------------------------------------------------------------|
| question_id          | Question post number.                                                |
| question_body        | Question content stored as rendered HTML.                            |
| question_date        | Question posting date and time.                                      |
| first_comment_id     | Earliest available direct question-comment number.                   |
| first_comment_text   | Earliest available direct question-comment content.                  |
| first_comment_date   | Earliest available direct question-comment posting time.             |
| first_answer_id      | Earliest available answer number.                                    |
| first_answer_body    | Earliest available answer content.                                   |
| first_answer_date    | Earliest available answer posting time.                              |
| accepted_answer_id   | Answer number stored in the question AcceptedAnswerId attribute.     |
| accepted_answer_body | Available content of the answer identified by AcceptedAnswerId.      |
| accepted_answer_date | Posting time of the available answer identified by AcceptedAnswerId. |

### Characteristic outputs

| **File**                   | **Contract**                                                                                                                                                                |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| thread_characteristics.tsv | One selected question per row and 47 tab-separated columns in config/characteristics.tsv order.                                                                             |
| validation.tsv             | One structural or source-comparison check per row with status PASS, WARN, or FAIL and an observed value.                                                                    |
| run_metadata.json          | Schema version and path, community, snapshot, period, limit, row count, generation time, elapsed time, Python version, absolute source-file details, and validation totals. |

The formatted definition of every characteristic is docs/reference/data-dictionary.xlsx.
Its rows follow the same 47 names and order as config/characteristics.tsv.

## Configuration contracts

### Characteristic specification

config/characteristics.tsv fixes the output position, characteristic name, calculation
group, availability stage, role, source, data type, unit or allowed values,
plain-language definition, calculation, interpretation, and empty-value meaning. The
calculation groups are Calculated by Stack Exchange, Calculated by us, and
Non-calculated.

### Summary-field selection

| **Column**       | **Contract**                                         |
|------------------|------------------------------------------------------|
| field            | Supported XML element name. Values are unique.       |
| include          | TRUE includes the field and FALSE omits it.          |
| source_record    | Supported source record used to obtain the value.    |
| source_attribute | Supported source attribute used to obtain the value. |
| meaning          | Plain-language field description.                    |

TSV row order controls XML child order. The loader rejects an unknown field, a duplicate
field, an invalid include value, a changed supported mapping, or a selection with no
enabled field. data/examples/summary_fields_compact.tsv is a six-field example.

## Notebook interface

| **Editable setting** | **Definition**                                                | **Default**                                |
|----------------------|---------------------------------------------------------------|--------------------------------------------|
| DATA_FILE            | Characteristic TSV analyzed by the run.                       | ../data/examples/characteristics_pilot.tsv |
| MIN_TAG_QUESTIONS    | Minimum question count required for a tag outcome comparison. | 20                                         |
| TOP_TAGS_TO_SHOW     | Maximum frequent tags displayed.                              | 15                                         |
| MIN_ABSOLUTE_RHO     | Minimum displayed absolute Spearman rank correlation.         | 0.30                                       |
| FDR_ALPHA            | Benjamini–Hochberg false-discovery-rate limit.                | 0.05                                       |
| MAX_CASES_TO_SHOW    | Maximum questions displayed in the final inspection table.    | 8                                          |

The notebook validates file existence, nonempty input, required columns, dates, numeric
values, TRUE/FALSE fields, one community, one snapshot, unique question IDs, and
temporal consistency before plotting.

| **Output**      | **Content**                                                                                  |
|-----------------|----------------------------------------------------------------------------------------------|
| Dataset summary | Community, question count, 47 source columns, question period, and dump snapshot.            |
| Figure 1        | Question outcome totals for answered, accepted, and closed questions.                        |
| Figure 2        | Cumulative question, answer, acceptance, and closure event evolution.                        |
| Figure 3        | Numeric distributions in complete labeled ranges, including open-ended extreme categories.   |
| Figures 4–5     | Frequent tags and tag outcome comparisons when the minimum evidence is available.            |
| Figure 6        | Spearman pairs meeting both false-discovery-rate control and the practical strength setting. |
| Final table     | Concrete question cases with identifiers, titles, URLs, and selection reasons.               |

## Validation, side effects, and failure behavior

| **Status** | **Meaning**                                                       | **Required response**                            |
|------------|-------------------------------------------------------------------|--------------------------------------------------|
| PASS       | The observed result meets the stated check.                       | The checked condition is accepted.               |
| WARN       | A documented source difference or unavailable event was observed. | Read and retain the observed value in reporting. |
| FAIL       | A structural requirement is violated.                             | Correct the input or implementation and rerun.   |

| **Component**                 | **Filesystem behavior**                                                    | **Handled failure behavior**                                                                                                                      |
|-------------------------------|----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| Thread and summary extractors | Create parent folders and atomically replace the selected destination XML. | Print an English contextual error, return 1, preserve source XML, and preserve a prior output when publication has not completed.                 |
| Characteristic builder        | Create three canonical files in the selected output folder.                | Refuse existing outputs without --overwrite, stop publication for internal FAIL, print a contextual error, and return 1.                          |
| EDA notebook                  | Updates saved notebook outputs when executed in place.                     | Raise a clear exception for missing or incompatible input, invalid values, mixed communities or snapshots, duplicate IDs, and inconsistent dates. |

| **Message fragment**                                   | **Meaning**                                                           |
|--------------------------------------------------------|-----------------------------------------------------------------------|
| Posts.xml file not found / Comments.xml file not found | The selected dump folder lacks an extractor input.                    |
| Missing required source file(s)                        | The characteristic route lacks Posts.xml, Comments.xml, or Votes.xml. |
| Question post ID(s) not found                          | The selected IDs do not occur in Posts.xml.                           |
| Post ID(s) are not questions                           | A selected ID belongs to another post type.                           |
| invalid CreationDate                                   | A selected source row has a timestamp outside the accepted dump form. |
| unknown / duplicate summary field                      | The selection violates the supported field catalogue.                 |
| Output already exists                                  | A canonical characteristic output exists in the destination.          |
| Internal validation failed                             | A generated characteristic result violates a structural check.        |
| Notebook missing required column                       | DATA_FILE identifies an incompatible table.                           |

## Deliverables, evidence, and terminology

### Deliverables register

| **Deliverable**              | **Canonical location**                                 | **Format**           | **Use and validation**                                                     |
|------------------------------|--------------------------------------------------------|----------------------|----------------------------------------------------------------------------|
| Python source                | src/\*.py                                              | Python               | Extraction and characteristic logic; compiled and controlled-run verified. |
| Runtime dependencies         | requirements.txt                                       | Text                 | Clean-environment runtime and notebook contract.                            |
| Development dependencies     | requirements-dev.txt                                   | Text                 | Runtime dependencies plus repository source checks.                         |
| Markdown rules               | .markdownlint.json                                     | JSON                 | GitHub documentation lint configuration.                                    |
| Characteristic specification | config/characteristics.tsv                             | TSV                  | Defines 47 output columns and order.                                       |
| Summary catalogue            | config/summary_fields.tsv                              | TSV                  | Defines supported selected-summary fields.                                 |
| Workflow overview            | docs/project-workflow-overview.svg and .png            | SVG, PNG             | Editable source and 4800×3400 publication export.                          |
| Documentation set | docs/README.md and linked pages | Markdown | GitHub-native Diátaxis documentation. |
| Verified XML examples        | data/examples/\*.xml                                   | XML                  | Regeneration targets for complete-thread and summary routes.               |
| Characteristic pilot         | data/examples/characteristics_pilot\*.tsv              | TSV                  | 20×47 first-run evidence and nine PASS checks.                             |
| Generic EDA                  | notebooks/stackexchange_eda.ipynb                      | IPYNB                | Self-contained descriptive analysis.                                       |
| Data dictionary              | docs/reference/data-dictionary.xlsx                    | XLSX                 | Plain-language definitions for all 47 characteristics.                     |
| Published statistics         | docs/reference/stackexchange-published-statistics.xlsx | XLSX                 | Published network and tag statistics with sources.                         |
| Scientific review            | docs/explanation/state-of-the-art-qpp-ppp-rag.pdf      | PDF                  | QPP, PPP, and RAG research context.                                        |
| Release evidence             | docs/reference/release-verification.tsv                | TSV                  | Recorded verification matrix.                                              |
| Raw dumps                    | Selected external source-data folder                   | XML archive contents | Official inputs; excluded from version control.                            |
| Annual outputs               | data/processed/\<run-name\>/                           | TSV, JSON            | Regenerated results; ignored by version control.                           |

Tracked XML regeneration targets: data/examples/complete_thread_example.xml,
softwareengineering_request_summary_example.xml, superuser_request_summary_example.xml,
and configurable_request_summary_example.xml. The compact summary selection is
data/examples/summary_fields_compact.tsv.

### Verified environment and results

The release environment used Python 3.12.3 with Ruff 0.15.21, lxml 5.4.0,
beautifulsoup4 4.15.0, numpy
2.5.1, pandas 2.3.3, matplotlib 3.11.0, scipy 1.18.0, IPython 9.15.0, ipykernel 6.31.0,
JupyterLab 4.6.1, and nbconvert 7.17.1.

- Complete-thread and default-summary outputs match retained real-data examples byte for
  byte.

- The compact summary selection matches its six-field XML example byte for byte.

- The bundled pilot contains 20 questions, 47 columns, nine PASS checks, zero WARN, and
  zero FAIL.

- The verified annual Software Engineering run contains 950 questions and no validation
  warning or failure.

- The verified annual Super User run contains 11,578 questions, no validation failure,
  and documented count-difference warnings for eight answer counts and two comment
  counts.

- The generic notebook executes every code cell from a clean kernel.

Detailed evidence is recorded in docs/reference/release-verification.tsv. The verified
release tag is verified-release-2026-07-11.

### Glossary

| **Term**                     | **Definition**                                                                                                  |
|------------------------------|-----------------------------------------------------------------------------------------------------------------|
| Stack Exchange community     | One question-and-answer site in the Stack Exchange network, with its own topic and public dump.                 |
| Data dump                    | A downloadable archive containing a snapshot of public community data in XML files.                             |
| Dump snapshot                | The state and date represented by one downloaded dump.                                                          |
| Question period              | The inclusive creation-date range used to select questions for one characteristic run.                          |
| Thread                       | One question, comments attached directly to that question, and all available answers.                           |
| Question ID                  | The positive Posts.xml identifier of a PostTypeId 1 row. The same ID appears in the question page URL.          |
| Direct question comment      | A Comments.xml row whose PostId equals the selected question ID.                                                |
| Accepted answer              | The answer whose ID is stored in the question AcceptedAnswerId attribute.                                       |
| Characteristic               | One documented value describing question content, provenance, human activity, or snapshot context.              |
| Characteristic specification | config/characteristics.tsv, which defines the 47 output names, order, and field contracts.                      |
| Summary field selection      | A TSV catalogue whose TRUE rows select and order summary XML elements.                                          |
| Validation report            | validation.tsv, containing PASS, WARN, and FAIL checks with observed values.                                    |
| Run metadata                 | run_metadata.json, containing settings, source-file details, versions, and totals for one build.                |
| EDA                          | Exploratory data analysis through descriptive tables, figures, statistical associations, and interpreted cases. |
| Source-data folder           | A selected local folder containing the extracted official Stack Exchange XML files.                             |
| Results folder               | A selected location for generated XML, TSV, JSON, notebook, or validation outputs.                              |

### Canonical locations

| **Need**                  | **Canonical location**                      |
|---------------------------|---------------------------------------------|
| Project navigation        | README.md                                   |
| GitHub repository         | [thearmankarapetyan/stackexchange-difficulty](https://github.com/thearmankarapetyan/stackexchange-difficulty) |
| Current completion record | PROJECT_CHECKLIST.md                        |
| Documentation home | docs/README.md |
| Workflow diagram          | docs/project-workflow-overview.svg and .png |
| Characteristic meanings   | docs/reference/data-dictionary.xlsx         |
| Summary field selection   | config/summary_fields.tsv                   |
| Characteristic order      | config/characteristics.tsv                  |
| Verified examples         | data/examples/                              |
| Exploratory analysis      | notebooks/stackexchange_eda.ipynb           |
| Release evidence          | docs/reference/release-verification.tsv     |
