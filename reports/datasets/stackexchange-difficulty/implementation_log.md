# Implementation Log

## 2026-05-12

Planned implementation scope:

- Create the local repository scaffold under `projects/stackexchange-difficulty/`.
- Copy the Stack Exchange methodological report, generated PDF, and SOTA PDF.
- Add schema constants, validation functions, derived indicators, JSONL export,
  provenance helpers, CLI commands, and an opt-in API smoke check.
- Add synthetic fixtures and tests.
- Run unit tests, lint, CLI help, fixture validation, and fixture derivation.
- Initialize a local Git repository, commit the scaffold, create the private
  GitHub repository, and push `main`.

Verification results:

- `python -m pytest` was not runnable in this shell because `python` is not on
  `PATH`.
- `/home/stage/venvs/stage/bin/python -m pytest`: passed, 13 tests.
- `/home/stage/venvs/stage/bin/python -m ruff check .`: passed.
- `PYTHONPATH=src /home/stage/venvs/stage/bin/python -m stackexchange_difficulty --help`:
  passed.
- Fixture validation command: passed and wrote `/tmp/stackexchange-validation.json`.
- Fixture derivation command: passed and wrote
  `/tmp/stackexchange-derived/derived_thread_indicators.tsv`,
  `/tmp/stackexchange-derived/threads.jsonl`, and
  `/tmp/stackexchange-derived/validation_report.json`.
- API smoke without `--live`: refused network access and wrote no output file.
- Git was initialized inside `projects/stackexchange-difficulty/` with branch
  `main`.
- Root commit created with message
  `Implement Stack Exchange corpus scaffold`.
- Private GitHub repository created at
  `https://github.com/thearmankarapetyan/stackexchange-difficulty`.
- `main` pushed to `origin` with the initial scaffold commit.

No live API smoke check, SEDE export, Data Dump download, HTML scraping, or real
corpus collection was run during scaffold implementation.

## 2026-05-12 Next-step hardening

Implemented reproducibility hardening before any real SEDE export:

- Added GitHub Actions CI for Python 3.12 with package installation, tests,
  Ruff, and console-script help.
- Added editable-install documentation and verified
  `stackexchange-difficulty --help` from a clean virtual environment.
- Added a documented SEDE pilot query template, expected-column file, and export
  checklist.
- Added `ingest-sede` for local SEDE CSV/TSV normalization into canonical
  question, answer, comment, provenance, and validation outputs.
- Added synthetic SEDE-shaped fixtures only; no real Stack Exchange content was
  committed.

Verification results:

- `python -m pytest`: passed, 18 tests.
- `python -m ruff check .`: passed.
- `stackexchange-difficulty --help` after editable install: passed.
- Installed-script fixture validation: passed and wrote
  `/tmp/stackexchange-validation.json`.
- Installed-script fixture derivation: passed and wrote
  `/tmp/stackexchange-derived/derived_thread_indicators.tsv`,
  `/tmp/stackexchange-derived/threads.jsonl`, and
  `/tmp/stackexchange-derived/validation_report.json`.
- Installed-script synthetic SEDE ingestion: passed and wrote normalized
  outputs under `/tmp/stackexchange-sede-ingest`.
- API smoke without `--live`: refused network access and wrote no output file.

No live API smoke check, SEDE export, Data Dump download, HTML scraping, or real
corpus collection was run during this hardening step.

## 2026-05-12 Corrected pilot-plan implementation

Implemented the corrected next-step safeguards without running a real SEDE
export:

- Kept the existing `v0.1.0-scaffold` baseline unchanged; no new tag was
  created.
- Fixed the lightweight YAML provenance loader so the repository template can
  parse block-style lists and one-level nested mappings.
- Added a JSON provenance template for the first real SEDE pilot to avoid
  relying on YAML during the pilot run.
- Added tracked pilot-audit templates that require aggregate findings only and
  forbid committing question titles, post bodies, answer text, code snippets,
  comments, or user profile content.
- Updated the SEDE export checklist to cover raw hashing, `DECLARE` fallback,
  row-count gating, explicit derivation after ingestion, and the current absence
  of comment text from the pilot export path.

Verification results:

- `python -m pip install -e .` was not runnable in this shell because `python`
  is not on `PATH`.
