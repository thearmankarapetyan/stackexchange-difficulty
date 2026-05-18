# Stack Exchange Difficulty Corpus Progress Note - 2026-05-18

## Current Status

The project now has a local reproducible workflow from Stack Exchange Data Dump
XML to canonical tables, derived indicators, JSONL, provenance, and aggregate
audits. The workflow has been exercised on Mathematics Stack Exchange with an
answerable-first profile and a stricter clean answerable profile.

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

## Target-Scale Inspection Finding

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

The target-scale parser run validated that the Data Dump workflow can produce a
large local answerable Mathematics sample without committing raw XML, processed
tables, comments, or JSONL threads. Its inspection result was not yet accepted:

- inspected records: `100`;
- suitable records: `yes=78, no=8, uncertain=14`;
- answerability clear: `yes=79, no=5, uncertain=16`;
- math notation readable: `yes=98, no=2, uncertain=0`;
- needs comments: `yes=1, no=96, uncertain=3`;
- recommendation: `target_scale_revise_sampling`.

The aggregate diagnostic report recommended moving to
`sample_profile=answerable_clean` for the next target-scale run.

## Sampling Revision

The `answerable_clean` profile tightened the sampling strategy using only
metadata available before sampling. It preserves the answerable profile rules
and additionally requires:

- nonnegative question score;
- nonblank tags;
- available first-answer timing;
- first-answer latency no greater than 168 hours.

It does not use question title text, question body text, answer body text,
comment text, usernames, URLs, or post history for candidate selection.

## Clean Validation Run

The 5,000-question `answerable_clean` validation run completed with:

- site: Mathematics;
- site slug: `math`;
- pilot slug: `math-answerable-clean`;
- dump date: `2026-04-20`;
- sample profile: `answerable_clean`;
- selected questions: `5000`;
- parser decision: `data_dump_parser_validated`;
- inspection labeler: `llm_assisted_xhigh`;
- inspection recommendation: `target_scale_sample_accepted`.

Aggregate clean 5,000-record inspection result:

- inspected records: `100`;
- suitable records: `yes=87, no=8, uncertain=5`;
- answerability clear: `yes=88, no=6, uncertain=6`;
- math notation readable: `yes=98, no=2, uncertain=0`;
- needs comments: `yes=2, no=98, uncertain=0`.

This result justified rerunning the target-scale sample with the clean profile.

## Clean Target-Scale Run

The 100,000-question `answerable_clean` target-scale run completed with:

- site: Mathematics;
- site slug: `math`;
- pilot slug: `math-answerable-clean-100k`;
- dump date: `2026-04-20`;
- sample profile: `answerable_clean`;
- selected questions: `100000`;
- answer rows: `168253`;
- comment rows: `546586`;
- derived indicator rows: `100000`;
- JSONL thread rows: `100000`;
- parser decision: `data_dump_parser_validated`;
- validation issue count: `0`;
- inspection labeler: `llm_assisted_xhigh`;
- inspection recommendation: `target_scale_sample_accepted`.

Aggregate clean 100,000-record inspection result:

- inspected records: `100`;
- suitable records: `yes=87, no=7, uncertain=6`;
- answerability clear: `yes=89, no=5, uncertain=6`;
- math notation readable: `yes=100, no=0, uncertain=0`;
- needs comments: `yes=5, no=95, uncertain=0`.

This is the accepted local target-scale Mathematics sample milestone.

## Inspection Decision

The clean target-scale sample met the acceptance thresholds:

- suitable yes labels are at least `80`;
- answerability-clear yes labels are at least `80`;
- notation-readable yes labels are at least `95`;
- needs-comments yes labels are at most `10`.

The current aggregate recommendation is `target_scale_sample_accepted`.

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

The clean answerable Mathematics profile excludes closed, unanswered, duplicate,
and no-accepted-answer cases. That is useful for constructing a clean
answerability baseline, but it does not yet cover hard diagnostic cases.

The accepted clean target-scale sample is local validation evidence, not a
public corpus release. Public distribution still requires attribution design,
release packaging, and a policy for what content can be redistributed.

Mathematics Stack Exchange may not generalize to all technical Stack Exchange
communities. Later work still needs cross-site design, model-evaluation
protocols, contamination controls, correctness checks, and redistribution-safe
attribution handling.

## Next Technical Step

The next technical step is to design metadata-only Hugging Face preparation for
Data Dump audits and then plan the 100,000-500,000 record production corpus
workflow.

Recommended next actions:

1. Extend metadata packaging so Data Dump audits and provenance can be prepared
   without including raw XML, processed TSVs, comments, JSONL threads, review
   files, label files, or post text.
2. Draft the production-corpus plan around the accepted
   `math-answerable-clean-100k` milestone.
3. Define attribution, licensing, redistribution, and contamination-risk
   handling before any public content release.
4. Keep API crawling, HTML scraping, and multi-site expansion out of scope until
   the metadata-only release path is implemented and tested.
