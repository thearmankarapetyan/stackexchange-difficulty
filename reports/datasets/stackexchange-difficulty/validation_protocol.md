# Validation Protocol

This protocol implements the checks described in the report before any empirical
comparison is attempted.

## Technical Checks

- Confirm expected row counts.
- Require unique `question_id` values.
- Reject Data Dump artificial post IDs `1000000001` and `1000000010`.
- Require all schema columns needed by the scaffold.
- Verify that every answer points to an existing question.
- Verify that every `accepted_answer_id` points to an existing answer for the
  same question.
- Check provenance completeness before processed outputs are accepted.
- For SEDE pilot ingestion, require the export columns listed in
  `sede_expected_columns.tsv` before writing normalized processed tables.

## Distribution Checks

- Inspect answered/unanswered balance.
- Inspect accepted/no-accepted balance.
- Inspect closure and duplicate coverage.
- Inspect tag distribution and visibility skew.
- Inspect time-to-first-answer distribution.

## Data Dump Parser Checks

The Data Dump parser is a local parser-validation milestone, not the final
large corpus run. The user downloads and extracts Stack Exchange Data Dump
archives manually. Project tooling reads the extracted XML files from ignored
`data/raw/stackexchange-difficulty/data-dump/` paths and must not download
archives, call the API, scrape HTML, upload data, or print post text.

For the v1 `answerable_pilot` profile, `Posts.xml` and `PostLinks.xml` are
required. `PostLinks.xml` is not optional because duplicate exclusion depends
on link rows with `LinkTypeId=3`. `Comments.xml` and `Tags.xml` are optional;
missing comment files produce an empty `comments.tsv`. `PostHistory.xml` is
read only when `--include-post-history` is passed, because it can be large and
its `Text` field contains raw markdown or event text that must remain separate
from rendered `Posts.Body` HTML.

Use `stackexchange-difficulty preflight-dump` before a parser run. The default
preflight output is aggregate JSON on stdout; it writes a report file only when
`--out` is provided. The preflight checks file presence, XML readability, row
counts, and raw file hashes without displaying titles, bodies, comments,
answers, formulas, usernames, or URLs.

Use `stackexchange-difficulty run-data-dump-pilot` only after preflight passes.
The parser must:

- reuse the shared `site_slug` and `pilot_slug` validation rules;
- exclude artificial post IDs `1000000001` and `1000000010`;
- reject incomplete duplicate filtering;
- reject closed, duplicate, unanswered, no-accepted-answer, missing-accepted,
  and accepted-parent-mismatch candidates for the `answerable_pilot` profile;
- stream XML row parsing with `iterparse` and clear parsed elements;
- write validation-compatible `questions.tsv`, `answers.tsv`, and
  `comments.tsv` tables under ignored `data/processed/`;
- write support tables such as `post_links.tsv`, `tags.tsv`, and optional
  `post_history.tsv` only under ignored processed paths;
- finalize processed hashes before deriving indicators and JSONL;
- produce tracked provenance and audit files that contain aggregate metadata
  only.

The Data Dump audit can be marked `data_dump_parser_validated` only when
`Posts.xml` and `PostLinks.xml` were present, the requested sample size was
reached, canonical validation passed, duplicate filtering was complete, and no
raw or processed Stack Exchange content was added to Git.

## Pilot Inspection

At least 100 records in a future real pilot must be inspected for readability,
field linking, code/error preservation, duplicate-link usefulness, and
record-level provenance.

The current SEDE pilot export path is question/answer centered and does not
include comment text. Comment context is inspected only if a separate comment
export or enrichment step is explicitly added and documented.

For a comment-enrichment pass, use the existing pilot `questions.tsv` and
`answers.tsv` as the source of allowed IDs. The generated SEDE comment query
must stay under ignored `data/processed/stackexchange-difficulty/` because it
contains real Stack Exchange post IDs. The tracked template is
`sede_comments_query_template.sql`; the ID-filled query is not a report
artifact.

When more than one pilot is run on the same Stack Exchange site, keep site and
pilot identity separate. For example, the cleaner answerable Mathematics pilot
uses `source_site_slug: math` and `pilot_slug: math-answerable`. Validation
must reject any workflow that treats `math-answerable` as the SEDE site slug.

Use `stackexchange-difficulty prepare-inspection` to create local ignored
review and label files under `data/processed/stackexchange-difficulty/`. The
review file may contain real post text and must stay untracked. Use
`stackexchange-difficulty summarize-inspection` only after labels have been
filled with controlled values by a human reviewer or LLM-assisted labeling
process; the tracked audit receives aggregate counts and the labeler method
only.

After comment enrichment, use `stackexchange-difficulty prepare-comment-reinspection`
to create a local ignored review subset for records previously labeled
`needs_comments=yes`. The reinspection files may contain comment text and must
remain untracked. Use `stackexchange-difficulty summarize-comment-reinspection`
after the comment-enriched labels are complete; only aggregate relabeling counts
and the final comment-enriched decision may be copied into an audit.

Tracked audit notes must report aggregate findings only. Do not copy question
titles, post bodies, answer text, code snippets, comments, or user profile
content into Git.
