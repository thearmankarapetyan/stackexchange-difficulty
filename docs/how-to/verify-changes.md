# How to verify and record a project change

[Documentation home](../README.md) · [Tutorial](../tutorials/first-analysis.md) · [How-to guides](../how-to/access-data-dump.md) · [Reference](../reference/system-reference.md) · [Explanation](../explanation/design-and-scope.md)

> **Goal:** Publish a change only after its affected behavior and artifacts have been checked.

**Before starting:** Read PROJECT_CHECKLIST.md, identify affected routes and
deliverables, and use temporary verification material outside the active project
whenever practical.

> **1. Define the change boundary and run static checks.** List affected artifacts,
> compile changed Python modules outside the project tree, and run the project’s Ruff
> checks.
>
> **2. Run controlled behavior checks.** Exercise each affected extractor and build a
> small characteristic table after calculation or schema changes.
>
> **3. Inspect evidence.** Compare headers with the schema, confirm validation has no
> FAIL, review every WARN, and inspect metadata.
>
> **4. Execute and inspect presentation outputs.** Run the notebook from a clean kernel
> when affected, then render and review changed visual and structured artifacts at
> normal reading size.
>
> **5. Clean the project.** Remove temporary tests, previews, caches, bytecode, office
> locks, and checkpoints.
>
> **6. Record completion.** Run git diff --check, review the full change list, update
> release-verification.tsv and PROJECT_CHECKLIST.md, and record the change in Git.

> **Completion check:** The affected behavior is reproduced, all recorded checks pass, changed visual artifacts are readable, temporary material is absent, and the repository records the verified change.
