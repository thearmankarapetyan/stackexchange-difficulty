# Project instructions

- Read [`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md) before planning or
  modifying this project.
- Treat that checklist as the canonical roadmap. Check an item only after
  verifying its evidence, and update its **Last reviewed** date when status
  changes.
- Preserve its thirteen independently numbered task sections. Record shared
  evidence under every applicable task instead of merging or silently dropping
  a requirement.
- Write authored documentation, code comments, command messages, notebook
  prose, and workbook labels in English. Preserve source data, XML values,
  proper names, and quoted research material in their original form.
- Keep production inputs configurable across compatible Stack Exchange sites;
  use the current verified sites as cross-site evidence and keep production
  behavior free of site-specific constants.
- Prefer simple code and concise documentation that can be understood by
  someone unfamiliar with the implementation.
- Maintain `README.md` as the single English project-documentation page. Add
  stable contents links, same-page cross-references, and glossary links so a
  reader can reach an exact answer directly. Treat linked headings as stable
  navigation targets and update every incoming link when a heading changes.
  Avoid duplicate documentation pages.
- Apply Diátaxis within the README: keep the tutorial concrete and choice-free,
  keep how-to sections focused on goals and actions, keep reference sections
  neutral and system-shaped, and reserve reasons, context, alternatives, and
  interpretation for the explanation section.
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
  the README, examples, and checklist synchronized with production behavior.
