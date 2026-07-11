# Design and scientific scope

[Documentation home](../README.md) · [Tutorial](../tutorials/first-analysis.md) · [How-to guides](../how-to/access-data-dump.md) · [Reference](../reference/system-reference.md) · [Explanation](../explanation/design-and-scope.md)

## About the research problem and implemented scope

The project studies observable signals associated with question difficulty in a setting
where humans and generative models may experience difficulty differently. Stack Exchange
supplies real questions together with traces of human response: answers, direct
clarification comments, accepted solutions, closure, votes, views, tags, and elapsed
times.

These traces support analysis of human response conditions. A question with delayed
answers, several clarification comments, closure, or no accepted answer can deserve
closer examination. Each trace remains evidence about community activity and requires
interpretation within the dump snapshot and the selected observation period.

The implemented software prepares this evidence. It reconstructs threads, produces
selected summaries, builds a documented question-level table, validates each analytical
run, and presents exploratory results. Difficulty judgements and generative-model
performance values belong to separately documented assessment protocols.

## About the three result routes

The routes serve three levels of evidence. Complete-thread XML preserves the richest
source representation for reading and sharing. Selected-summary XML creates a compact
file whose fields can be aligned with a reporting request. The characteristic route
transforms source records into a stable analytical table and then presents aggregate
patterns and concrete cases through one notebook.

Keeping these routes separate protects their distinct purposes. Source-rich
reconstruction supports qualitative inspection. Configurable summaries support focused
exchange. The 47-field table supports systematic comparison, validation, and exploratory
analysis. All routes share ID, timestamp, ordering, and safe-writing rules where their
source semantics are the same.

## About provenance and information layers

| **Information layer**   | **Examples**                                                       | **Interpretive role**                                              |
|-------------------------|--------------------------------------------------------------------|--------------------------------------------------------------------|
| Provenance              | Community, snapshot date, URL, licence, source files.              | Identifies where the evidence came from and supports reproduction. |
| Question representation | Title, rendered body, tags, words, code, links, images.            | Describes the question content available in the snapshot.          |
| Human-response evidence | Answers, comments, closure, acceptance, scores, views, and delays. | Describes community activity observed by the snapshot.             |
| Difficulty assessment   | A documented manual judgement or model-performance value.          | Supplies a study outcome through a separate assessment method.     |

The table keeps provenance, source-maintained values, project calculations, and
assessment outcomes conceptually distinct. This separation makes it possible to trace a
result to its source and prevents an analytical signal from being presented as a
difficulty label by itself.

## About snapshot-based evidence

### Question state and observation time

Posts.xml represents the rendered question state present in the downloaded snapshot. A
title or body can include edits made after posting. Scores and views accumulate through
the snapshot. observation_days_at_dump records the length of follow-up available for
each selected question. Historical pre-edit wording requires PostHistory.xml, which is
outside the implemented pipeline.

### Platform counters and available rows

Stack Exchange maintains AnswerCount and CommentCount on the question row. The project
also counts answer rows and direct question-comment rows available in the downloaded
XML. Deleted or unavailable records can produce a difference between these values.
Keeping both preserves source provenance and exposes the difference through WARN rows in
validation.tsv.

### Answer posting and acceptance

The accepted answer CreationDate records when that answer was posted. A Votes.xml row
with VoteTypeId 1 records the acceptance action at calendar-day precision. The table
therefore stores accepted_answer_creation_datetime and
time_to_eventually_accepted_answer_post_hours separately from acceptance_date and
days_to_acceptance. This distinction keeps answer availability and the later author
action interpretable.

## About configurability and one generic notebook

Run-specific choices belong in command arguments, configuration files, or the notebook
settings cell. This design allows the same production logic to work with compatible
communities, source folders, snapshots, date periods, question IDs, summary selections,
schemas, and output locations.

The summary catalogue provides a reviewed set of supported source mappings while
allowing each run to select and order the required fields. The notebook applies one
visible analysis sequence to every compatible characteristic TSV. Its explanations,
parameters, direct pandas/Matplotlib/SciPy code, figures, and interpretations remain
together, which keeps the analytical path inspectable.

## About validation and reproducibility

The builder publishes analytical values together with validation.tsv and
run_metadata.json because a table alone cannot identify how it was produced. Validation
records structural checks and source differences. Metadata records the selected site,
snapshot, question period, schema, limit, source files, software context, and output
totals.

A controlled small run exposes input, schema, and calculation problems quickly. A
clean-kernel notebook execution checks cell order and hidden state. Byte-for-byte XML
comparisons verify stable extraction behavior. Visual review checks information that
structural tests cannot assess, such as clipping, overlap, and readability. Together
these checks create evidence that can be examined after the execution has ended.

## Scope boundaries

- Complete-thread extraction contains comments attached directly to the question and all
  available answers. Answer comments are outside the agreed extraction scope.

- The characteristic table represents the current 47-field specification and the
  selected dump snapshot.

- Acceptance events have calendar-day precision in public Votes.xml data.

- Deleted or unavailable source rows can create documented differences between
  platform-maintained counters and reconstructed row counts.

- Human-response traces support analysis and case selection. Difficulty categories
  require explicit assessment criteria.

- Raw dumps and regenerated annual outputs remain external or ignored because of their
  size.

- The repository records local Git history and currently has no configured remote.

> **Reading boundary:** This documentation describes the implemented Stack Exchange evidence workflow. The scientific review in [state-of-the-art-qpp-ppp-rag.pdf](state-of-the-art-qpp-ppp-rag.pdf) provides the wider QPP, PPP, and RAG research context.
