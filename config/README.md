# Configuration files

This folder contains the three tab-separated contracts used by the project. The
canonical explanations are on the root [`README.md`](../README.md) page.

| File | Routine use | Complete contract |
|---|---|---|
| [`characteristic_catalogue.tsv`](characteristic_catalogue.tsv) | The complete 138-characteristic research catalogue remains unchanged during routine processing. It records implementation status, source requirements, definitions, calculations, interpretations, and Dictionary v5 traceability. | [Complete characteristic catalogue contract](../README.md#complete-characteristic-catalogue-contract) |
| [`characteristics.tsv`](characteristics.tsv) | This file remains unchanged when a site, period, or output folder is selected. It defines the names and order of the 49 implemented analytical columns. | [Characteristic specification contract](../README.md#characteristic-specification-contract) |
| [`summary_fields.tsv`](summary_fields.tsv) | A run-specific copy supports changes to `include` values or row order. The canonical file defines 27 supported summary fields and enables 12 by default. | [Summary-field selection contract](../README.md#summary-field-selection-contract) |

The complete catalogue records every retained concept. The current schema is
the implemented question-level subset produced by `build_characteristics.py`.
The canonical data-dictionary workbook presents both layers and is rebuilt by
`src/build_data_dictionary.py`.

Catalogue IDs remain stable. New concepts are appended with the next ID, and
semantic aliases are recorded in `source_name_v5` on one canonical row.

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
