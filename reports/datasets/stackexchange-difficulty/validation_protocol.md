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
