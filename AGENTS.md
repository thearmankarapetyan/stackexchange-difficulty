# Project requirements

- [`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md) is consulted before project
  planning or modification.
- The checklist is the canonical roadmap. Completion status changes only after
  evidence verification, and each status change updates the **Last reviewed**
  date.
- Its thirteen independently numbered task sections remain present. Shared
  evidence is recorded under every applicable task without merging or omitting
  a requirement.
- Authored documentation, code comments, command messages, notebook prose, and
  workbook labels remain in English. Source data, XML values, proper names, and
  quoted research material retain their original form.
- Production inputs remain configurable across compatible Stack Exchange
  sites. Current verified sites provide cross-site evidence, while production
  behavior remains free of site-specific constants.
- Code and documentation remain simple, concise, and comprehensible without
  implementation familiarity.
- Independent comprehension is an acceptance condition. Terms are defined
  before use, routine run values are identified, concrete examples are
  included, and links target the exact relevant heading.
- Authored project prose uses an impersonal, descriptive tone. Second-person
  address, first-person project references, conversational prompts, and
  direct imperatives are excluded. Procedures retain exact actions
  through declarative or passive constructions.
- `README.md` remains the single English project-documentation page. Stable
  contents links, same-page cross-references, and glossary links provide direct
  navigation. Linked headings are stable targets, and heading changes include
  updates to every incoming link. Duplicate documentation pages remain absent.
- Folder-level README files remain short orientations with direct links to the
  canonical root README.
- Diátaxis remains visible within the README: the tutorial is concrete and
  choice-free, how-to sections focus on goals and actions, reference sections
  remain neutral and system-shaped, and the explanation section contains
  reasons, context, alternatives, and interpretation.
- One canonical editable overview flowchart and one publication export remain
  maintained. Superseded workflow variants are archived after verification.
- Default summary behavior remains in `config/summary_fields.tsv`. Run-specific
  summary outputs use a copied field-selection TSV.
- `config/characteristic_catalogue.tsv` remains the complete research
  catalogue. `config/characteristics.tsv` remains its implemented
  question-level output subset. Field changes keep both TSV files, the pilot,
  the generated data-dictionary workbook, the notebook, and README synchronized.
- One generic, self-contained EDA notebook remains canonical. Site-specific
  notebook copies, notebook generators, and large plotting-helper modules
  remain excluded.
- Raw dumps remain unmodified. Superseded project material is archived
  non-destructively, with its checksum recorded before canonical-copy removal.
- A small controlled run precedes a full-period run. Completion evidence
  includes compilation, validation and metadata inspection, clean-kernel
  notebook execution, visual-artifact inspection, temporary-material removal,
  and `git diff --check`.
- Release evidence remains in `docs/reference/release-verification.tsv`.
  README, example, and checklist content remains synchronized with production
  behavior.
