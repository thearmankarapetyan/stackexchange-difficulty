# Security policy

## Supported version

Security fixes are applied to the current `main` branch.

## Reporting a concern

For this private repository, open a repository issue and mark the title with
`[security]`. Describe the affected file or behavior and provide safe steps to
reproduce the concern. Keep credentials, tokens, private keys, personal data,
and raw dump content out of the report.

Before any public release, enable GitHub private vulnerability reporting and
replace this reporting route with the repository's private security form.

## Data and credential handling

- Stack Exchange credentials are never required by the processing scripts.
- Raw public dumps and generated annual datasets stay in ignored local folders.
- Secrets belong in local environment variables or an approved secret manager.
- A committed secret must be revoked at its source and removed from Git history;
  deleting it in a later commit does not remove earlier copies.
