# Completion Criteria

The v1 scaffold is complete when:

- `python -m pytest` passes.
- `python -m ruff check .` passes.
- CLI help works through `python -m stackexchange_difficulty --help`.
- Editable installation exposes `stackexchange-difficulty --help`.
- Fixture validation produces a passing validation report.
- Fixture derivation writes `derived_thread_indicators.tsv`, `threads.jsonl`,
  and `validation_report.json`.
- Synthetic SEDE ingestion writes normalized question, answer, comment,
  provenance, and validation outputs.
- The opt-in API smoke check exists and stores metadata only.
- No real SEDE export, Data Dump download, HTML scrape, or corpus collection is
  performed by default.
- The implementation log records executed checks and their results.
- The private GitHub repository contains the initial scaffold commit.
- GitHub Actions passes on `main`.

Future corpus work is complete only after a real pilot also satisfies the pilot
inspection and audit requirements in `validation_protocol.md`.

## First Real SEDE Pilot Gate

The first real SEDE pilot is ready for review only when:

- A raw export has been saved under `data/raw/stackexchange-difficulty/` and is
  ignored by Git.
- `stackexchange-difficulty preflight-sede` has confirmed required columns,
  the 5,000-10,000 row target, duplicate IDs, artificial-ID exclusion,
  accepted-answer consistency, and the raw export hash.
- If `stackexchange-difficulty run-sede-pilot` is used, browser login and
  Cloudflare verification remain manual and no credentials are handled by the
  project tooling.
- A dated JSON provenance file has been created from
  `provenance_sede_pilot_template.json`.
- `stackexchange-difficulty ingest-sede` has produced normalized local tables.
- `stackexchange-difficulty finalize-provenance` has replaced pending output
  hashes before derived JSONL is generated.
- `stackexchange-difficulty derive` has produced indicators and JSONL.
- The tracked audit under `audits/` contains aggregate validation results,
  processed-file hashes, and the inspection summary.
- No real Stack Exchange post content has been committed.

## Cleaner Mathematics Answerable Pilot Gate

The cleaner second Mathematics pilot is ready for inspection only when:

- `stackexchange-difficulty run-sede-pilot` is run with `--site-slug math`,
  `--site-name Mathematics`, `--pilot-slug math-answerable`, and
  `sede_pilot_query_math_answerable.sql`.
- The query returns 5,000-10,000 rows without accepting closed, duplicate,
  unanswered, or no-accepted-answer records as the main sample.
- Generated artifact names use `math-answerable`, while provenance keeps
  `source_site_slug: math` and records `pilot_slug: math-answerable`.
- The tracked audit is aggregate-only and contains no titles, bodies, answers,
  comments, code snippets, usernames, or credentials.
- A 100-record inspection or LLM-assisted inspection reaches at least 80
  suitable records, at least 80 answerability-clear records, at least 95
  notation-readable records, and at most 10 records needing comments.
- The audit decision is `ready_for_data_dump_design` before Data Dump parser
  planning begins.

## Comment-Enriched Pilot Gate

The Mathematics pilot is ready for larger design planning only when:

- `stackexchange-difficulty run-sede-comment-enrichment` has generated an
  ID-locked SEDE comment query from the existing pilot IDs.
- The rendered query, raw comment export, processed comment table, derived
  JSONL, and local reinspection files remain under ignored `data/` paths.
- Comment validation has confirmed required columns, unique `comment_id`
  values, known `question_id` values, and `post_id` links to pilot questions or
  included first/accepted answers.
- Pending provenance hashes have been finalized before comment-enriched JSONL
  is generated.
- `stackexchange-difficulty prepare-comment-reinspection` has produced a local
  ignored subset for records previously labeled `needs_comments=yes`.
- `stackexchange-difficulty summarize-comment-reinspection` has updated the
  tracked audit with aggregate comment-enriched relabeling counts only.
- The tracked audit contains aggregate comment coverage and aggregate
  reinspection counts only.
- The final decision is one of `ready_for_data_dump_design`,
  `needs_more_comment_coverage`, or `revise_sede_query`.

## Data Dump Parser Validation Gate

The local Data Dump parser milestone is complete only when:

- The cleaner `math-answerable` SEDE pilot audit has already reached
  `ready_for_data_dump_design`.
- Extracted Data Dump XML files are provided manually under ignored
  `data/raw/stackexchange-difficulty/data-dump/` paths.
- The project does not download archives, extract `.7z` files, call the API,
  scrape HTML, upload content, or print Stack Exchange post text.
- `stackexchange-difficulty preflight-dump` confirms XML file presence,
  readability, row counts, raw hashes, and the required `PostLinks.xml` file
  for `sample_profile=answerable_pilot`.
- `stackexchange-difficulty run-data-dump-pilot` fails instead of overwriting
  existing processed directories, derived directories, provenance files, or
  audits.
- `questions.tsv`, `answers.tsv`, and `comments.tsv` remain compatible with the
  existing canonical validation checks.
- `PostLinks.xml` duplicate filtering is complete; a parser audit cannot be
  marked validated without it.
- `PostHistory.xml` is ignored by default and included only when
  `--include-post-history` is passed.
- Processed hash manifests are finalized before derived indicators and
  `threads.jsonl` are produced.
- Generated tracked provenance and audit files contain aggregate metadata,
  hashes, and decisions only.
- Raw XML, processed TSVs, JSONL threads, comments, post history, review files,
  labels, and any copied Stack Exchange content remain ignored and uncommitted.
- A synthetic fixture run can produce `data_dump_parser_validated`.
- Local tests, Ruff, CLI help checks, and GitHub Actions pass.

## Hugging Face Metadata Release Gate

A private Hugging Face metadata release is ready only when:

- A dated pilot provenance JSON file exists under
  `reports/datasets/stackexchange-difficulty/`.
- A dated aggregate pilot audit exists under
  `reports/datasets/stackexchange-difficulty/audits/`.
- `stackexchange-difficulty prepare-hf-release` creates a release folder under
  ignored `dist/` with a dataset card, manifest, data dictionary, protocol docs,
  provenance, audit, and methodology report.
- The generated manifest includes SHA-256 hashes for every staged file.
- The staged files contain no credential-like markers.
- The staged files do not include raw SEDE exports, processed Stack Exchange
  post text, JSONL thread records, comments, usernames, browser downloads, or
  local raw/processed data outputs.
- `stackexchange-difficulty upload-hf-release` is reviewed in dry-run mode
  before any `--apply` upload.
- Any applied upload uses `hf auth whoami` and a private dataset repository.
