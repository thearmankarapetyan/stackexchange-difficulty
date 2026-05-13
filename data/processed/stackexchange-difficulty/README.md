# Processed Stack Exchange Difficulty Data

This directory is reserved for generated outputs derived from raw files through
documented scripts. Processed outputs must remain reproducible from preserved
raw files and provenance metadata.

Expected future outputs include:

- relational-style processed tables;
- `derived_thread_indicators.tsv`;
- thread-level `threads.jsonl`;
- validation reports and corpus audit material.

Data Dump parser runs write ignored directories such as:

```text
data/processed/stackexchange-difficulty/dump-math-answerable-YYYY-MM-DD/
data/processed/stackexchange-difficulty/dump-math-answerable-YYYY-MM-DD-derived/
```

The canonical tables remain `questions.tsv`, `answers.tsv`, and
`comments.tsv`, so existing validation and derivation commands continue to
work. Support tables such as `post_links.tsv`, `tags.tsv`, and optional
`post_history.tsv` are local parser outputs only. `Posts.Body` is preserved as
rendered HTML in `body_html`. `PostHistory.Text` is included only when
requested and remains separate from rendered post bodies.

Processed TSV files, JSONL threads, hash manifests, review files, labels, and
any real Stack Exchange text remain ignored by Git. Tracked reports should
contain aggregate counts, hashes, and decisions only.

This scaffold tracks only documentation and the data dictionary.
