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
