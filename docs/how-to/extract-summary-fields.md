# How to create a selected-field summary XML

[Documentation home](../README.md) · [Tutorial](../tutorials/first-analysis.md) · [How-to guides](../how-to/access-data-dump.md) · [Reference](../reference/system-reference.md) · [Explanation](../explanation/design-and-scope.md)

> **Goal:** Create one XML file whose child fields and order match a selected summary-field TSV.

**Before starting:** Prepare Posts.xml and Comments.xml, collect question IDs, and
decide whether the default 12 fields or another supported selection is required.

## Use the default 12 fields

```bash
python src/extract_request_summary.py \
  --dump-dir /path/to/extracted-dump \
  --output /path/to/results/question-summary.xml \
  QUESTION_ID [QUESTION_ID ...]
```

## Use another supported selection

> **1. Copy the catalogue.** Copy config/summary_fields.tsv to a run-specific TSV file.
>
> **2. Select elements.** Keep TRUE in the include column for required elements and use
> FALSE for omitted elements.
>
> **3. Select element order.** Arrange the TSV rows in the order required in each
> request element.
>
> **4. Preserve mappings.** Keep field, source_record, and source_attribute values from
> the supported catalogue.

```bash
python src/extract_request_summary.py \
  --dump-dir /path/to/extracted-dump \
  --output /path/to/results/question-summary.xml \
  --fields /path/to/run-summary-fields.tsv \
  QUESTION_ID [QUESTION_ID ...]
```

> **Completion check:** The command returns successfully, the XML has one request per distinct selected question, and its child elements follow the chosen TSV order. Selected unavailable values appear as empty elements. See the [configuration contracts](../reference/system-reference.md#configuration-contracts).
