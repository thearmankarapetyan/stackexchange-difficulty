-- Stack Exchange SEDE Mathematics answerable pilot query.
-- Purpose: export a cleaner 5,000-row Mathematics pilot centered on questions
-- with accepted answers. This query keeps the same output schema as the local
-- ingestion pipeline while reducing closed, duplicate, unanswered, and
-- no-accepted-answer records.
--
-- Run this on Mathematics SEDE:
-- https://data.stackexchange.com/math/query/new
--
-- The sample size is controlled by the literal SELECT TOP 5000 in the final
-- selected_questions CTE. If SEDE times out, reduce the seed_questions TOP
-- value first while preserving the output aliases below.

WITH seed_questions AS (
    SELECT TOP 50000
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
    FROM Posts AS q
    INNER JOIN Posts AS aa_check
        ON aa_check.Id = q.AcceptedAnswerId
       AND aa_check.PostTypeId = 2
       AND aa_check.ParentId = q.Id
    WHERE q.PostTypeId = 1
      AND q.Id NOT IN (1000000001, 1000000010)
      AND q.ClosedDate IS NULL
      AND q.AnswerCount > 0
      AND q.AcceptedAnswerId IS NOT NULL
      AND NOT EXISTS (
          SELECT 1
          FROM PostLinks AS pl
          WHERE pl.PostId = q.Id
            AND pl.LinkTypeId = 3
      )
    ORDER BY q.Id DESC
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
        'false' AS is_duplicate,
        q.content_license,
        'answered' AS answer_status,
        'accepted' AS accepted_status,
        'open' AS closure_status,
        CASE
            WHEN q.tags IS NULL OR q.tags = '' THEN 'none'
            WHEN CHARINDEX('><', q.tags) > 0
                THEN LOWER(SUBSTRING(q.tags, 2, CHARINDEX('><', q.tags) - 2))
            ELSE LOWER(REPLACE(REPLACE(q.tags, '<', ''), '>', ''))
        END AS tag_family,
        CASE
            WHEN q.creation_date < '2014-01-01' THEN 'older'
            WHEN q.creation_date < '2020-01-01' THEN 'middle'
            ELSE 'recent'
        END AS time_period
    FROM seed_questions AS q
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
        aa.CreationDate AS accepted_answer_creation_date,
        CASE
            WHEN DATEDIFF(hour, qb.creation_date, fa.CreationDate) < 1 THEN 'under_1h'
            WHEN DATEDIFF(hour, qb.creation_date, fa.CreationDate) < 24 THEN 'under_24h'
            WHEN DATEDIFF(hour, qb.creation_date, fa.CreationDate) < 168 THEN 'under_7d'
            ELSE 'over_7d'
        END AS answer_latency_bucket,
        CASE
            WHEN qb.score < 0 THEN 'negative'
            WHEN qb.score < 3 THEN 'low'
            WHEN qb.score < 10 THEN 'medium'
            ELSE 'high'
        END AS score_bucket,
        CASE
            WHEN qb.view_count < 500 THEN 'low'
            WHEN qb.view_count < 5000 THEN 'medium'
            ELSE 'high'
        END AS view_bucket,
        CASE
            WHEN qb.comment_count = 0 THEN 'none'
            WHEN qb.comment_count < 4 THEN 'low'
            ELSE 'high'
        END AS comment_count_bucket
    FROM question_base AS qb
    CROSS APPLY (
        SELECT TOP 1 a.Id, a.Body, a.Score, a.CreationDate
        FROM Posts AS a
        WHERE a.PostTypeId = 2
          AND a.ParentId = qb.question_id
        ORDER BY a.CreationDate ASC
    ) AS fa
    INNER JOIN Posts AS aa
        ON aa.Id = qb.accepted_answer_id
       AND aa.PostTypeId = 2
       AND aa.ParentId = qb.question_id
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY tag_family, time_period, answer_latency_bucket,
                         score_bucket, view_bucket, comment_count_bucket
            ORDER BY ABS(CHECKSUM(question_id))
        ) AS stratum_rank
    FROM answer_context
),
selected_questions AS (
    SELECT TOP 5000
        *
    FROM ranked
    ORDER BY stratum_rank, tag_family, time_period, answer_latency_bucket,
             score_bucket, view_bucket, comment_count_bucket, question_id
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
    sq.first_answer_id,
    sq.first_answer_body_html,
    sq.first_answer_score,
    sq.first_answer_creation_date,
    sq.accepted_answer_body_html,
    sq.accepted_answer_score,
    sq.accepted_answer_creation_date,
    sq.answer_status,
    sq.accepted_status,
    sq.closure_status,
    sq.tag_family,
    sq.time_period
FROM selected_questions AS sq
ORDER BY tag_family, time_period, answer_latency_bucket,
         score_bucket, view_bucket, comment_count_bucket, question_id;