- `/home/stage/venvs/stage/bin/python -m pip install -e .`: passed.
- `/home/stage/venvs/stage/bin/python -m pytest`: passed, 20 tests.
- `/home/stage/venvs/stage/bin/python -m ruff check .`: passed.
- `/home/stage/venvs/stage/bin/stackexchange-difficulty --help`: passed.
- `/home/stage/venvs/stage/bin/stackexchange-difficulty ingest-sede --help`:
  passed.
- Installed-script synthetic SEDE ingestion followed by installed-script
  derivation: passed, producing two synthetic JSONL threads under `/tmp`.
- `git check-ignore` confirmed dated raw pilot exports and processed pilot
  tables remain ignored by Git.

No live API smoke check, SEDE export, Data Dump download, HTML scraping, or real
corpus collection was run during this corrected-plan implementation.

## 2026-05-12 Safer SEDE pilot preflight implementation

Implemented the safer preflight workflow without running a real SEDE export:

- Added `stackexchange-difficulty preflight-sede` to hash a local SEDE export,
  validate expected export columns, and enforce the 5,000-10,000 pilot row-count
  gate through the project reader rather than `wc -l`.
- Added `stackexchange-difficulty finalize-provenance` to replace pending
  `processed_output_hash` and `output_hash` values from a processed hash
  manifest before derived JSONL is generated.
- Updated pilot documentation to activate `~/venvs/stage`, keep the real export
  suffix from SEDE, use date-derived paths, and avoid committing raw or
  processed Stack Exchange content.
- Extended the SEDE pilot audit and provenance templates to track preflight,
  finalized provenance, and source-documentation check dates.

Verification results:

- `source ~/venvs/stage/bin/activate && python -m pytest`: passed, 23 tests.
- `source ~/venvs/stage/bin/activate && python -m ruff check .`: passed.
- `source ~/venvs/stage/bin/activate && stackexchange-difficulty --help`:
  passed.
- Installed-script synthetic SEDE preflight with custom row bounds: passed and
  wrote a SHA-256 manifest under `/tmp`.
- Installed-script provenance finalization: passed and replaced pending output
  hashes in a temporary provenance file.
- `git check-ignore` confirmed the date-derived raw export, processed question
  table, and derived JSONL paths remain ignored by Git.

No live API smoke check, SEDE export, Data Dump download, HTML scraping, or real
corpus collection was run during this implementation because no real local SEDE
export was present.

## 2026-05-12 Browser-assisted SEDE pilot automation implementation

Implemented safe automation for the non-API SEDE pilot path without handling
credentials or bypassing browser verification:

- Added `stackexchange-difficulty run-sede-pilot` with two paths: an
  already-downloaded `--export` path and a browser-assisted `--open-browser`
  path that watches for a new CSV/TSV export.
- Kept login, Cloudflare verification, query execution, and export confirmation
  as manual browser actions; credentials must never be pasted, stored, scripted,
  logged, or committed in this project.
- Added local raw-copy, hashing, preflight, dated JSON provenance creation,
  ingestion, processed-hash finalization before derivation, JSONL derivation,
  derived hash writing, and aggregate audit generation.
- Strengthened SEDE export validation so preflight catches duplicate question
  IDs, artificial post IDs, and accepted-answer consistency failures before
  processed outputs are accepted.
- Added tests for download detection, partial downloads, unsupported suffixes,
  mocked browser opening, synthetic full-pipeline execution, finalized
  provenance inside JSONL, and Git ignore protection for real-data paths.

Verification results:

- `source ~/venvs/stage/bin/activate && python -m pytest`: passed, 34 tests.
- `source ~/venvs/stage/bin/activate && python -m ruff check .`: passed.
- `source ~/venvs/stage/bin/activate && stackexchange-difficulty --help`:
  passed.
- `source ~/venvs/stage/bin/activate && stackexchange-difficulty run-sede-pilot --help`:
  passed.
- Installed-script synthetic `run-sede-pilot --export` with custom row bounds:
  passed in a temporary project root and wrote raw, processed, derived,
  provenance, and aggregate audit outputs outside the repository.
- `git check-ignore` confirmed the dated raw export, processed question table,
  derived JSONL, and browser partial-download paths remain ignored by Git.

No live SEDE export, API crawl, Data Dump download, HTML scraping, credential
use, or real corpus collection was run during this implementation.

## 2026-05-12 Hugging Face metadata-release implementation

Implemented a private-first, metadata-only Hugging Face release layer without
uploading any data:

- Added `stackexchange-difficulty prepare-hf-release` to stage a local release
  folder under ignored `dist/` from safe project metadata only.
