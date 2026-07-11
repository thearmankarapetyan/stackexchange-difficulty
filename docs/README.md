# Stack Exchange difficulty project documentation

This documentation explains the implemented workflow from official Stack Exchange dump
access to verified XML, TSV, and exploratory results. It applies the Diátaxis model with
separate pages for learning, completing a task, looking up exact facts, and understanding
the project choices.

Documentation revision: **11 July 2026**

The workflow accepts compatible Stack Exchange community dumps. Paths, communities,
dates, question IDs, summary fields, schemas, and output locations are selected for each
run. Super User and Software Engineering provide cross-site verification evidence.

## Workflow overview

![Stack Exchange project workflow](project-workflow-overview.png)

The editable diagram is [project-workflow-overview.svg](project-workflow-overview.svg).

## Choose the documentation you need

| Need | Page | Result |
|---|---|---|
| Complete one fixed first analysis | [Tutorial](tutorials/first-analysis.md) | Executed bundled pilot notebook |
| Accomplish a selected task | [How-to guides](#how-to-guides) | XML, TSV, metadata, notebook, or verified change |
| Look up an exact interface or contract | [System reference](reference/system-reference.md) | Commands, fields, formats, validation, and canonical locations |
| Understand the research and design choices | [Design and scientific scope](explanation/design-and-scope.md) | Context, reasoning, and interpretation boundaries |

## How-to guides

- [Access and prepare an official community dump](how-to/access-data-dump.md)
- [Create complete-thread XML](how-to/extract-complete-threads.md)
- [Create a selected-field summary XML](how-to/extract-summary-fields.md)
- [Build a validated characteristic table](how-to/build-characteristics.md)
- [Analyze a compatible characteristic table](how-to/run-eda.md)
- [Verify and record a project change](how-to/verify-changes.md)

## Choose a result route

| Required result | Procedure | Primary output |
|---|---|---|
| A question with its direct comments and all available answers | [Complete-thread extraction](how-to/extract-complete-threads.md) | Complete-thread XML |
| A configurable set of question, comment, answer, and accepted-answer fields | [Selected-field extraction](how-to/extract-summary-fields.md) | Selected-field summary XML |
| A validated question-level analytical dataset | [Characteristic construction](how-to/build-characteristics.md) | 47-column TSV, validation TSV, and metadata JSON |
| Tables, figures, interpretations, and selected cases | [Exploratory analysis](how-to/run-eda.md) | Executed generic EDA notebook |

## Current status and supporting material

- [Project status and completed verification](../PROJECT_CHECKLIST.md)
- [Release verification matrix](reference/release-verification.tsv)
- [Plain-language data dictionary](reference/data-dictionary.xlsx)
- [Scientific state of the art](explanation/state-of-the-art-qpp-ppp-rag.pdf)
- [Verified small examples](../data/examples/README.md)
