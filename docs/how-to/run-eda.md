# How to analyze a compatible characteristic table

[Documentation home](../README.md) · [Tutorial](../tutorials/first-analysis.md) · [How-to guides](../how-to/access-data-dump.md) · [Reference](../reference/system-reference.md) · [Explanation](../explanation/design-and-scope.md)

> **Goal:** Run the generic notebook on a selected characteristic TSV and obtain readable descriptive results.

**Before starting:** Use a table produced by the current characteristic builder and keep
its validation and metadata beside it.

> **1. Open the notebook.** Open notebooks/stackexchange_eda.ipynb in JupyterLab.
>
> **2. Select the table.** In the Editable settings cell, set DATA_FILE to the selected
> thread_characteristics.tsv.
>
> **3. Adjust evidence-display settings when required.** Set tag eligibility, tag count,
> correlation strength, false-discovery rate, and final case count in the same cell.
>
> **4. Execute from the beginning.** Use Restart Kernel and Run All Cells.
>
> **5. Review the complete result.** Read the dataset summary, every table, every figure
> or availability message, every interpretation, and the final selected cases.

> **Completion check:** Every cell completes, the summary identifies the intended community and snapshot, available figures are readable, unavailable analyses state the evidence limitation, and each result has a plain-language interpretation. See the [notebook interface](../reference/system-reference.md#notebook-interface).
