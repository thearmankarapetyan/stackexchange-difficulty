-- Stack Exchange SEDE comment-enrichment query template.
-- Purpose: export comments for an existing local pilot without reselecting a
-- different question sample. The local tool renders the VALUES blocks from the
-- already downloaded pilot question IDs and included first/accepted answer IDs.
--
-- The rendered query is written under ignored data/processed/... because it
-- contains real Stack Exchange post IDs. Do not commit the rendered query.
-- Paste only the rendered ignored query into the selected SEDE site's editor.

WITH selected_questions(question_id) AS (
    SELECT v.question_id
    FROM (VALUES
        {question_values}
    ) AS v(question_id)
    WHERE v.question_id IS NOT NULL
),
selected_answer_posts(post_id, question_id) AS (
    SELECT v.post_id, v.question_id
    FROM (VALUES
        {answer_values}
    ) AS v(post_id, question_id)
    WHERE v.post_id IS NOT NULL
),
selected_posts(post_id, question_id) AS (
    SELECT question_id AS post_id, question_id
    FROM selected_questions
    UNION ALL
    SELECT post_id, question_id
    FROM selected_answer_posts
)
SELECT
    c.Id AS comment_id,
    c.PostId AS post_id,
    sp.question_id AS question_id,
    p.PostTypeId AS post_type_id,
    c.Text AS text,
    c.Score AS score,
    c.CreationDate AS creation_date,
    c.ContentLicense AS content_license
FROM Comments AS c
JOIN selected_posts AS sp
    ON sp.post_id = c.PostId
JOIN Posts AS p
    ON p.Id = c.PostId
ORDER BY sp.question_id, c.PostId, c.CreationDate, c.Id;
