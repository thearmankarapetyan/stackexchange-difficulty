-- Stack Overflow SEDE non-coding-question pilot query template.
-- Purpose: export a 5,000-10,000 question pilot with the same columns as the
-- main pilot query, while targeting conceptual/non-implementation questions.
--
-- Stack Overflow is a programming site, so this is not a "non-programming"
-- query. It is a stricter Stack Overflow query for questions that are less
-- likely to ask for code, debugging, syntax repair, or script implementation.
--
-- Filters used:
--
-- 1. Exclude rendered code markup in the question body:
--        q.Body NOT LIKE '%<code>%'
--
-- 2. Require at least one conceptual or design-oriented tag.
--
-- 3. Exclude common language, framework, web UI, command-line, debugging, and
--    error/exception signals.
--
-- This remains a heuristic. Manual inspection is still required before treating
-- the result as a clean non-coding corpus.
--
-- Do not run this automatically from the repository. Copy it into
-- https://data.stackexchange.com/stackoverflow/query/new and save the query URL,
-- execution date, export filename, export hash, and SEDE refresh date.
--
-- Performance note:
-- The candidate seed is larger than the main pilot query because the filter is
-- restrictive. If SEDE times out, reduce SELECT TOP 200000 to SELECT TOP 100000.
-- If fewer than 5,000 rows are returned, increase the seed cautiously or broaden
-- the conceptual tag list.

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
        SELECT TOP 200000
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
          AND q.Body NOT LIKE '%<code>%'
          AND (
              q.Tags LIKE '%<algorithm>%'
              OR q.Tags LIKE '%<data-structures>%'
              OR q.Tags LIKE '%<design-patterns>%'
              OR q.Tags LIKE '%<database-design>%'
              OR q.Tags LIKE '%<architecture>%'
              OR q.Tags LIKE '%<terminology>%'
              OR q.Tags LIKE '%<language-agnostic>%'
              OR q.Tags LIKE '%<computer-science>%'
              OR q.Tags LIKE '%<complexity-theory>%'
              OR q.Tags LIKE '%<oop>%'
              OR q.Tags LIKE '%<functional-programming>%'
              OR q.Tags LIKE '%<recursion>%'
              OR q.Tags LIKE '%<concurrency>%'
              OR q.Tags LIKE '%<multithreading>%'
              OR q.Tags LIKE '%<performance>%'
              OR q.Tags LIKE '%<security>%'
          )
          AND q.Tags NOT LIKE '%<python>%'
          AND q.Tags NOT LIKE '%<javascript>%'
          AND q.Tags NOT LIKE '%<typescript>%'
          AND q.Tags NOT LIKE '%<java>%'
          AND q.Tags NOT LIKE '%<c#>%'
          AND q.Tags NOT LIKE '%<c++>%'
          AND q.Tags NOT LIKE '%<c>%'
          AND q.Tags NOT LIKE '%<php>%'
          AND q.Tags NOT LIKE '%<ruby>%'
          AND q.Tags NOT LIKE '%<go>%'
          AND q.Tags NOT LIKE '%<r>%'
          AND q.Tags NOT LIKE '%<swift>%'
          AND q.Tags NOT LIKE '%<kotlin>%'
          AND q.Tags NOT LIKE '%<rust>%'
          AND q.Tags NOT LIKE '%<scala>%'
          AND q.Tags NOT LIKE '%<html>%'
          AND q.Tags NOT LIKE '%<css>%'
          AND q.Tags NOT LIKE '%<sql>%'
          AND q.Tags NOT LIKE '%<mysql>%'
          AND q.Tags NOT LIKE '%<postgresql>%'
          AND q.Tags NOT LIKE '%<sql-server>%'
          AND q.Tags NOT LIKE '%<oracle>%'
          AND q.Tags NOT LIKE '%<bash>%'
          AND q.Tags NOT LIKE '%<shell>%'
          AND q.Tags NOT LIKE '%<powershell>%'
          AND q.Tags NOT LIKE '%<regex>%'
          AND q.Tags NOT LIKE '%<jquery>%'
          AND q.Tags NOT LIKE '%<reactjs>%'
          AND q.Tags NOT LIKE '%<angular>%'
          AND q.Tags NOT LIKE '%<node.js>%'
          AND q.Tags NOT LIKE '%<django>%'
          AND q.Tags NOT LIKE '%<flask>%'
          AND q.Tags NOT LIKE '%<spring>%'
          AND q.Tags NOT LIKE '%<.net>%'
          AND q.Tags NOT LIKE '%<android>%'
          AND q.Tags NOT LIKE '%<ios>%'
          AND q.Title NOT LIKE '%error%'
          AND q.Title NOT LIKE '%exception%'
          AND q.Title NOT LIKE '%traceback%'
          AND q.Title NOT LIKE '%stack trace%'
          AND q.Title NOT LIKE '%compile%'
          AND q.Title NOT LIKE '%compiler%'
          AND q.Title NOT LIKE '%syntax%'
          AND q.Title NOT LIKE '%debug%'
          AND q.Title NOT LIKE '%crash%'
          AND q.Title NOT LIKE '%undefined%'
          AND q.Title NOT LIKE '%null reference%'
          AND q.Title NOT LIKE '%segmentation fault%'
          AND q.Body NOT LIKE '%error%'
          AND q.Body NOT LIKE '%exception%'
          AND q.Body NOT LIKE '%traceback%'
          AND q.Body NOT LIKE '%stack trace%'
          AND q.Body NOT LIKE '%compile%'
          AND q.Body NOT LIKE '%compiler%'
          AND q.Body NOT LIKE '%syntax%'
          AND q.Body NOT LIKE '%debug%'
          AND q.Body NOT LIKE '%crash%'
          AND q.Body NOT LIKE '%undefined%'
          AND q.Body NOT LIKE '%null reference%'
          AND q.Body NOT LIKE '%segmentation fault%'
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
