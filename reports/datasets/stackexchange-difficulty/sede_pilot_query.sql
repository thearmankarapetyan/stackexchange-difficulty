-- Stack Overflow SEDE pilot query template.
-- Purpose: export a 5,000-10,000 question pilot with enough fields to build
-- question records, first-answer records, accepted-answer records, strata, and
-- provenance-aware validation outputs.
--
-- Do not run this automatically from the repository. Copy it into
-- https://data.stackexchange.com/stackoverflow/query/new and save the query URL,
-- execution date, export filename, export hash, and SEDE refresh date.

DECLARE @RowsPerStratum int = 80;

WITH question_base AS (
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
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM PostLinks AS pl
                WHERE pl.PostId = q.Id AND pl.LinkTypeId = 3
            )
            THEN 'true'
            ELSE 'false'
        END AS is_duplicate,
        q.ContentLicense AS content_license,
        CASE WHEN q.AnswerCount > 0 THEN 'answered' ELSE 'unanswered' END AS answer_status,
        CASE WHEN q.AcceptedAnswerId IS NULL THEN 'no_accepted' ELSE 'accepted' END AS accepted_status,
        CASE WHEN q.ClosedDate IS NULL THEN 'open' ELSE 'closed' END AS closure_status,
        CASE
            WHEN q.Tags LIKE '%<python>%' THEN 'python'
            WHEN q.Tags LIKE '%<javascript>%' THEN 'javascript'
            WHEN q.Tags LIKE '%<java>%' THEN 'java'
            WHEN q.Tags LIKE '%<c#>%' THEN 'csharp'
            ELSE 'other'
        END AS tag_family,
        CASE
            WHEN q.CreationDate < '2014-01-01' THEN 'older'
            WHEN q.CreationDate < '2020-01-01' THEN 'middle'
            ELSE 'recent'
        END AS time_period
    FROM Posts AS q
    WHERE q.PostTypeId = 1
      AND q.Id NOT IN (1000000001, 1000000010)
),
answer_context AS (
    SELECT
        qb.*,
        fa.Id AS first_answer_id,
        fa.Body AS first_answer_body_html,
        fa.Score AS first_answer_score,
        fa.CreationDate AS first_answer_creation_date,
        aa.Body AS accepted_answer_body_html,
        aa.Score AS accepted_answer_score,
        aa.CreationDate AS accepted_answer_creation_date
    FROM question_base AS qb
    OUTER APPLY (
        SELECT TOP 1 a.Id, a.Body, a.Score, a.CreationDate
        FROM Posts AS a
        WHERE a.PostTypeId = 2 AND a.ParentId = qb.question_id
        ORDER BY a.CreationDate ASC
    ) AS fa
    LEFT JOIN Posts AS aa
        ON aa.Id = qb.accepted_answer_id
       AND aa.PostTypeId = 2
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY answer_status, accepted_status, closure_status,
                         is_duplicate, tag_family, time_period
            ORDER BY ABS(CHECKSUM(question_id))
        ) AS stratum_rank
    FROM answer_context
)
SELECT TOP 10000
    question_id,
    title,
    body_html,
    tags,
    creation_date,
    score,
    view_count,
    answer_count,
    comment_count,
    closed_date,
    accepted_answer_id,
    is_duplicate,
    content_license,
    first_answer_id,
    first_answer_body_html,
    first_answer_score,
    first_answer_creation_date,
    accepted_answer_body_html,
    accepted_answer_score,
    accepted_answer_creation_date,
    answer_status,
    accepted_status,
    closure_status,
    tag_family,
    time_period
FROM ranked
WHERE stratum_rank <= @RowsPerStratum
ORDER BY answer_status, accepted_status, closure_status, is_duplicate,
         tag_family, time_period, question_id;
