# How to build a validated characteristic table

[Documentation home](../README.md) · [Tutorial](../tutorials/first-analysis.md) · [How-to guides](../how-to/access-data-dump.md) · [Reference](../reference/system-reference.md) · [Explanation](../explanation/design-and-scope.md)

> **Goal:** Generate the canonical question-level TSV, validation TSV, and run metadata JSON for a selected creation-date period.

**Before starting:** Prepare Posts.xml, Comments.xml, and Votes.xml, then select a
community host, dump snapshot date, inclusive question dates, and an empty output
folder.

## Run a controlled pilot

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

> **1. Read validation.tsv.** Confirm that no row has status FAIL and review every WARN
> with its observed value.
>
> **2. Read run_metadata.json.** Confirm the community, snapshot, question period,
> source files, row limit, and row count.
>
> **3. Inspect the TSV header.** Confirm that thread_characteristics.tsv follows
> config/characteristics.tsv and contains 47 columns.

## Run the selected complete period

After the controlled pilot passes, run the same command with a new output folder and
omit --limit. Use --overwrite only after reviewing the files already present in the
selected destination.

> **Completion check:** The destination contains thread_characteristics.tsv, validation.tsv, and run_metadata.json. Validation has no FAIL, every WARN has been reviewed, and metadata matches the intended execution. See the [command-line interfaces](../reference/system-reference.md#command-line-interfaces) and [output contracts](../reference/system-reference.md#output-contracts).
