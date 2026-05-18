# Qualitative Analysis Of Recent Mathematics Threads - 2026-05-18

## Objective

This memo summarizes a qualitative slice requested by the supervisor: recent Mathematics exchanges that began between May 2025 and April 2026.

## Source And Sample

- Site slug: `math`.
- Source slug: `math-answerable-clean-100k`.
- Date range: `2025-05-01` to `2026-04-20`.
- Coded records: 30.
- Sample groups: clear_direct=10, high_effort_or_ambiguous=10, ordinary_intermediate=10.

## Coding Method

- Labeling method: llm_assisted_xhigh.
- Coding used controlled categories for difficulty, answerability, difficulty source, response type, interaction role, notation/formulation, comment need, and corpus-design implication.

## Aggregate Coding Results

- qualitative_difficulty: high=16, low=5, medium=9.
- answerability_clarity: clear=21, partially_clear=9.
- source_of_difficulty: computational=5, conceptual=8, domain_specific=7, missing_context=2, multi_step_reasoning=2, notation_or_formulation=1, proof_based=5.
- answer_type: correction=3, direct_solution=5, explanation=11, partial_answer=4, proof=7.
- interaction_role: comments_clarify_question=7, comments_correct_answer=1, comments_not_available_or_not_needed=4, comments_reveal_missing_context=3, no_comments_needed=15.
- notation_or_formulation_issue: minor=11, none=15, significant=4.
- comments_needed: no=19, uncertain=1, yes=10.
- corpus_design_implication: add_diagnostic_subset=8, include_comments=9, keep_main_clean_corpus=13.

## Observed Qualitative Patterns

- Clear recent cases tend to remain usable when the problem object and requested result are explicit.
- Higher-effort cases are mainly useful as diagnostic material when they show missing context, multi-step reasoning, or formulation uncertainty.
- The clean sample remains suitable as the main answerable corpus layer, while a smaller diagnostic layer can preserve more ambiguous cases.

## Difficulty And Answerability Signals

- The qualitative coding supports using latency, interaction volume, and question length as descriptive indicators rather than final difficulty labels.
- Accepted-answer presence is useful for answerability, but qualitative review is still needed before treating it as a correctness signal.

## Role Of Comments And Interaction

- Comments are most useful when they clarify assumptions, expose missing context, or reveal correction work.
- Most clean-profile records do not require comments for basic answerability judgment, but comments remain useful for diagnostic subsets.

## Implications For Corpus Design

- Keep `answerable_clean` as the default main corpus profile for Mathematics.
- Add a separate diagnostic qualitative subset for ambiguous, context-dependent, or high-effort cases.
- Treat derived indicators as interpretive controls before using them as difficulty labels.

## Discussion Points For Supervisor Meeting

- Confirm Mathematics as the first validated site or redirect toward a code-centric Stack Exchange site.
- Decide whether the main corpus and diagnostic subset should be separated.
- Decide when comments should become part of the default analysis layer.
- Decide whether future labels should target difficulty, answerability, or both.

## Content Safety

- This memo contains aggregate counts and paraphrased methodological patterns only. It excludes row-level identifiers, original post content, copied mathematical expressions, links, user handles, local review files, and local coding files.
