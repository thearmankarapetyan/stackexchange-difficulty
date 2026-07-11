# Run the bundled 20-question analysis

[Documentation home](../README.md) · [Tutorial](../tutorials/first-analysis.md) · [How-to guides](../how-to/access-data-dump.md) · [Reference](../reference/system-reference.md) · [Explanation](../explanation/design-and-scope.md)

In this tutorial, we will execute the existing exploratory notebook with the verified
table included in the project. We will see the dataset summary, outcome figures,
cumulative evolution, distributions, tags, and selected cases.

> **Result:** An executed copy of notebooks/stackexchange_eda.ipynb whose cells complete without an exception and whose available figures are readable and interpreted.

## Confirm the starting files

Open the project root and confirm that these files exist:

```text
data/examples/characteristics_pilot.tsv
data/examples/characteristics_pilot_validation.tsv
notebooks/stackexchange_eda.ipynb
requirements.txt
```

> **Expected result:** The characteristic table and validation table open as
> tab-separated text. The notebook opens as a Jupyter notebook.

## Create the Python environment

Run the following commands from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

> **Expected result:** The installation finishes successfully and the active terminal
> prompt usually begins with (.venv).

## Open the notebook

```bash
python -m jupyter lab
```

> **Expected result:** JupyterLab opens in a browser and shows the project files. Keep
> the terminal session running while JupyterLab is open.

## Run the fixed pilot

> **1. Open the notebook.** Select notebooks/stackexchange_eda.ipynb in JupyterLab.
>
> **2. Keep the provided settings.** The DATA_FILE value already selects
> ../data/examples/characteristics_pilot.tsv.
>
> **3. Run the complete notebook.** Use Restart Kernel and Run All Cells from the Kernel
> menu.
>
> **4. Follow the outputs.** Read each displayed table, figure, interpretation, and
> availability message in order.
>
> **Expected result:** The first summary reports one community, 20 questions, 47 source
> columns, one question period, and one dump snapshot. No cell displays a Python
> exception.

## Notice the visible evidence

- Figure 1 reports 19 questions with an available answer, 12 with an accepted answer,
  and 2 closed questions.

- Figure 2 shows how question, answer, acceptance, and closure totals accumulate through
  time.

- Figure 3 groups numeric results into complete, readable ranges.

- Figure 4 shows the frequent tags in this 20-question table.

- Later sections display a figure when the pilot contains sufficient evidence and
  display a clear availability message when it does not.

- The final inspection table identifies concrete questions and states why each case was
  selected.

> **Expected result:** Every displayed figure is followed by a plain-language
> interpretation. The final output provides question IDs, titles, links, and selection
> reasons.

## Repeat the result

Run Restart Kernel and Run All Cells once more. The same input should produce the same
tables, figures, and availability messages.

> **Expected result:** The second run completes without an exception and preserves the
> same reported pilot totals.

> **Completed:** You have opened a documented characteristic table, executed the generic analysis from a clean kernel, checked the expected evidence, and reproduced the result. Continue with the [how-to guides](../how-to/access-data-dump.md) when you are ready to use a selected community dump or another compatible table.