- Added `stackexchange-difficulty upload-hf-release` with dry-run output by
  default and opt-in `--apply` execution through the `hf` CLI.
- Added release safety checks for missing dated audit/provenance files, raw or
  processed data paths, and credential-like markers.
- Added a generated Hugging Face dataset card, release manifest, and license
  and attribution notes.
- Added `huggingface_release_checklist.md` documenting private repository use,
  authentication boundaries, and the ban on real post-text upload in v1.
- Added tests for release packaging, manifest hashes, dry-run upload behavior,
  missing `hf`, failed `hf auth whoami`, mocked apply-mode CLI calls, ignored
  `dist/` paths, and credential-marker rejection.

Verification results:

- `source ~/venvs/stage/bin/activate && python -m pytest`: passed, 43 tests.
- `source ~/venvs/stage/bin/activate && python -m ruff check .`: passed.
- `source ~/venvs/stage/bin/activate && stackexchange-difficulty --help`:
  passed.
- `source ~/venvs/stage/bin/activate && stackexchange-difficulty prepare-hf-release --help`:
  passed.
- `source ~/venvs/stage/bin/activate && stackexchange-difficulty upload-hf-release --help`:
  passed.
- `git check-ignore dist/huggingface/stackexchange-difficulty-2026-05-12/README.md`:
  passed.
- Credential scan for the previously exposed password, university email, and
  Hugging Face token patterns found no real leaked credentials in the project;
  the only password-like match was a synthetic test string used to verify the
  release safety gate.

No Hugging Face upload, live API smoke check, SEDE export, Data Dump download,
HTML scraping, credential use, or real corpus collection was run during this
implementation.

## 2026-05-12 Tooling checkpoint before first pilot

Prepared the current SEDE pilot automation and Hugging Face metadata-release
tooling for publication to `main`:

- Extended GitHub Actions to verify `run-sede-pilot`, `prepare-hf-release`, and
  `upload-hf-release` help output in addition to tests, Ruff, and base CLI help.
- Confirmed the implementation includes current tracked edits and untracked
  feature files for SEDE browser-assisted automation and metadata-only HF
  release packaging.
- Adjusted the credential-marker test fixture so the project safety scanner is
  still tested without matching the known leaked credential patterns.

Verification results:

- `source ~/venvs/stage/bin/activate && python -m pytest`: passed, 43 tests.
- `source ~/venvs/stage/bin/activate && python -m ruff check .`: passed.
- `stackexchange-difficulty --help`: passed.
- `stackexchange-difficulty run-sede-pilot --help`: passed.
- `stackexchange-difficulty prepare-hf-release --help`: passed.
- `stackexchange-difficulty upload-hf-release --help`: passed.
- `git diff --check`: passed.
- `git check-ignore dist/huggingface/stackexchange-difficulty-2026-05-12/README.md`:
  passed.
- Known-leak credential scan found no matches.

## 2026-05-12 Clipboard fallback fix

Fixed the `run-sede-pilot --open-browser` clipboard preparation path after the
Stage environment reported:

```text
Clipboard copy unavailable. Paste the query from: /home/stage/Stage/projects/stackexchange-difficulty/reports/datasets/stackexchange-difficulty/sede_pilot_query.sql
```

Cause:

- The implementation only tried external clipboard utilities such as
  `wl-copy`, `xclip`, `xsel`, and `pbcopy`.
- Those utilities were not installed in the Stage environment.
- Python/Tk clipboard access worked with the available `DISPLAY`.

Fix:

- Kept external clipboard utilities as the first path.
- Added `clip.exe` support for WSL-style environments.
- Added Python/Tk clipboard fallback.
- Added OSC52 terminal fallback when stderr is a real terminal and `TERM` is not
  `dumb`.
- Added tests for Tk fallback routing and OSC52 escape generation.

## 2026-05-12 Clipboard verification and browser-helper fix

Fixed a second clipboard problem where `run-sede-pilot` reported successful
copying, but the query was not available in the user's paste buffer.

Cause:

- The Python/Tk fallback can accept clipboard text and return success even when
  no clipboard manager persists the selection after the process exits.
- A separate Python process could not read back the value, which matched the
  user's observed paste failure.

Fix:

- Python/Tk clipboard copying now succeeds only if a separate process can read
  the same clipboard value back.
- If terminal clipboard copying is unavailable, `run-sede-pilot --open-browser`
  writes an ignored local browser helper page under `reports/run-logs/` and
  opens it before the SEDE editor.
