# Supervisor Meeting Notes - 2026-05-19

## Purpose

These notes prepare the discussion following the methodological report and the
supervisor's request for a qualitative analysis of recent exchanges.

The immediate objective is to decide which corpus-construction choices should be
kept for the next phase, and how to use qualitative evidence alongside the
existing indicators.

## Current Technical Status

The project now has a validated local workflow for Mathematics Stack Exchange:

- source: Stack Exchange Data Dump;
- site: Mathematics;
- source slug: `math-answerable-clean-100k`;
- sample profile: `answerable_clean`;
- selected questions: `100000`;
- parser decision: `data_dump_parser_validated`;
- target-scale inspection recommendation: `target_scale_sample_accepted`.

The tracked materials remain aggregate-only. Raw XML, processed TSV files,
thread JSONL, review files, code files, and Stack Exchange post text remain
local and ignored.

## Recent Qualitative Slice

The qualitative analysis covers recent Mathematics exchanges that began between
`2025-05-01` and `2026-04-20`, using the accepted clean 100,000-question local
sample.

The qualitative sample contains `30` coded threads:

- `10` clear/direct cases;
- `10` ordinary/intermediate cases;
- `10` high-effort or ambiguous cases.

Coding was LLM-assisted with controlled categories and aggregate-only reporting.
The coding file remains local and ignored.

## Aggregate Qualitative Findings

The coded recent slice produced these aggregate results:

- qualitative difficulty: `high=16`, `medium=9`, `low=5`;
- answerability clarity: `clear=21`, `partially_clear=9`;
- comments needed: `yes=10`, `no=19`, `uncertain=1`;
- corpus-design implication: `keep_main_clean_corpus=13`,
  `include_comments=9`, `add_diagnostic_subset=8`.

The main interpretation is that the clean profile works as a main answerable
corpus layer, but recent threads still show enough high-effort and
comment-relevant cases to justify a smaller diagnostic qualitative subset.

## Proposed Position For Discussion

Recommended default choices:

1. Keep Mathematics as the first fully validated site, because the local parser,
   sampling, inspection, and qualitative workflow are now coherent.
2. Use `answerable_clean` as the main corpus profile for answerable
   Mathematics questions.
3. Add a separate diagnostic subset later for ambiguous, comment-dependent,
   high-effort, closed, unanswered, or otherwise difficult cases.
4. Keep comments optional for the main corpus, but include them in qualitative
   and diagnostic analyses when they clarify missing context.
5. Treat the current indicators as descriptive variables, not final
   easy/difficult labels.

## Choices To Resolve With Supervisor

Questions for the meeting:

1. Should the first validated corpus remain Mathematics, or should the next
   validation target return to a more code-centric site such as Stack Overflow?
2. Should the first empirical corpus focus on clean answerable cases, or include
   hard diagnostic cases from the beginning?
3. Should comments be part of the default thread representation, or only added
   for qualitative and diagnostic subsets?
4. Should the next annotation target be difficulty, answerability, or a combined
   rubric separating both?
5. Should the project prepare a metadata-only release package before expanding
   from 100,000 records toward a larger 100,000-500,000-record corpus?

## Suggested Short Explanation In French

Le pipeline local est maintenant valide sur Mathematics. Le premier grand
échantillon answerable a validé le parseur, mais son inspection qualitative a
montré que l'échantillonnage devait être resserré. Le profil
`answerable_clean` a ensuite été validé sur 5,000 puis 100,000 questions, avec
une recommandation positive.

L'analyse qualitative récente montre que les indicateurs sont utiles pour
décrire les profils de difficulté, mais qu'ils ne doivent pas encore être
traités comme des labels définitifs. Elle suggère aussi de distinguer deux
couches: un corpus principal propre et answerable, puis un sous-ensemble
diagnostique pour les cas ambigus, difficiles ou dépendants des commentaires.

## Content Safety

This note contains only aggregate counts, methodological interpretation, and
discussion points. It contains no original Stack Exchange post text, no copied
formulas, no individual record identifiers, no URLs, no usernames, and no local
review or coding content.
