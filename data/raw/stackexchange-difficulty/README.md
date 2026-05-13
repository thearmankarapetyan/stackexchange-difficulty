# Raw Stack Exchange Difficulty Data

This directory is reserved for unedited source exports. Raw files must not be
manually changed after download or export.

Allowed future inputs include:

- SEDE pilot exports for schema and sampling validation.
- Public Stack Exchange Data Dump XML files that have been manually downloaded
  and manually extracted outside the project tooling.
- Opt-in API enrichment metadata or responses when explicitly justified.

For Data Dump parser validation, use a local ignored layout such as:

```text
data/raw/stackexchange-difficulty/data-dump/math-YYYY-MM-DD/
```

For the v1 `answerable_pilot` profile, that directory must include
`Posts.xml` and `PostLinks.xml`. `Comments.xml` and `Tags.xml` are optional.
`PostHistory.xml` is optional and is read only when the parser is invoked with
`--include-post-history`.

The project does not download dump archives, extract `.7z` files, call the API,
or scrape pages for this workflow. Raw XML files must stay ignored by Git.

This scaffold does not include real Stack Exchange content.
