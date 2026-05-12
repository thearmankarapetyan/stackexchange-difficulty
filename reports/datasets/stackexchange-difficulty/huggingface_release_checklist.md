# Hugging Face Release Checklist

This checklist governs the first Hugging Face dataset repository workflow for
the Stack Exchange difficulty project. The v1 release is private-first and
metadata-only.

## Scope

Allowed in the v1 release package:

- Hugging Face dataset card.
- Release manifest with SHA-256 hashes.
- Data dictionary.
- Dated pilot provenance JSON.
- Dated aggregate pilot audit.
- Validation and completion protocol documents.
- SEDE export checklist.
- Methodological report text.

Not allowed in the v1 release package:

- Raw SEDE CSV or TSV exports.
- Processed Stack Exchange post text.
- JSONL thread records.
- Question titles, bodies, code snippets, answers, comments, usernames, or user
  profile content.
- Browser downloads, partial downloads, caches, logs, or local run artifacts.
- Passwords, API tokens, Hugging Face tokens, Stack Exchange credentials, or
  university credentials.

## Preparation

1. Confirm that the dated provenance and aggregate audit exist.
2. Confirm that the audit contains aggregate results only.
3. Run:

   ```bash
   stackexchange-difficulty prepare-hf-release \
     --pilot-date YYYY-MM-DD \
     --repo-id NAMESPACE/REPO \
     --out-dir dist/huggingface/stackexchange-difficulty-YYYY-MM-DD
   ```

4. Inspect the generated `README.md` and `hf_release_manifest.json`.
5. Confirm that every manifest row has a SHA-256 hash.
6. Confirm that the release folder is under ignored `dist/`.

## Upload

Upload is dry-run by default:

```bash
stackexchange-difficulty upload-hf-release \
  --release-dir dist/huggingface/stackexchange-difficulty-YYYY-MM-DD \
  --repo-id NAMESPACE/REPO
```

Apply only after local review:

```bash
stackexchange-difficulty upload-hf-release \
  --release-dir dist/huggingface/stackexchange-difficulty-YYYY-MM-DD \
  --repo-id NAMESPACE/REPO \
  --apply
```

Authentication happens outside the project through `hf auth login` or
`HF_TOKEN`. Tokens must never be pasted into chat, code, logs, provenance,
audits, or tracked files. The applied command verifies the local account with
`hf auth whoami` before creating or uploading to the private dataset repository.

## Release Decision

The release can proceed only if:

- The repository target is explicitly provided as `--repo-id NAMESPACE/REPO`.
- The dataset repository is private.
- The package is metadata-only.
- The manifest and audit support reproducibility review.
- No real Stack Exchange post content or credentials are present.

A public or gated content-bearing release requires a separate plan covering
per-record attribution, license handling, redistribution scope, and audit
approval.
