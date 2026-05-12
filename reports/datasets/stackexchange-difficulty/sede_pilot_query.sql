-- Stack Overflow SEDE pilot query template.
-- Purpose: export a 5,000-10,000 question pilot with enough fields to build
-- question records, first-answer records, accepted-answer records, strata, and
-- provenance-aware validation outputs.
--
-- Do not run this automatically from the repository. Copy it into
-- https://data.stackexchange.com/stackoverflow/query/new and save the query URL,
-- execution date, export filename, export hash, and SEDE refresh date.
--
-- Performance note:
-- SEDE can time out if the query ranks all Stack Overflow questions before
-- applying TOP. This template first limits the candidate set to recent question
-- IDs, ranks only that bounded set, and joins answer bodies only after selecting
-- the pilot rows.

WITH seed_questions AS (
    SELECT
        q.Id AS question_id,
        q.Title AS title,
        q.Body AS body_html,
        q.Tags AS tags,
        q.CreationDate AS creation_date,
        q.Score AS score,
        q.ViewCount AS view_count,
        q.AnswerCount AS answer_count,
        q.CommentCount AS comment_count,
        q.ClosedDate AS closed_date,
        q.AcceptedAnswerId AS accepted_answer_id,
        q.ContentLicense AS content_license
    FROM (
        SELECT TOP 20000
            q.Id,
            q.Title,
            q.Body,
            q.Tags,
            q.CreationDate,
            q.Score,
            q.ViewCount,
            q.AnswerCount,
            q.CommentCount,
            q.ClosedDate,
            q.AcceptedAnswerId,
            q.ContentLicense
        FROM Posts AS q
        WHERE q.PostTypeId = 1
          AND q.Id NOT IN (1000000001, 1000000010)
        ORDER BY q.Id DESC
    ) AS q
),
question_base AS (
    SELECT
        q.question_id,
        q.title,
        q.body_html,
        q.tags,
        q.creation_date,
        q.score,
        q.view_count,
        q.answer_count,
        q.comment_count,
        q.closed_date,
        q.accepted_answer_id,
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM PostLinks AS pl
                WHERE pl.PostId = q.question_id AND pl.LinkTypeId = 3
            )
            THEN 'true'
            ELSE 'false'
        END AS is_duplicate,
        q.content_license,
        CASE WHEN q.answer_count > 0 THEN 'answered' ELSE 'unanswered' END AS answer_status,
        CASE WHEN q.accepted_answer_id IS NULL THEN 'no_accepted' ELSE 'accepted' END AS accepted_status,
        CASE WHEN q.closed_date IS NULL THEN 'open' ELSE 'closed' END AS closure_status,
        CASE
            WHEN q.tags LIKE '%<python>%' THEN 'python'
            WHEN q.tags LIKE '%<javascript>%' THEN 'javascript'
            WHEN q.tags LIKE '%<java>%' THEN 'java'
            WHEN q.tags LIKE '%<c#>%' THEN 'csharp'
            ELSE 'other'
        END AS tag_family,
        CASE
            WHEN q.creation_date < '2014-01-01' THEN 'older'
            WHEN q.creation_date < '2020-01-01' THEN 'middle'
            ELSE 'recent'
        END AS time_period
    FROM seed_questions AS q
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY answer_status, accepted_status, closure_status,
                         is_duplicate, tag_family, time_period
            ORDER BY ABS(CHECKSUM(question_id))
        ) AS stratum_rank
    FROM question_base
),
selected_questions AS (
    SELECT TOP 5000
        *
    FROM ranked
    ORDER BY stratum_rank, answer_status, accepted_status, closure_status,
             is_duplicate, tag_family, time_period, question_id
)
SELECT
    sq.question_id,
    sq.title,
    sq.body_html,
    sq.tags,
    sq.creation_date,
    sq.score,
    sq.view_count,
    sq.answer_count,
    sq.comment_count,
    sq.closed_date,
    sq.accepted_answer_id,
    sq.is_duplicate,
    sq.content_license,
    fa.Id AS first_answer_id,
    fa.Body AS first_answer_body_html,
    fa.Score AS first_answer_score,
    fa.CreationDate AS first_answer_creation_date,
    aa.Body AS accepted_answer_body_html,
    aa.Score AS accepted_answer_score,
    aa.CreationDate AS accepted_answer_creation_date,
    sq.answer_status,
    sq.accepted_status,
    sq.closure_status,
    sq.tag_family,
    sq.time_period
FROM selected_questions AS sq
OUTER APPLY (
    SELECT TOP 1 a.Id, a.Body, a.Score, a.CreationDate
    FROM Posts AS a
    WHERE a.PostTypeId = 2 AND a.ParentId = sq.question_id
    ORDER BY a.CreationDate ASC
) AS fa
LEFT JOIN Posts AS aa
    ON aa.Id = sq.accepted_answer_id
   AND aa.PostTypeId = 2
ORDER BY answer_status, accepted_status, closure_status, is_duplicate,
         tag_family, time_period, question_id;
