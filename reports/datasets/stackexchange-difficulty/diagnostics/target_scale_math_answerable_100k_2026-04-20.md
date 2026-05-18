# Target-Scale Inspection Diagnostics

## Source

- Inspected records: 100.
- Inputs were local ignored inspection files; this report contains aggregates only.

## Label Summary

- Suitable records: yes=78, no=8, uncertain=14.
- Answerability clear: yes=79, no=5, uncertain=16.
- Math notation readable: yes=98, no=2, uncertain=0.
- Needs comments: yes=1, no=96, uncertain=3.
- Reason codes: good=77, unclear_answerability=16, still_missing_context=3, unsuitable=3, notation_issue=1.

## Suitability By Stratum

- answered;accepted;open;not_duplicate;long_latency;tag_bucket:high: yes=12, no=0, uncertain=4.
- answered;accepted;open;not_duplicate;long_latency;tag_bucket:high;has_question_comments: yes=13, no=4, uncertain=1.
- answered;accepted;open;not_duplicate;long_latency;tag_bucket:medium;has_question_comments: yes=1, no=0, uncertain=0.
- answered;accepted;open;not_duplicate;short_latency;tag_bucket:high: yes=18, no=2, uncertain=0.
- answered;accepted;open;not_duplicate;short_latency;tag_bucket:high;has_question_comments: yes=32, no=2, uncertain=9.
- answered;accepted;open;not_duplicate;short_latency;tag_bucket:low;has_question_comments: yes=1, no=0, uncertain=0.
- answered;accepted;open;not_duplicate;short_latency;tag_bucket:medium;has_question_comments: yes=1, no=0, uncertain=0.

## Answerability By Stratum

- answered;accepted;open;not_duplicate;long_latency;tag_bucket:high: yes=11, no=0, uncertain=5.
- answered;accepted;open;not_duplicate;long_latency;tag_bucket:high;has_question_comments: yes=14, no=2, uncertain=2.
- answered;accepted;open;not_duplicate;long_latency;tag_bucket:medium;has_question_comments: yes=1, no=0, uncertain=0.
- answered;accepted;open;not_duplicate;short_latency;tag_bucket:high: yes=18, no=1, uncertain=1.
- answered;accepted;open;not_duplicate;short_latency;tag_bucket:high;has_question_comments: yes=33, no=2, uncertain=8.
- answered;accepted;open;not_duplicate;short_latency;tag_bucket:low;has_question_comments: yes=1, no=0, uncertain=0.
- answered;accepted;open;not_duplicate;short_latency;tag_bucket:medium;has_question_comments: yes=1, no=0, uncertain=0.

## Reason Codes By Stratum

- answered;accepted;open;not_duplicate;long_latency;tag_bucket:high: good=11, unclear_answerability=4, still_missing_context=1.
- answered;accepted;open;not_duplicate;long_latency;tag_bucket:high;has_question_comments: good=13, unclear_answerability=2, unsuitable=2, still_missing_context=1.
- answered;accepted;open;not_duplicate;long_latency;tag_bucket:medium;has_question_comments: good=1.
- answered;accepted;open;not_duplicate;short_latency;tag_bucket:high: good=18, notation_issue=1, unclear_answerability=1.
- answered;accepted;open;not_duplicate;short_latency;tag_bucket:high;has_question_comments: good=32, unclear_answerability=9, still_missing_context=1, unsuitable=1.
- answered;accepted;open;not_duplicate;short_latency;tag_bucket:low;has_question_comments: good=1.
- answered;accepted;open;not_duplicate;short_latency;tag_bucket:medium;has_question_comments: good=1.

## Metadata Buckets

- Sample strata: answered;accepted;open;not_duplicate;short_latency;tag_bucket:high;has_question_comments=43, answered;accepted;open;not_duplicate;short_latency;tag_bucket:high=20, answered;accepted;open;not_duplicate;long_latency;tag_bucket:high;has_question_comments=18, answered;accepted;open;not_duplicate;long_latency;tag_bucket:high=16, answered;accepted;open;not_duplicate;long_latency;tag_bucket:medium;has_question_comments=1, answered;accepted;open;not_duplicate;short_latency;tag_bucket:low;has_question_comments=1, answered;accepted;open;not_duplicate;short_latency;tag_bucket:medium;has_question_comments=1.
- score_bucket: low=58, medium=25, high=12, negative=5.
- view_bucket: low=57, medium=38, high=5.
- comment_count_bucket: low=44, none=36, high=20.
- latency_bucket: under_1h=34, under_24h=31, under_7d=20, over_7d=15.
- tag_popularity_bucket: high=97, medium=2, low=1.
- has_question_comments: true=64, false=36.

## Clean Sampling Recommendation

- Recommendation: Recommend using sample_profile=answerable_clean for the next target-scale run.

## Content Safety

- This diagnostic contains aggregate counts only. It does not include individual row identifiers, row-level text fields, formulas, links, user handles, label notes, or copied Stack Exchange post content.
