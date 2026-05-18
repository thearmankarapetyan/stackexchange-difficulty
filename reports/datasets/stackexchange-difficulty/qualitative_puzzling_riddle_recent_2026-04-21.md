# Qualitative Analysis Of Recent Puzzling/Riddle Threads - 2026-04-21

## Objective

This memo summarizes a recent Puzzling Stack Exchange slice for natural-language problem-solving, riddle, wordplay, and lateral-reasoning difficulty analysis.

## Source And Sample

- Site slug: `puzzling`.
- Source slug: `puzzling-riddle-clean`.
- Date range: `2025-05-01` to `2026-04-21`.
- Coded records: 50.
- Partial sample: false.
- Sample groups: clear_direct=13, ordinary_intermediate=13, high_effort_or_ambiguous=12, language_or_lateral=12.

## Coding Method

- Labeling method: llm_assisted_xhigh.
- Coding used controlled categories for puzzle type, qualitative difficulty, solution clarity, reasoning type, language dependence, misdirection, outside knowledge, answer explanation, comments or hints, model-evaluation suitability, and corpus-design implication.

## Aggregate Coding Counts

- puzzle_type: clue_puzzle=13, wordplay=12, riddle=9, mixed=8, lateral_thinking=4, logic_deduction=4.
- qualitative_difficulty: high=25, medium=17, low=8.
- solution_clarity: unique_solution=38, multiple_plausible_solutions=8, unclear_solution=4.
- reasoning_type: outside_knowledge=19, semantic_association=13, constraint_satisfaction=12, lateral_inference=6.
- language_dependence: high=29, medium=18, low=3.
- misdirection_level: mild=32, strong=17, none=1.
- outside_knowledge_needed: yes=35, no=9, uncertain=6.
- answer_explanation_quality: explicit=34, partial=13, minimal=3.
- comments_or_hints_role: not_needed=20, challenge_solution=12, clarify_prompt=9, provide_hint=9.
- model_evaluation_suitability: diagnostic_only=33, exclude=11, good=6.
- corpus_design_implication: add_diagnostic_subset=22, exclude_from_model_eval=10, include_comments_or_hints=10, keep_riddle_clean_profile=6, revise_tag_filters=2.

## Observed Puzzle-Difficulty Patterns

- Direct riddles are best suited for clean natural-language difficulty checks when the prompt and accepted solution relation are explicit.
- Wordplay and lateral puzzles are useful diagnostic cases because difficulty can come from ambiguity, hidden assumptions, or deliberate misdirection.
- Puzzling accepted answers are treated as accepted or intended solution candidates, not as identical to ordinary help-forum answerability.

## Language And Misdirection Patterns

- Language dependence and misdirection should be tracked separately from generic difficulty because they may favor or penalize language models differently.
- Strongly lateral or word-dependent records should remain visible as a diagnostic subset even when excluded from strict answerability benchmarks.

## Role Of Accepted Answers

- Accepted answers provide a practical solution anchor for the pilot.
- They still require qualitative interpretation because Puzzling can have multiple plausible or community-negotiated solutions.

## Role Of Comments And Hints

- Comments and hints may clarify puzzle constraints or reveal intended directions.
- The main pipeline keeps comments local but records whether they are needed for interpretation through aggregate coding.

## Model-Evaluation Suitability

- Good or diagnostic-only records: 39.
- Excluded records: 11.
- Unclear-solution records: 4.
- Qualitative acceptance gate: not_accepted.

## Corpus-Design Implications

- Keep Puzzling as a separate natural-language problem-solving track.
- Keep Mathematics as the formal-reasoning baseline rather than replacing it.
- Use Puzzling coding outcomes to decide whether the main corpus should include riddles, a diagnostic riddle subset, or both formal and natural-language tracks.

## Discussion Points For Supervisor

- Decide whether Puzzling is the preferred site for difficulty in words.
- Decide whether wordplay/lateral cases should be benchmark material or diagnostic material.
- Decide how much comment and hint context is acceptable in later model evaluation.

## Content Safety

- This memo contains aggregate counts and paraphrased methodological patterns only. It excludes post identifiers, puzzle titles, puzzle text, answer text, comment text, URLs, user handles, local review files, local coding files, and credentials.