- The helper page contains the SQL in a textarea plus a browser-local copy
  button using `navigator.clipboard.writeText` with `document.execCommand`
  fallback.
- Added tests for helper-page creation, helper opening, HTML escaping, and
  cross-process Tk verification failure.
- Converted missing download directories from raw `FileNotFoundError` into a
  clear `SedePilotError`.

## 2026-05-12 Manual query-location workflow

Simplified the `run-sede-pilot --open-browser` setup after user feedback that
automatic clipboard behavior was not needed.

Changes:

- Removed automatic clipboard copying from the browser-assisted SEDE path.
- Removed the browser helper page generation from that path.
- Kept the SEDE page opening behavior.
- The command now prints the exact local query-file location and tells the user
  to paste the SQL from that file into the SEDE editor manually.

## 2026-05-12 SEDE timeout query correction

Reworked the committed SEDE pilot query after SEDE timed out before returning
even a small final result set.

Cause:

- The previous query ranked the full Stack Overflow question table and joined
  first/accepted answer bodies before the final output limit.
- Changing only the final `SELECT TOP` did not reduce the expensive upstream
  work, so SEDE still timed out.

Fix:

- The query now first limits to a bounded seed set of recent question IDs.
- It ranks only that bounded seed set.
- It joins first-answer and accepted-answer bodies only after selecting the
  pilot rows.
- Removed the `@RowsPerStratum` parameter path because it encouraged changing
  the final row count without reducing the expensive ranking step.
- Added static tests to prevent reintroducing the full-table ranking pattern
  and to verify the expected export columns remain present.

## 2026-05-12 First SEDE pilot run

Ran the first Stack Overflow SEDE pilot through the local `run-sede-pilot`
pipeline after the corrected query returned 5,000 rows in SEDE.

Results:

- Raw export copied to the ignored raw-data path.
- Raw export hash recorded in the dated provenance file.
- Preflight accepted the export columns and row count.
- Normalized outputs were written under ignored processed-data paths.
- Derived indicators and JSONL were generated under ignored processed-data
  paths.
- The tracked aggregate audit reports 5,000 question rows, 3,551 answer rows,
  zero duplicate-question failures, zero artificial-ID failures, zero
  accepted-answer consistency failures, and zero missing-column failures.
- The audit records aggregate tag-family, tag-popularity, and time-period
  distributions without including post content.
- Comment rows are absent in this pilot because the current SEDE export is
  question/answer centered.
- Manual inspection of at least 100 local records remains required before using
  the pilot as a larger Data Dump planning decision.

Content-safety note:

- No raw Stack Exchange titles, bodies, answers, comments, code snippets,
  usernames, or credentials were copied into the tracked audit.
- The generated audit and provenance use repository-relative paths.

## 2026-05-13 Site-aware SEDE pilot workflow

Implemented the site-aware path needed for non-Stack Overflow pilots such as
Mathematics while preserving the historical Stack Overflow filenames when no
site slug is passed.

Changes:

- Added `--site-slug`, `--site-name`, and `--query-file` to
  `run-sede-pilot`.
- Derived the SEDE query URL from `--site-slug` when `--query-url` is not
  provided, for example `https://data.stackexchange.com/math/query/new`.
- Added site-specific raw, processed, derived, provenance, and audit naming for
  site-selected pilots.
- Added site/query metadata to generated provenance and audits.
- Added slug validation so spaces, slashes, dots, and path traversal are
  rejected before paths are constructed.
- Extended `prepare-hf-release --site-slug` so metadata packages can find
  site-specific provenance and audit files.
- Updated the SEDE export checklist to prefer
  `sede_pilot_query_site_generic.sql` for site-selected pilots and to keep
  Stack Overflow filter queries as optional experiments.

Verification:

- `python -m pytest` passed with 58 tests.
- `python -m ruff check .` passed.
- `stackexchange-difficulty --help`,
  `stackexchange-difficulty run-sede-pilot --help`, and
  `stackexchange-difficulty prepare-hf-release --help` passed.
- `git diff --check` passed.
- `git check-ignore` confirmed the Mathematics raw export, processed question
  table, and derived JSONL paths are ignored.

## 2026-05-13 Project-root autodetection fix

Fixed the browser-assisted command when launched from the Stage workspace root
instead of the project repository.

Cause:

- `run-sede-pilot` resolved relative query paths against the current working
  directory.
