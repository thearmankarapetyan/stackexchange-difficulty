# Project instructions

- Read [`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md) before planning or
  modifying this project.
- Treat that checklist as the canonical roadmap. Check an item only after
  verifying its evidence, and update its **Last reviewed** date when status
  changes.
- Write authored documentation, code comments, command messages, notebook
  prose, and workbook labels in English. Preserve source data, XML values,
  proper names, and quoted research material in their original form.
- Keep production inputs configurable across compatible Stack Exchange sites;
  use the current verified sites as cross-site evidence and keep production
  behavior free of site-specific constants.
- Prefer simple code and concise documentation that can be understood by
  someone unfamiliar with the implementation.
- Maintain one central English project guide. Do not create another document
  when an existing guide section can carry the information clearly.
- Apply Diátaxis strictly inside that guide: keep orientation brief, make the
  tutorial concrete and choice-free, keep how-to guides focused on goals and
  actions, keep reference neutral and system-shaped, and reserve reasons,
  context, alternatives, and interpretation for explanation.
- Maintain one canonical editable overview flowchart and one publication
  export. Archive superseded workflow variants after verification.
- Keep the default summary behavior in `config/summary_fields.tsv`; use a
  copied field-selection TSV for run-specific summary outputs.
- Preserve one generic, self-contained EDA notebook. Do not add site-specific
  notebook copies, a notebook generator, or a large plotting-helper module.
- Do not modify raw dumps. Archive superseded project material
  non-destructively and record its checksum before removing the canonical copy.
- Verify a small controlled run before a full-period run. Compile changed
  modules, inspect validation and metadata, execute the notebook from a clean
  kernel, inspect changed visual artifacts, remove temporary material, and run
  `git diff --check` before recording completion.
- Record release evidence in `docs/reference/release-verification.tsv` and keep
  the central guide, examples, README, and checklist synchronized with
  production behavior.
