# Stack Exchange human–model difficulty

This is the clean, canonical directory for the current internship work.

The project studies signals of question difficulty in Stack Exchange threads and prepares a paired comparison with generative-model outcomes. The current data sources are the April 2026 public dumps for Super User and Software Engineering.

## Project roadmap

Read [`PROJECT_CHECKLIST.md`](PROJECT_CHECKLIST.md) before planning or changing
the project. It records the verified baseline, eight deliverable-focused
tasks, acceptance criteria, and the repeatable quality gate.

The canonical overview flowchart and one central English project guide are
being finalized under Tasks 1 and 2. Existing workflow spreadsheets, HTML,
images, and Word documents remain reference material until the verified
canonical source and publication export replace them.

## Current workflow

1. `src/extract_threads.py` reconstructs complete requested threads in XML.
2. `src/extract_request_summary.py` produces the twelve-field XML requested by the supervisors.
3. `src/build_characteristics.py` creates one verified question-level TSV from a site dump.
4. `notebooks/stackexchange_eda.ipynb` provides one generic exploratory analysis for either site.
5. `config/characteristics.tsv` is the versioned specification for every output column.

The three command-line tools share only the small XML rules in
`src/stackexchange_xml.py`: streaming, date validation, chronological ordering,
and safe XML writing. The 47 transparent field calculations are grouped in
`src/question_characteristics.py` so they can be compared directly with the
data dictionary.

## Documentation

The current documentation folders follow Diátaxis:

- `docs/tutorials/`: guided learning sessions;
- `docs/how-to/`: instructions for a specific task;
- `docs/reference/`: exact field, command, and file descriptions;
- `docs/explanation/`: research choices, context, and limitations.

Use this README and `PROJECT_CHECKLIST.md` as the current English entry points.
The useful content of the existing French DOCX files will be consolidated into
`docs/stackexchange-project-guide.docx`; until that guide is verified, those
files remain source material for consolidation into the verified guide.

The recovery audit is in `docs/explanation/project-recovery-audit.docx`. The
scientific review is
`docs/explanation/state-of-the-art-qpp-ppp-rag.pdf`. The
formatted data dictionary is `docs/reference/data-dictionary.xlsx`; its
version-controlled source is `config/characteristics.tsv`. Published network
and tag statistics are in
`docs/reference/stackexchange-published-statistics.xlsx`.

## Data

Large XML dumps and regenerated outputs stay outside version control. The command-line tools use explicit input and output paths, so the project does not depend on one computer or one personal directory.

The current comparable analysis period is 1 January–31 December 2024. Both
tables use the April 2026 dump snapshot, which gives every selected question at
least fifteen months of possible follow-up.