- Running from `~/Stage` therefore looked for
  `reports/datasets/stackexchange-difficulty/sede_pilot_query_site_generic.sql`
  outside the project repository.

Fix:

- Added default project-root autodetection for CLI commands that need repository
  files.
- The resolver now checks the current directory, then
  `projects/stackexchange-difficulty`, then the editable package source root.
- Added a regression test that runs the CLI from a workspace root containing a
  `projects/stackexchange-difficulty` project.

Verification:

- `python -m pytest` passed with 59 tests.
- `python -m ruff check .` passed.
- From `/home/stage/Stage`, `resolve_project_root()` returned
  `/home/stage/Stage/projects/stackexchange-difficulty`.

## 2026-05-13 Mathematics SEDE pilot run

Processed the Mathematics SEDE pilot export downloaded by the browser under
`/home/stage/Téléchargements/QueryResults (1).csv`.

Results:

- Raw export copied to the ignored raw-data path as
  `data/raw/stackexchange-difficulty/sede-pilot-math-2026-05-13.csv`.
- Dated provenance written to
  `reports/datasets/stackexchange-difficulty/provenance_sede_pilot_math_2026-05-13.json`.
- Aggregate audit written to
  `reports/datasets/stackexchange-difficulty/audits/sede_pilot_math_2026-05-13.md`.
- Preflight accepted 5,000 Mathematics rows.
- Normalized outputs contain 5,000 question rows, 3,386 answer rows, and 0
  comment rows.
- Validation found zero duplicate-question failures, zero artificial-ID
  failures, zero accepted-answer consistency failures, zero missing-column
  failures, and zero provenance failures.
- Derived indicators and JSONL were generated under ignored processed-data
  paths.

Content-safety note:

- The tracked audit contains aggregate counts and distributions only.
- Raw export, processed TSV files, derived JSONL, and hash manifests under
  `data/` remain ignored by Git.
- Comment usefulness remains deferred because this SEDE export path does not
  include comment text.

## 2026-05-13 Safe Mathematics inspection tooling

Implemented the content-safe inspection workflow for the Mathematics
pilot:

- Compacted future audit tag-family distributions to the top 25 values plus an
  `other` count.
- Updated the tracked Mathematics audit to use the compact tag-family summary.
- Added `stackexchange-difficulty prepare-inspection` to write local ignored
  `review.tsv`, `labels.tsv`, and `README.md` files under
  `data/processed/stackexchange-difficulty/`.
- Added deterministic stratified sampling across answer, accepted-answer,
  closure, duplicate, latency, and tag-popularity signals.
- Added `stackexchange-difficulty summarize-inspection` to update tracked
  audits with aggregate inspection counts only.
- Kept per-record review material and labels out of Git; the CLI prints only
  paths, counts, and JSON status.

Verification results:

- `source ~/venvs/stage/bin/activate && python -m pytest`: passed, 67 tests.
- `source ~/venvs/stage/bin/activate && python -m ruff check .`: passed.
- `stackexchange-difficulty --help`: passed.
- `stackexchange-difficulty prepare-inspection --help`: passed.
- `stackexchange-difficulty summarize-inspection --help`: passed.
- `git diff --check`: passed.
- `stackexchange-difficulty prepare-inspection` created a 100-record local
  Mathematics inspection sample under the ignored processed-data directory.
- `git check-ignore` confirmed the Mathematics `review.tsv` and `labels.tsv`
  inspection files are ignored by Git.
- Known-leak credential scan found no matches.

## 2026-05-13 LLM-assisted Mathematics inspection

Completed the 100-record Mathematics pilot inspection through LLM-assisted
batch labeling:

- Split the ignored local `review.tsv` sample into five 20-record batches.
- Each batch returned only controlled labels: suitability, answerability,
  notation readability, comment need, and reason code.
- Wrote the labels to the ignored local `labels.tsv` file under
  `data/processed/stackexchange-difficulty/pilot-math-2026-05-13-inspection/`.
- Ran `stackexchange-difficulty summarize-inspection --labeler llm_assisted`.
- Updated the tracked audit with aggregate counts only: 61 suitable, 22
  unsuitable, 17 uncertain; 70 answerability-clear; 100 notation-readable; 21
  needing comments.
- The aggregate recommendation is `needs_comment_enrichment`.

Content-safety note:

- No titles, bodies, answers, URLs, formulas, usernames, comments, or copied
  post content were added to tracked files.
- The row-level review and label files remain ignored by Git.
