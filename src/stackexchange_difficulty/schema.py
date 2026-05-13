"""Schema constants derived from the methodological report."""

ARTIFICIAL_POST_IDS = {"1000000001", "1000000010"}

QUESTION_REQUIRED_COLUMNS = (
    "question_id",
    "title",
    "body_html",
    "tags",
    "creation_date",
    "score",
    "view_count",
    "answer_count",
    "comment_count",
    "closed_date",
    "accepted_answer_id",
    "is_duplicate",
    "content_license",
)

ANSWER_REQUIRED_COLUMNS = (
    "answer_id",
    "question_id",
    "body_html",
    "score",
    "creation_date",
    "is_accepted",
)

COMMENT_REQUIRED_COLUMNS = (
    "comment_id",
    "post_id",
    "text",
    "score",
    "creation_date",
)

SEDE_COMMENT_REQUIRED_COLUMNS = (
    "comment_id",
    "post_id",
    "question_id",
    "post_type_id",
    "text",
    "score",
    "creation_date",
    "content_license",
)

DERIVED_COLUMNS = (
    "question_id",
    "has_answer",
    "has_accepted_answer",
    "is_unanswered",
    "is_closed",
    "is_duplicate",
    "time_to_first_answer_hours",
    "time_to_accepted_answer_hours",
    "comment_count_before_first_answer",
    "tag_popularity_bucket",
    "rare_tag_flag",
    "question_length",
    "code_block_count",
    "contains_error_message",
)

PROVENANCE_REQUIRED_KEYS = (
    "source_method",
    "access_date",
    "license",
    "transformation_steps",
    "output_hash",
)

PROVENANCE_IDENTIFIER_KEYS = (
    "source_version",
    "source_identifier",
    "query_or_dump_file",
    "export_identifier",
)

SEDE_PILOT_REQUIRED_COLUMNS = (
    "question_id",
    "title",
    "body_html",
    "tags",
    "creation_date",
    "score",
    "view_count",
    "answer_count",
    "comment_count",
    "closed_date",
    "accepted_answer_id",
    "is_duplicate",
    "content_license",
    "first_answer_id",
    "first_answer_body_html",
    "first_answer_score",
    "first_answer_creation_date",
    "accepted_answer_body_html",
    "accepted_answer_score",
    "accepted_answer_creation_date",
)
