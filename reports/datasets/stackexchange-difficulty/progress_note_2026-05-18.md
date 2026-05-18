# Stack Exchange Difficulty Corpus Progress Note - 2026-05-18

## Current Status

The project now has a local reproducible workflow from Stack Exchange Data Dump
XML to canonical tables, derived indicators, JSONL, provenance, and aggregate
audits. The workflow has been exercised on Mathematics Stack Exchange with an
answerable-first profile.

This is still a local validation milestone. It is not a public corpus release,
and no raw or processed Stack Exchange content has been committed.

## Validated Workflow

The current methodology keeps the access methods separated by role:

- SEDE was used for pilot design and query validation.
- The public Stack Exchange Data Dump is the large-corpus source.
- The Stack Exchange API remains enrichment-only.
- HTML scraping remains excluded.

The Data Dump parser reads manually extracted XML files from ignored
`data/raw/` paths, normalizes selected records into ignored `data/processed/`
outputs, derives indicators and JSONL locally, and writes only aggregate
provenance and audit material to tracked reports.

## Mathematics SEDE Pilot

The answerable Mathematics SEDE pilot provided the first clean site-specific
pilot evidence. Its inspection result justified moving from SEDE pilot design
to Data Dump parser validation.

The pilot remains useful as historical evidence, but it is not the target
corpus. It established the answerable-first sampling direction and the need to
keep site identity, pilot identity, provenance, and aggregate audit material
separate.

## Data Dump Parser Validation

The 5,000-question Mathematics Data Dump parser validation passed with decision
`data_dump_parser_validated`.

Important validated parser properties:

- `Posts.xml` and `PostLinks.xml` are required for the answerable profile.
- `PostLinks.xml` is used for duplicate filtering.
- Artificial post IDs `1000000001` and `1000000010` are excluded.
- Closed, unanswered, no-accepted-answer, missing accepted-answer, and
  accepted-answer-parent-mismatch cases are excluded from the answerable
  profile.
- `PostHistory.xml` is excluded by default.
- Canonical validation checks pass before derived outputs are accepted.

## Target-Scale Local Sample

A 100,000-question local Mathematics Data Dump sample was generated with:

- site: Mathematics;
- site slug: `math`;
- pilot slug: `math-answerable-100k`;
- dump date: `2026-04-20`;
- sample profile: `answerable_pilot`;
- selected questions: `100000`;
- answer rows: `161112`;
- comment rows: `534698`;
- derived indicator rows: `100000`;
- JSONL thread rows: `100000`;
- parser decision: `data_dump_parser_validated`.

The target-scale parser run validates that the Data Dump workflow can produce a
large local answerable Mathematics sample without committing raw XML, processed
tables, comments, or JSONL threads.

## Inspection Result

A 100-record LLM-assisted inspection sample was prepared from the 100,000-record
local sample. The row-level review and label files remain ignored under
`data/processed/`.

Aggregate inspection result:

- inspected records: `100`;
- suitable records: `yes=78, no=8, uncertain=14`;
- answerability clear: `yes=79, no=5, uncertain=16`;
- math notation readable: `yes=98, no=2, uncertain=0`;
- needs comments: `yes=1, no=96, uncertain=3`;
- recommendation: `target_scale_revise_sampling`.

The parser-scale milestone is valid, but the 100,000-record answerable sample is
not yet accepted as a target-scale sample. Suitability and answerability-clear
counts were just below the threshold of 80 yes labels each.

## Content Safety

Tracked files contain aggregate counts, hashes, provenance, and decisions only.

The following remain local and ignored:

- raw XML files;
- processed question, answer, comment, link, and tag TSV files;
- derived JSONL threads;
- inspection review files;
- inspection label files;
- LLM batch files.

No question titles, question bodies, answer text, comment text, copied formulas,
usernames, individual record URLs, credentials, or raw Stack Exchange post
content are included in this progress note.

## Licensing And Provenance

Licensing and attribution are tracked through provenance and source fields,
including Stack Exchange source method, site identity, dump date, file hashes,
transformation steps, and `ContentLicense` fields in local canonical outputs.

Public redistribution of Stack Exchange post text still requires a separate
attribution and release design. Hugging Face upload remains metadata-only until
that design is implemented and tested.

## Remaining Risks

The current answerable-first Mathematics profile excludes closed, unanswered,
duplicate, and no-accepted-answer cases. That is useful for constructing a clean
answerability baseline, but it does not yet cover hard diagnostic cases.

The target-scale inspection showed that a larger sample can contain more
unsuitable or unclear records than the smaller pilot. The next work should
therefore revise sampling or filtering before public release planning.

Mathematics Stack Exchange may not generalize to all technical Stack Exchange
communities. Later work still needs cross-site design, model-evaluation
protocols, contamination controls, correctness checks, and redistribution-safe
attribution handling.

## Next Technical Step

The next technical step is to revise the target-scale sampling strategy before
preparing a public or Hugging Face release.

Recommended next actions:

1. Inspect aggregate strata from the 100-record target-scale sample to identify
   where unsuitable and unclear cases concentrate.
2. Adjust the answerable Data Dump sampling profile or create a stricter
   `math-answerable-clean` profile.
3. Rerun a smaller validation sample first, then rerun the 100,000-question
   target-scale sample.
4. Repeat the 100-record aggregate inspection.
5. Proceed to metadata-release planning only after the recommendation becomes
   `target_scale_sample_accepted`.
