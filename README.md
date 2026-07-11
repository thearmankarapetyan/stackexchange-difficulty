# Stack Exchange human–model difficulty

This project prepares reproducible Stack Exchange evidence for studying question difficulty. It reconstructs complete [question threads](#thread), extracts configurable XML summaries, builds one documented 47-field [characteristic](#characteristic) table, publishes a [validation report](#validation-report) for each analytical run, and provides one generic [exploratory data analysis](#eda) notebook.

**Documentation revision:** 11 July 2026

This README is the canonical project documentation. Its linked contents and reference index lead directly to the relevant section of this page. Supporting source files, examples, spreadsheets, figures, and research material remain linked in their native formats.

## Contents

- [Find an answer](#find-an-answer)
- [Project overview](#project-overview)
- [Workflow overview](#workflow-overview)
- [Tutorial: run the bundled analysis](#tutorial-run-the-bundled-analysis)
- [How-to guides](#how-to-guides)
  - [Access and prepare a data dump](#access-and-prepare-a-data-dump)
  - [Create complete-thread XML](#create-complete-thread-xml)
  - [Create selected-field summary XML](#create-selected-field-summary-xml)
  - [Build a validated characteristic table](#build-a-validated-characteristic-table)
  - [Run the exploratory notebook](#run-the-exploratory-notebook)
  - [Verify and record a change](#verify-and-record-a-change)
- [System reference](#system-reference)
  - [Architecture and components](#architecture-and-components)
  - [Environment and installation](#environment-and-installation)
  - [Repository structure](#repository-structure)
  - [Command-line interfaces](#command-line-interfaces)
  - [Source XML contracts](#source-xml-contracts)
  - [Output contracts](#output-contracts)
  - [Configuration contracts](#configuration-contracts)
  - [Notebook interface](#notebook-interface)
  - [Validation and errors](#validation-and-errors)
  - [Deliverables register](#deliverables-register)
  - [Verified results](#verified-results)
- [Scientific and design explanation](#scientific-and-design-explanation)
- [Glossary](#glossary)
- [Canonical locations](#canonical-locations)

## Find an answer

Use this index as the entry point for a task or unfamiliar term.

| Need or term | Direct destination |
|---|---|
| Understand the project in a few minutes | [Project overview](#project-overview) |
| See the complete sequence from Stack Exchange access to results | [Workflow overview](#workflow-overview) |
| Run a first working example | [Bundled analysis tutorial](#tutorial-run-the-bundled-analysis) |
| Register, sign in, and access an official dump | [Access and prepare a data dump](#access-and-prepare-a-data-dump) |
| Reconstruct questions, comments, and answers | [Create complete-thread XML](#create-complete-thread-xml) |
| Select and order summary fields | [Create selected-field summary XML](#create-selected-field-summary-xml) |
| Produce the 47-column analytical table | [Build a validated characteristic table](#build-a-validated-characteristic-table) |
| Produce tables, figures, and interpretations | [Run the exploratory notebook](#run-the-exploratory-notebook) |
| Look up a command or parameter | [Command-line interfaces](#command-line-interfaces) |
| Understand `Posts.xml`, `Comments.xml`, or `Votes.xml` | [Source XML contracts](#source-xml-contracts) |
| Understand an output file | [Output contracts](#output-contracts) |
| Understand a notebook setting or figure | [Notebook interface](#notebook-interface) |
| Understand a PASS, WARN, FAIL, or error message | [Validation and errors](#validation-and-errors) |
| Understand an accepted answer | [Accepted answer](#accepted-answer) |
| Understand which comments form a thread | [Direct question comment](#direct-question-comment) |
| Understand the 47-field schema | [Characteristic specification](#characteristic-specification) |
| Understand configurable summary selection | [Summary field selection](#summary-field-selection) |
| Understand run provenance | [Run metadata](#run-metadata) |
| Understand source and result folders | [Source-data folder](#source-data-folder) · [Results folder](#results-folder) |
| Look up another technical term | [Glossary](#glossary) |
| Understand the 47 characteristics in plain language | [Data dictionary](docs/reference/data-dictionary.xlsx) |
| Check what has been verified | [Verified results](#verified-results) |
| Find a source, result, or supporting artifact | [Canonical locations](#canonical-locations) |

[Back to contents](#contents)

## Project overview

### Research purpose

The project studies observable signals associated with question difficulty in a setting where humans and generative models may experience difficulty differently. Stack Exchange supplies real questions together with traces of human response: answers, direct clarification comments, [accepted answers](#accepted-answer), closure, votes, views, tags, and elapsed times.

These traces describe community activity. Delayed answers, repeated clarification comments, closure, and the absence of an accepted answer can identify questions that deserve closer examination. Their meaning depends on the selected [dump snapshot](#dump-snapshot) and [question period](#question-period).

The implemented software prepares this evidence. It reconstructs threads, produces selected summaries, builds a documented question-level table, validates every analytical run, and presents exploratory results. Difficulty judgements and generative-model performance values require their own documented assessment protocols.

### Implemented result routes

| Route | Purpose | Required input | Entry point | Primary result |
|---|---|---|---|---|
| [Complete thread](#create-complete-thread-xml) | Preserve a question, its direct question comments, and every available answer | `Posts.xml`, `Comments.xml`, one or more question IDs | [`src/extract_threads.py`](src/extract_threads.py) | One complete-thread XML file |
| [Selected summary](#create-selected-field-summary-xml) | Create a compact report with selected and ordered fields | `Posts.xml`, `Comments.xml`, question IDs, optional field-selection TSV | [`src/extract_request_summary.py`](src/extract_request_summary.py) | One configurable summary XML file |
| [Characteristics and EDA](#build-a-validated-characteristic-table) | Build validated question-level evidence and explore it | `Posts.xml`, `Comments.xml`, `Votes.xml`, run settings, schema | [`src/build_characteristics.py`](src/build_characteristics.py), then [`notebooks/stackexchange_eda.ipynb`](notebooks/stackexchange_eda.ipynb) | TSV, validation, metadata, tables, figures, and interpretations |

The workflow accepts compatible Stack Exchange community dumps. Paths, communities, dates, question IDs, summary fields, schemas, and output locations are selected for each run. Super User and Software Engineering provide cross-site verification evidence.

[Back to contents](#contents)

## Workflow overview

![Stack Exchange project workflow](docs/project-workflow-overview.png)

Open the [full-size PNG](docs/project-workflow-overview.png) for reading or the [editable SVG](docs/project-workflow-overview.svg) for a reviewed diagram change.

The implemented sequence is:

1. Select a compatible [Stack Exchange community](#stack-exchange-community).
2. Create an account or sign in on that community.
3. Open profile settings, open data-dump access, and affirm the displayed declaration.
4. Download and extract the official [data dump](#data-dump).
5. Create a Python environment and install the declared dependencies.
6. Choose one implemented result route.
7. Supply run-specific paths, identifiers, dates, or field selections through the documented interfaces.
8. Inspect the generated XML or the TSV, validation, and metadata files.
9. Run the generic notebook when exploratory results are required.
10. Retain the source provenance, run settings, validation evidence, and generated result together.

Each route has a completion check in the [how-to guides](#how-to-guides). Exact arguments and file contracts are in the [system reference](#system-reference).

[Back to contents](#contents)

## Tutorial: run the bundled analysis

This tutorial executes the existing exploratory notebook with the verified table included in the repository. It provides a first visible result before requiring a public dump.

> **Result:** An executed copy of `notebooks/stackexchange_eda.ipynb` whose cells complete successfully and whose available figures are readable and interpreted.

### Confirm the tutorial files

From the project root, confirm that these files exist:

```text
data/examples/characteristics_pilot.tsv
data/examples/characteristics_pilot_validation.tsv
notebooks/stackexchange_eda.ipynb
requirements.txt
```

The characteristic and validation files open as tab-separated text. The notebook opens in JupyterLab.

### Create the Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The installation should complete successfully. The active POSIX terminal prompt usually begins with `(.venv)`.

### Open and run the notebook

```bash
python -m jupyter lab
```

1. Open `notebooks/stackexchange_eda.ipynb`.
2. Keep the provided `DATA_FILE` setting, which selects `../data/examples/characteristics_pilot.tsv` from the notebook folder.
3. Select **Restart Kernel and Run All Cells** from the JupyterLab Kernel menu.
4. Read each table, figure, interpretation, and availability message in order.

The first summary should report one community, 20 questions, 47 source columns, one question period, and one dump snapshot. Every code cell should complete without a Python exception.

### Check the visible evidence

- Figure 1 reports 19 questions with an available answer, 12 with an accepted answer, and 2 closed questions.
- Figure 2 shows how question, answer, acceptance, and closure totals accumulate through time.
- Figure 3 groups numeric results into complete, readable ranges.
- Figure 4 shows the frequent tags in this 20-question table.
- Later sections display a figure when the pilot contains sufficient evidence and an availability message when evidence is insufficient.
- The final inspection table identifies concrete questions and gives each selection reason.

Every displayed figure should have a plain-language interpretation. The final output should provide question IDs, titles, links, and selection reasons.

### Repeat the result

Select **Restart Kernel and Run All Cells** once more. The second run should preserve the same tables, figures, availability messages, and pilot totals.

> **Tutorial complete:** The generic analysis has been executed from a clean kernel, its expected evidence has been checked, and its result has been reproduced.

[Back to contents](#contents)

## How-to guides

These procedures start from a selected goal. Use the [command reference](#command-line-interfaces) when an exact argument definition is required.

### Access and prepare a data dump

> **Goal:** Place the XML files required by a selected processing route in one readable local folder.

**Before starting:** Select the Stack Exchange community, provide enough storage for its archive, and have an account on that community.

1. Open the selected Stack Exchange community and sign in or create an account.
2. Open the profile page, select **Settings**, then select **Data dump access** under **Access**.
3. Read and affirm the declaration presented by Stack Exchange.
4. Select **Download data** and wait for the archive download to finish.
5. Extract the archive into a selected local source-data folder.
6. Confirm `Posts.xml` and `Comments.xml` for the complete-thread and selected-summary routes.
7. Confirm `Posts.xml`, `Comments.xml`, and `Votes.xml` for the characteristic route.

Authoritative access instructions: [Stack Exchange Help Center — How do I access a data dump?](https://stackoverflow.com/help/data-dumps).

> **Completion check:** The source-data folder contains the XML files required by the selected route, and the files can be opened for reading.

### Create complete-thread XML

> **Goal:** Create one XML file containing one or more questions, each question's direct comments, and every available answer.

**Before starting:** Prepare `Posts.xml` and `Comments.xml`, then collect one or more [question IDs](#question-id) from the same community.

```bash
python src/extract_threads.py \
  --dump-dir /path/to/extracted-dump \
  --output /path/to/results/complete-threads.xml \
  QUESTION_ID [QUESTION_ID ...]
```

1. Select a destination XML path outside the source dump folder.
2. Run the extractor with the dump folder, destination, and question IDs in the required order.
3. Open the result and inspect the `threads` root and one `thread` element for every distinct selected ID.
4. Confirm each thread contains its `question`, `comments`, and `answers` elements.

> **Completion check:** The command succeeds, the destination is well-formed XML, and every selected question contains its direct question comments and all available answers.

### Create selected-field summary XML

> **Goal:** Create one XML file whose child fields and order match a selected summary-field TSV.

**Before starting:** Prepare `Posts.xml` and `Comments.xml`, collect question IDs, and decide whether the default 12 fields or another supported selection is required.

Use the default selection:

```bash
python src/extract_request_summary.py \
  --dump-dir /path/to/extracted-dump \
  --output /path/to/results/question-summary.xml \
  QUESTION_ID [QUESTION_ID ...]
```

Use another supported selection:

1. Copy [`config/summary_fields.tsv`](config/summary_fields.tsv) to a run-specific TSV file.
2. Keep `TRUE` in the `include` column for required elements and use `FALSE` for omitted elements.
3. Arrange the rows in the required XML child order.
4. Preserve each supported `field`, `source_record`, and `source_attribute` mapping.

```bash
python src/extract_request_summary.py \
  --dump-dir /path/to/extracted-dump \
  --output /path/to/results/question-summary.xml \
  --fields /path/to/run-summary-fields.tsv \
  QUESTION_ID [QUESTION_ID ...]
```

> **Completion check:** The command succeeds, the XML contains one `request` per distinct selected question, and each request follows the selected TSV field order. Selected unavailable values appear as empty elements.

### Build a validated characteristic table

> **Goal:** Generate the canonical question-level TSV, validation TSV, and run metadata JSON for a selected creation-date period.

**Before starting:** Prepare `Posts.xml`, `Comments.xml`, and `Votes.xml`, then select a community host, dump snapshot date, inclusive question dates, and an empty output folder.

Run a small controlled pilot first:

```bash
python src/build_characteristics.py \
  --dump-dir /path/to/extracted-dump \
  --site selected-community.example \
  --dump-date YYYY-MM-DD \
  --start-date YYYY-MM-DD \
  --end-date YYYY-MM-DD \
  --limit 20 \
  --output-dir /path/to/results/pilot-run
```

1. Open `validation.tsv`. Confirm every row avoids `FAIL` and review every `WARN` with its observed value.
2. Open `run_metadata.json`. Confirm the community, snapshot, question period, source files, row limit, and row count.
3. Inspect the TSV header. Confirm `thread_characteristics.tsv` follows [`config/characteristics.tsv`](config/characteristics.tsv) and contains 47 columns.
4. After the pilot passes, repeat the command with a new output folder and omit `--limit` for the selected complete period.
5. Use `--overwrite` only after reviewing the canonical files already present in the destination.

> **Completion check:** The destination contains `thread_characteristics.tsv`, `validation.tsv`, and `run_metadata.json`. Validation has no `FAIL`, every `WARN` has been reviewed, and metadata matches the intended execution.

### Run the exploratory notebook

> **Goal:** Run the generic notebook on a selected characteristic TSV and obtain readable descriptive results.

**Before starting:** Use a table produced by the current characteristic builder and keep its validation and metadata beside it.

1. Open [`notebooks/stackexchange_eda.ipynb`](notebooks/stackexchange_eda.ipynb) in JupyterLab.
2. In the **Editable settings** cell, set `DATA_FILE` to the selected `thread_characteristics.tsv`.
3. Adjust tag eligibility, tag count, correlation strength, false-discovery rate, and final case count only when the analytical need requires a change.
4. Select **Restart Kernel and Run All Cells**.
5. Read the dataset summary, every table, every figure or availability message, every interpretation, and the final selected cases.

> **Completion check:** Every cell completes, the summary identifies the intended community and snapshot, available figures are readable, unavailable analyses state the evidence limitation, and each result has a plain-language interpretation.

### Verify and record a change

> **Goal:** Publish a change after its affected behavior and artifacts have been checked.

1. Read [`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md) and identify affected routes and deliverables.
2. Compile changed Python modules outside the project tree and run the project's Ruff checks.
3. Exercise each affected extractor. Build a small characteristic table after calculation or schema changes.
4. Compare generated headers with the schema, confirm validation has no `FAIL`, review every `WARN`, and inspect metadata.
5. Execute the notebook from a clean kernel when it is affected. Render and inspect changed structured or visual artifacts at normal reading size.
6. Remove temporary tests, previews, caches, bytecode, office locks, and checkpoints.
7. Run `git diff --check`, review the complete change list, update [`docs/reference/release-verification.tsv`](docs/reference/release-verification.tsv) and the checklist, and record the change in Git.

> **Completion check:** The affected behavior is reproduced, all recorded checks pass, visual artifacts are readable, temporary material is absent, and the repository records the verified change.

[Back to contents](#contents)

## System reference

This section states the current interfaces and contracts. The [how-to guides](#how-to-guides) provide goal-oriented procedures.

### Architecture and components

| Component | Responsibility | Input | Output or interface |
|---|---|---|---|
| [`src/stackexchange_xml.py`](src/stackexchange_xml.py) | Shared streaming XML, row validation, ordering, question-comment reading, and atomic XML writing | XML paths and selected question IDs | Copied row dictionaries and library helpers |
| [`src/extract_threads.py`](src/extract_threads.py) | Complete-thread reconstruction | `Posts.xml`, `Comments.xml`, question IDs | One XML file; command and `extract_threads` function |
| [`src/extract_request_summary.py`](src/extract_request_summary.py) | Configurable summary extraction | `Posts.xml`, `Comments.xml`, question IDs, summary TSV | One XML file; command and `extract_request_summaries` function |
| [`src/question_characteristics.py`](src/question_characteristics.py) | Transparent 47-field calculations | Selected question, answer, comment, acceptance, and provenance values | One characteristic dictionary per question |
| [`src/build_characteristics.py`](src/build_characteristics.py) | Question selection, orchestration, validation, and publication | Three XML files, run settings, schema | TSV, validation, metadata; command and `run` function |
| [`notebooks/stackexchange_eda.ipynb`](notebooks/stackexchange_eda.ipynb) | Generic exploratory analysis | Compatible `thread_characteristics.tsv` | Tables, figures, interpretations, and inspection cases |

Shared source semantics—IDs, timestamps, ordering, question-comment selection, and safe output writing—live in the shared XML module. The characteristic calculations remain in a focused module. The notebook keeps its parameters, direct pandas, Matplotlib, and SciPy analysis code, results, and explanations together.

### Environment and installation

The project supports Python 3.10 or newer.

| Requirement | Compatible range | Role |
|---|---|---|
| Python | `>=3.10` | Source modules and notebook runtime |
| lxml | `>=5.2, <6` | XML processing |
| beautifulsoup4 | `>=4.12, <5` | Rendered HTML text processing |
| NumPy | `>=1.26, <3` | Numerical notebook operations |
| pandas | `>=2.1, <3` | TSV loading, cleaning, grouping, and tables |
| Matplotlib | `>=3.6, <4` | Notebook figures |
| SciPy | `>=1.11, <2` | Spearman correlation calculations |
| IPython | `>=8.20, <10` | Notebook display support |
| ipykernel | `>=6.29, <7` | Jupyter kernel |
| JupyterLab | `>=4.2, <5` | Interactive notebook interface |
| nbconvert | `>=6.5, <8` | Automated notebook execution and conversion |
| Ruff | `>=0.15, <1` | Repository source checks |

Clone the private repository after access has been granted:

```bash
git clone https://github.com/thearmankarapetyan/stackexchange-difficulty.git
cd stackexchange-difficulty
```

Create the runtime environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

`requirements.txt` defines the source and notebook environment. `requirements-dev.txt` adds Ruff for repository checks. The project needs read access to source XML and write access to selected output locations. It uses no project-specific environment variable.

| Shell | Environment activation command |
|---|---|
| POSIX shell | `source .venv/bin/activate` |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |

### Repository structure

```text
stackexchange-difficulty/
├── README.md                         Canonical project documentation
├── PROJECT_CHECKLIST.md              Completion and evidence record
├── src/                              Five production Python modules
├── config/                           Characteristic and summary contracts
├── data/
│   ├── examples/                     Small verified inputs and outputs
│   ├── raw/                          Ignored local dump location
│   └── processed/                    Ignored regenerated run location
├── notebooks/
│   └── stackexchange_eda.ipynb       Generic self-contained analysis
├── docs/
│   ├── project-workflow-overview.*   Editable and publication diagrams
│   ├── reference/                    Dictionary, statistics, release evidence
│   └── explanation/                  Scientific state-of-the-art report
├── requirements.txt                  Runtime and notebook dependencies
├── requirements-dev.txt              Development checks
├── CONTRIBUTING.md                   Change procedure
└── SECURITY.md                       Data and credential policy
```

### GitHub repository

| Property | Current contract |
|---|---|
| Repository | [thearmankarapetyan/stackexchange-difficulty](https://github.com/thearmankarapetyan/stackexchange-difficulty) |
| Visibility | Private during active project work |
| Default branch | `main` |
| Change route | Short-lived branch, pull request, successful checks, squash merge |
| Continuous integration | Python 3.10 and 3.12 source and CLI checks; Markdown checks and pilot notebook execution on Python 3.12 |
| Dependency automation | Weekly GitHub Actions updates; Python vulnerability alerts and automated security fixes |
| Historical branch | `archive/legacy-corpus-scaffold` preserves the superseded remote scaffold |

Contribution rules are in [`CONTRIBUTING.md`](CONTRIBUTING.md). Security and data-handling rules are in [`SECURITY.md`](SECURITY.md). Pull-request, ownership, continuous-integration, and dependency settings are under [`.github/`](.github/).

### Command-line interfaces

#### Complete-thread extractor command

```bash
python src/extract_threads.py \
  --dump-dir DUMP_DIR \
  --output OUTPUT \
  QUESTION_ID [QUESTION_ID ...]
```

| Argument | Requirement | Meaning |
|---|---|---|
| `--dump-dir DUMP_DIR` | Required | Folder containing `Posts.xml` and `Comments.xml` |
| `--output OUTPUT` | Required | Destination XML file |
| `QUESTION_ID` | One or more | Positive decimal question post IDs; request order is preserved and repeated IDs are written once |
| `-h`, `--help` | Optional | Display command help and exit |

#### Selected-summary extractor command

```bash
python src/extract_request_summary.py \
  --dump-dir DUMP_DIR \
  --output OUTPUT \
  [--fields FIELDS] \
  QUESTION_ID [QUESTION_ID ...]
```

| Argument | Requirement | Meaning |
|---|---|---|
| `--dump-dir DUMP_DIR` | Required | Folder containing `Posts.xml` and `Comments.xml` |
| `--output OUTPUT` | Required | Destination XML file |
| `--fields FIELDS` | Optional | Summary-field TSV; default: `config/summary_fields.tsv` |
| `QUESTION_ID` | One or more | Positive decimal question post IDs; request order is preserved and repeated IDs are written once |
| `-h`, `--help` | Optional | Display command help and exit |

#### Characteristic builder command

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

| Argument | Requirement | Meaning |
|---|---|---|
| `--dump-dir DUMP_DIR` | Required | Folder containing `Posts.xml`, `Comments.xml`, and `Votes.xml` |
| `--site SITE` | Required | Community host used for URLs and provenance; supply the host name |
| `--dump-date DUMP_DATE` | Required | Snapshot date represented by the dump in `YYYY-MM-DD` form |
| `--start-date START_DATE` | Required | First included question creation date, inclusive, in `YYYY-MM-DD` form |
| `--end-date END_DATE` | Required | Last included question creation date, inclusive, in `YYYY-MM-DD` form |
| `--output-dir OUTPUT_DIR` | Required | Folder receiving the canonical TSV, validation, and metadata files |
| `--schema SCHEMA` | Optional | Characteristic specification TSV; default: `config/characteristics.tsv` |
| `--limit LIMIT` | Optional | Positive chronological question-row limit for a controlled run |
| `--overwrite` | Optional | Permit replacement of existing canonical outputs in `OUTPUT_DIR` |
| `-h`, `--help` | Optional | Display command help and exit |

All three entry points return `0` after successful completion and `1` for handled file, value, validation, or XML errors. Argument-parsing errors follow `argparse` behavior and return a nonzero status.

### Source XML contracts

| File | Role | Used by route |
|---|---|---|
| `Posts.xml` | Stores questions and answers. `PostTypeId="1"` identifies questions, `PostTypeId="2"` identifies answers, and `ParentId` links an answer to its question. | All routes |
| `Comments.xml` | Stores comments. `PostId` links a comment to a post. The implemented routes select comments whose `PostId` equals the selected question ID. | All routes |
| `Votes.xml` | Supplies `VoteTypeId="1"` rows that record the calendar day of an acceptance action for a currently accepted answer. | Characteristics and EDA |

Source rules:

- Selection and ordering IDs are positive decimal integers.
- Selected timestamps use `YYYY-MM-DDTHH:MM:SS` with an optional decimal fraction.
- The complete fractional timestamp participates in chronological ordering.
- Numeric ID resolves an exact timestamp tie.
- XML rows are streamed and cleared after their attributes are copied.
- Complete-thread output preserves copied source attribute names and values.

### Output contracts

#### Complete-thread XML contract

```text
threads
└── thread
    └── question [all source question attributes]
        ├── comments
        │   └── comment [all source comment attributes]
        └── answers
            └── answer [all source answer attributes]
```

Each distinct requested ID produces one `thread` in request order. Comments attach directly to the question. Answers attach through `ParentId`. Comments and answers are ordered by complete `CreationDate` and then numeric ID. Empty `comments` and `answers` containers remain present.

#### Selected-summary XML contract

The root element is `requests`. Each distinct requested question produces one `request` child in request order. Every request contains enabled fields in summary TSV row order. An unavailable selected value produces an empty XML element.

The default catalogue enables these twelve fields:

| Default element | Meaning |
|---|---|
| `question_id` | Question post number |
| `question_body` | Question content stored as rendered HTML |
| `question_date` | Question posting date and time |
| `first_comment_id` | Earliest available direct question-comment number |
| `first_comment_text` | Earliest available direct question-comment content |
| `first_comment_date` | Earliest available direct question-comment posting time |
| `first_answer_id` | Earliest available answer number |
| `first_answer_body` | Earliest available answer content |
| `first_answer_date` | Earliest available answer posting time |
| `accepted_answer_id` | Answer number stored in the question's `AcceptedAnswerId` attribute |
| `accepted_answer_body` | Available content of the answer identified by `AcceptedAnswerId` |
| `accepted_answer_date` | Posting time of the available answer identified by `AcceptedAnswerId` |

#### Characteristic output contracts

| File | Contract |
|---|---|
| `thread_characteristics.tsv` | One selected question per row and 47 tab-separated columns in `config/characteristics.tsv` order |
| `validation.tsv` | One structural or source-comparison check per row with status `PASS`, `WARN`, or `FAIL` and an observed value |
| `run_metadata.json` | Schema version and path, community, snapshot, period, limit, row count, generation time, elapsed time, Python version, absolute source-file details, and validation totals |

The [plain-language data dictionary](docs/reference/data-dictionary.xlsx) explains what every characteristic is, how it works, how to read it, and what an empty value means. Its 47 rows follow the names and order in [`config/characteristics.tsv`](config/characteristics.tsv).

### Configuration contracts

#### Characteristic specification contract

[`config/characteristics.tsv`](config/characteristics.tsv) fixes each output position, characteristic name, calculation group, availability stage, role, source, data type, unit or allowed values, definition, calculation, interpretation, and empty-value meaning.

Its calculation groups are:

- **Calculated by Stack Exchange** — a value maintained by the platform and copied or represented by the project;
- **Calculated by us** — a value derived by the characteristic pipeline from source records;
- **Non-calculated** — an identifier, provenance field, source text, URL, date, category, or other value that is selected or assembled directly.

#### Summary-field selection contract

[`config/summary_fields.tsv`](config/summary_fields.tsv) contains 27 supported summary fields. Twelve are enabled in the default output.

| Column | Contract |
|---|---|
| `field` | Unique supported XML element name |
| `include` | `TRUE` includes the field; `FALSE` omits it |
| `source_record` | Supported source record used to obtain the value |
| `source_attribute` | Supported source attribute used to obtain the value |
| `meaning` | Plain-language field description |

TSV row order controls XML child order. The loader rejects unknown fields, duplicate fields, invalid `include` values, changed supported mappings, and a selection containing no enabled field. [`data/examples/summary_fields_compact.tsv`](data/examples/summary_fields_compact.tsv) is a six-field example.

### Notebook interface

The notebook has one visible **Editable settings** cell. Each setting is explained beside its value.

| Editable setting | Meaning | Default |
|---|---|---|
| `DATA_FILE` | Characteristic TSV analyzed by the run | `../data/examples/characteristics_pilot.tsv` |
| `MIN_TAG_QUESTIONS` | Minimum question count required for a tag outcome comparison | `20` |
| `TOP_TAGS_TO_SHOW` | Maximum frequent tags displayed | `15` |
| `MIN_ABSOLUTE_RHO` | Minimum displayed absolute Spearman rank correlation | `0.30` |
| `FDR_ALPHA` | Benjamini–Hochberg false-discovery-rate limit | `0.05` |
| `MAX_CASES_TO_SHOW` | Maximum questions displayed in the final inspection table | `8` |

The notebook validates file existence, nonempty input, required columns, dates, numeric values, `TRUE`/`FALSE` fields, one community, one snapshot, unique question IDs, and temporal consistency before plotting.

| Output | Content |
|---|---|
| Dataset summary | Community, question count, 47 source columns, question period, and dump snapshot |
| Figure 1 | Question outcome totals for answered, accepted, and closed questions |
| Figure 2 | Cumulative question, answer, acceptance, and closure event evolution |
| Figure 3 | Numeric distributions in complete labelled ranges, including open-ended extreme categories |
| Figures 4–5 | Frequent tags and tag outcome comparisons when the minimum evidence is available |
| Figure 6 | Spearman pairs meeting false-discovery-rate control and the practical strength setting |
| Final table | Concrete question cases with identifiers, titles, URLs, and selection reasons |

Every plot is followed by an explanation of what it shows, how to read it, its main observation, and why the result matters. An availability message explains when the selected data cannot support a particular figure.

### Validation and errors

| Status | Meaning | Required response |
|---|---|---|
| `PASS` | The observed result meets the stated check | Accept the checked condition |
| `WARN` | A documented source difference or unavailable event was observed | Read and retain the observed value in reporting |
| `FAIL` | A structural requirement is violated | Correct the input or implementation and rerun |

| Component | Filesystem behavior | Handled failure behavior |
|---|---|---|
| Thread and summary extractors | Create parent folders and atomically replace the selected destination XML | Print an English contextual error, return `1`, preserve source XML, and preserve a prior output until publication completes |
| Characteristic builder | Create three canonical files in the selected output folder | Refuse existing outputs unless `--overwrite` is supplied, stop publication for internal `FAIL`, print a contextual error, and return `1` |
| EDA notebook | Update saved notebook outputs when executed in place | Raise a clear exception for missing or incompatible input, invalid values, mixed communities or snapshots, duplicate IDs, and inconsistent dates |

| Message fragment | Meaning |
|---|---|
| `Posts.xml file not found` or `Comments.xml file not found` | The selected dump folder lacks an extractor input |
| `Missing required source file(s)` | The characteristic route lacks `Posts.xml`, `Comments.xml`, or `Votes.xml` |
| `Question post ID(s) not found` | The selected IDs do not occur in `Posts.xml` |
| `Post ID(s) are not questions` | A selected ID belongs to another post type |
| `invalid CreationDate` | A selected source row has a timestamp outside the accepted dump form |
| `unknown summary field` or `duplicate summary field` | The selection violates the supported field catalogue |
| `Output already exists` | A canonical characteristic output exists in the destination |
| `Internal validation failed` | A generated characteristic result violates a structural check |
| `Notebook missing required column` | `DATA_FILE` identifies an incompatible table |

### Deliverables register

| Deliverable | Canonical location | Format | Purpose and evidence |
|---|---|---|---|
| Canonical documentation | [`README.md`](README.md) | Markdown | Single-page project overview, tutorial, procedures, reference, explanation, and glossary |
| Python source | [`src/`](src/) | Python | Extraction and characteristic logic; compile and controlled-run verified |
| Runtime dependencies | [`requirements.txt`](requirements.txt) | Text | Clean-environment source and notebook contract |
| Development dependencies | [`requirements-dev.txt`](requirements-dev.txt) | Text | Runtime dependencies plus source checks |
| Characteristic specification | [`config/characteristics.tsv`](config/characteristics.tsv) | TSV | Defines 47 output columns and their order |
| Summary catalogue | [`config/summary_fields.tsv`](config/summary_fields.tsv) | TSV | Defines 27 supported summary fields and the default selection |
| Workflow overview | [`docs/project-workflow-overview.svg`](docs/project-workflow-overview.svg), [`PNG`](docs/project-workflow-overview.png) | SVG, PNG | Editable source and 4800 × 3400 publication export |
| Verified XML examples | [`data/examples/`](data/examples/) | XML | Regeneration targets for complete-thread and summary routes |
| Characteristic pilot | [`data/examples/characteristics_pilot.tsv`](data/examples/characteristics_pilot.tsv) and [validation](data/examples/characteristics_pilot_validation.tsv) | TSV | 20 × 47 first-run evidence and nine `PASS` checks |
| Generic EDA | [`notebooks/stackexchange_eda.ipynb`](notebooks/stackexchange_eda.ipynb) | IPYNB | Self-contained descriptive analysis |
| Data dictionary | [`docs/reference/data-dictionary.xlsx`](docs/reference/data-dictionary.xlsx) | XLSX | Plain-language definitions for all 47 characteristics |
| Published statistics | [`docs/reference/stackexchange-published-statistics.xlsx`](docs/reference/stackexchange-published-statistics.xlsx) | XLSX | Published network and tag statistics with sources |
| Scientific review | [`docs/explanation/state-of-the-art-qpp-ppp-rag.pdf`](docs/explanation/state-of-the-art-qpp-ppp-rag.pdf) | PDF | QPP, PPP, and RAG research context |
| Release evidence | [`docs/reference/release-verification.tsv`](docs/reference/release-verification.tsv) | TSV | Recorded verification matrix |
| Raw dumps | Selected external source-data folder | XML archive contents | Official inputs excluded from version control |
| Regenerated analytical runs | `data/processed/<run-name>/` | TSV, JSON | Reproducible local results excluded from version control |

Tracked XML regeneration targets are:

- [`complete_thread_example.xml`](data/examples/complete_thread_example.xml);
- [`softwareengineering_request_summary_example.xml`](data/examples/softwareengineering_request_summary_example.xml);
- [`superuser_request_summary_example.xml`](data/examples/superuser_request_summary_example.xml);
- [`configurable_request_summary_example.xml`](data/examples/configurable_request_summary_example.xml).

The compact six-field selection is [`summary_fields_compact.tsv`](data/examples/summary_fields_compact.tsv).

### Verified examples

The tracked examples make every implemented route inspectable while the large source dumps remain external:

- [`complete_thread_example.xml`](data/examples/complete_thread_example.xml) and [`softwareengineering_request_summary_example.xml`](data/examples/softwareengineering_request_summary_example.xml) use [Software Engineering question 450355](https://softwareengineering.stackexchange.com/questions/450355).
- [`superuser_request_summary_example.xml`](data/examples/superuser_request_summary_example.xml) uses [Super User question 1823849](https://superuser.com/questions/1823849).
- [`summary_fields_compact.tsv`](data/examples/summary_fields_compact.tsv) selects six supported fields, and [`configurable_request_summary_example.xml`](data/examples/configurable_request_summary_example.xml) contains its output for question 450355.
- The three default XML files were regenerated from the April 2026 public dumps with the canonical extractors.
- [`characteristics_pilot.tsv`](data/examples/characteristics_pilot.tsv) contains the first 20 Software Engineering questions selected chronologically from 1–8 January 2024 by the current 47-field builder.
- [`characteristics_pilot_validation.tsv`](data/examples/characteristics_pilot_validation.tsv) records nine `PASS`, zero `WARN`, and zero `FAIL` checks for that pilot.

The examples contain public Stack Exchange content, source URLs, available author identifiers, and content-licence fields. Preserve this provenance when sharing or reusing them.

### Verified results

The recorded release environment used Python 3.12.3 with Ruff 0.15.21, lxml 5.4.0, beautifulsoup4 4.15.0, NumPy 2.5.1, pandas 2.3.3, Matplotlib 3.11.0, SciPy 1.18.0, IPython 9.15.0, ipykernel 6.31.0, JupyterLab 4.6.1, and nbconvert 7.17.1.

- Complete-thread and default-summary outputs match retained real-data examples byte for byte.
- The compact summary selection matches its six-field XML example byte for byte.
- The bundled pilot contains 20 questions, 47 columns, nine `PASS` checks, zero `WARN`, and zero `FAIL`.
- The verified annual Software Engineering run contains 950 questions and no validation warning or failure.
- The verified annual Super User run contains 11,578 questions, no validation failure, and documented count-difference warnings for eight answer counts and two comment counts.
- The generic notebook executes every code cell from a clean kernel.

Detailed evidence is in [`docs/reference/release-verification.tsv`](docs/reference/release-verification.tsv). The verified release tag is `verified-release-2026-07-11`.

[Back to contents](#contents)

## Scientific and design explanation

### Information layers

| Information layer | Examples | Interpretive role |
|---|---|---|
| Provenance | Community, snapshot date, URL, content licence, source files | Identifies the evidence origin and supports reproduction |
| Question representation | Title, rendered body, tags, words, code, links, images | Describes question content available in the snapshot |
| Human-response evidence | Answers, comments, closure, acceptance, scores, views, delays | Describes community activity observed by the snapshot |
| Difficulty assessment | Documented manual judgement or model-performance value | Supplies a study outcome through a separate assessment method |

The characteristic table keeps provenance, platform-maintained values, project calculations, and assessment outcomes conceptually distinct. This separation supports traceability and keeps each analytical signal in its documented role.

### Why the project has three routes

Complete-thread XML preserves the richest source representation for reading and sharing. Selected-summary XML creates a compact file aligned with a reporting request. The characteristic route transforms source records into a stable analytical table and presents aggregate patterns and concrete cases through one notebook.

The three routes support source-rich qualitative inspection, focused information exchange, and systematic quantitative analysis. They share source rules where the semantics are identical.

### Snapshot-based evidence

#### Question state and observation time

`Posts.xml` represents the rendered question state in the downloaded snapshot. A title or body can include edits made after posting. Scores and views accumulate through the snapshot. `observation_days_at_dump` records the follow-up time available for each selected question. Historical pre-edit wording requires `PostHistory.xml`, which is outside the implemented workflow.

#### Platform counters and available rows

Stack Exchange maintains `AnswerCount` and `CommentCount` on the question row. The project also counts answer rows and direct question-comment rows available in the downloaded XML. Deleted or unavailable records can create differences. Both forms are retained, and `validation.tsv` records the observed differences as `WARN` rows.

#### Answer posting and acceptance

The accepted answer's `CreationDate` records when the answer was posted. A `Votes.xml` row with `VoteTypeId="1"` records the acceptance action at calendar-day precision. The table stores `accepted_answer_creation_datetime` and `time_to_eventually_accepted_answer_post_hours` separately from `acceptance_date` and `days_to_acceptance` so each event keeps its source meaning.

### Configurability and the generic notebook

Run-specific choices belong in command arguments, configuration TSV files, or the notebook settings cell. The same production logic therefore works with compatible communities, source folders, snapshots, date periods, question IDs, summary selections, schemas, and output locations.

The summary catalogue offers reviewed source mappings and allows each run to select and order required fields. The notebook applies one visible analysis sequence to every compatible characteristic TSV. Its explanations, settings, direct analysis code, figures, and interpretations remain together for inspection.

### Validation and reproducibility

The builder publishes `thread_characteristics.tsv` together with `validation.tsv` and `run_metadata.json`. Validation records structural checks and source differences. Metadata records the selected site, snapshot, question period, schema, limit, source files, software context, and output totals.

A controlled small run exposes input, schema, and calculation problems quickly. A clean-kernel notebook execution checks cell order and hidden state. Byte-for-byte XML comparisons verify stable extraction behavior. Visual review checks clipping, overlap, and readability. These checks create evidence that remains available after execution.

### Scope boundaries

- Complete-thread extraction contains comments attached directly to the question and all available answers. Answer comments are outside the agreed extraction scope.
- The characteristic table represents the current 47-field specification and selected dump snapshot.
- Acceptance events have calendar-day precision in public `Votes.xml` data.
- Deleted or unavailable source rows can create documented differences between platform counters and reconstructed row counts.
- Human-response traces support analysis and case selection. Difficulty categories require explicit assessment criteria.
- Raw dumps and regenerated annual outputs remain external or ignored because of their size.

The [scientific state-of-the-art report](docs/explanation/state-of-the-art-qpp-ppp-rag.pdf) provides the wider QPP, PPP, and RAG research context.

[Back to contents](#contents)

## Glossary

The links in the [reference index](#find-an-answer) and throughout this README point to these definitions.

### Accepted answer

The answer whose ID is stored in the question's `AcceptedAnswerId` attribute. Its posting time and the later acceptance action are separate events.

### Characteristic

One documented value describing question content, provenance, human activity, or snapshot context. The project publishes 47 characteristics per selected question.

### Characteristic specification

[`config/characteristics.tsv`](config/characteristics.tsv), which defines the 47 output names, order, types, roles, sources, calculations, and field contracts.

### Data dump

A downloadable archive containing a snapshot of public data from one Stack Exchange community. The project reads extracted XML files from this archive.

### Direct question comment

A `Comments.xml` row whose `PostId` equals the selected question ID. The complete-thread route includes these question comments.

### Dump snapshot

The state and date represented by one downloaded data dump. Scores, views, edits, available rows, and other source values are interpreted at this observation point.

### EDA

Exploratory data analysis using descriptive tables, figures, statistical associations, plain-language interpretations, and selected concrete cases. The project uses one generic Jupyter notebook for this work.

### Question ID

The positive `Posts.xml` identifier of a row with `PostTypeId="1"`. The same number appears in the Stack Exchange question page URL.

### Question period

The inclusive creation-date range used to select questions for one characteristic run.

### Results folder

A selected location that receives generated XML, TSV, JSON, notebook, or validation results.

### Run metadata

`run_metadata.json`, which records run settings, source-file details, versions, generation information, and output totals for one characteristic build.

### Source-data folder

A selected local folder containing the extracted official Stack Exchange XML files required by a route.

### Stack Exchange community

One specialised question-and-answer site in the Stack Exchange network, with its own topic, host name, and public data dump.

### Summary field selection

A TSV catalogue whose `TRUE` rows select summary XML elements and whose row order controls their output order.

### Thread

One question, comments attached directly to that question, and all available answers. The implemented thread scope excludes comments attached to answers.

### Validation report

`validation.tsv`, which contains `PASS`, `WARN`, and `FAIL` checks with their observed values for one characteristic build.

[Back to contents](#contents)

## Canonical locations

| Need | Canonical location |
|---|---|
| Complete project documentation | [`README.md`](README.md) |
| GitHub repository | [thearmankarapetyan/stackexchange-difficulty](https://github.com/thearmankarapetyan/stackexchange-difficulty) |
| Current completion record | [`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md) |
| Workflow diagram | [`docs/project-workflow-overview.svg`](docs/project-workflow-overview.svg) and [PNG](docs/project-workflow-overview.png) |
| Characteristic meanings | [`docs/reference/data-dictionary.xlsx`](docs/reference/data-dictionary.xlsx) |
| Summary field selection | [`config/summary_fields.tsv`](config/summary_fields.tsv) |
| Characteristic order and contracts | [`config/characteristics.tsv`](config/characteristics.tsv) |
| Verified examples | [`data/examples/`](data/examples/) |
| Exploratory analysis | [`notebooks/stackexchange_eda.ipynb`](notebooks/stackexchange_eda.ipynb) |
| Published Stack Exchange statistics | [`docs/reference/stackexchange-published-statistics.xlsx`](docs/reference/stackexchange-published-statistics.xlsx) |
| Scientific review | [`docs/explanation/state-of-the-art-qpp-ppp-rag.pdf`](docs/explanation/state-of-the-art-qpp-ppp-rag.pdf) |
| Release evidence | [`docs/reference/release-verification.tsv`](docs/reference/release-verification.tsv) |
| Contribution procedure | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Security and data handling | [`SECURITY.md`](SECURITY.md) |

[Back to contents](#contents)
