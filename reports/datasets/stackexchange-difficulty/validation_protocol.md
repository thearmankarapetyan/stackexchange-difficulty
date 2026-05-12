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

## Distribution Checks

- Inspect answered/unanswered balance.
- Inspect accepted/no-accepted balance.
- Inspect closure and duplicate coverage.
- Inspect tag distribution and visibility skew.
- Inspect time-to-first-answer distribution.

## Manual Inspection

At least 100 records in a future real pilot must be inspected for readability,
field linking, code/error preservation, duplicate-link usefulness, comment
context, and record-level provenance.

