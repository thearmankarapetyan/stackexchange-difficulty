# Security policy

## Supported version

Security fixes are applied to the current `main` branch.

## Reporting a concern

The reporting route for this private repository is a repository issue with
`[security]` in its title. The report identifies the affected file or behavior
and includes safe reproduction steps. Credentials, tokens, private keys,
personal data, and raw dump content remain excluded.

GitHub private vulnerability reporting and the repository's private security
form become prerequisites before any public release.

## Data and credential handling

- Stack Exchange credentials are never required by the processing scripts.
- Raw public dumps and generated annual datasets stay in ignored local folders.
- Secrets belong in local environment variables or an approved secret manager.
- A committed secret must be revoked at its source and removed from Git history;
  deleting it in a later commit does not remove earlier copies.
