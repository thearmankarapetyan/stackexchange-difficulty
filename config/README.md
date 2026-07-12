# Configuration files

This folder contains the two tab-separated contracts used by the project. The
canonical explanations are on the root [`README.md`](../README.md) page.

| File | Routine use | Complete contract |
|---|---|---|
| [`characteristics.tsv`](characteristics.tsv) | This file remains unchanged when a site, period, or output folder is selected. It defines the names and order of all 47 analytical columns. | [Characteristic specification contract](../README.md#characteristic-specification-contract) |
| [`summary_fields.tsv`](summary_fields.tsv) | A run-specific copy supports changes to `include` values or row order. The canonical file defines 27 supported summary fields and enables 12 by default. | [Summary-field selection contract](../README.md#summary-field-selection-contract) |

The summary extractor accepts `TRUE` and `FALSE` in the `include` column. The
`source_record` and `source_attribute` columns preserve each supported mapping
to the question, earliest direct question comment, earliest available answer,
or available accepted answer. The root glossary defines a
[direct question comment](../README.md#direct-question-comment) and an
[accepted answer](../README.md#accepted-answer). Selected unavailable values
become empty XML elements.

Edited copies retain the tab-separated format. Related definitions are
[TSV](../README.md#tsv), [XML](../README.md#xml), and the
[plain-language data dictionary](../docs/reference/data-dictionary.xlsx).
