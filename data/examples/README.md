# Verified examples

These small artifacts make each implemented route inspectable without adding
large public dump archives to version control.

## XML extraction examples

- `complete_thread_example.xml` and
  `softwareengineering_request_summary_example.xml` use Software Engineering
  question 450355:
  <https://softwareengineering.stackexchange.com/questions/450355>.
- `superuser_request_summary_example.xml` uses Super User question 1823849:
  <https://superuser.com/questions/1823849>.
- `summary_fields_compact.tsv` selects six supported summary fields.
- `configurable_request_summary_example.xml` is the output produced from that
  compact selection for question 450355.

The three default XML files were regenerated from the April 2026 public dumps
with the canonical extractors. Source attributes such as author identifiers
and content licences remain available for attribution and verification.

## Characteristic and notebook example

- `characteristics_pilot.tsv` contains the first 20 Software Engineering
  questions selected chronologically from 1–8 January 2024 by the current
  47-field builder.
- `characteristics_pilot_validation.tsv` records nine PASS checks, zero WARN,
  and zero FAIL for that pilot.

The generic notebook uses this pilot by default. The example contains real
public Stack Exchange content, source URLs, author identifiers when available,
and content-licence fields. Preserve that provenance when sharing or reusing
the content.
