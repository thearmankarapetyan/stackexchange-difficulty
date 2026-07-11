# Configuration files

`characteristics.tsv` defines the order and meaning of the 47 columns written
by `build_characteristics.py`.

`summary_fields.tsv` is the field catalogue and default selection used by
`extract_request_summary.py`. Each row names one supported XML output field.
Set `include` to `TRUE` to write that field or `FALSE` to omit it. The output
order follows the row order. Copy the file before changing a selection that
must be preserved for a particular extraction.

The `source_record` and `source_attribute` columns show exactly where each
value comes from. The four source records are the question, its earliest direct
question comment, its earliest available answer, and its available accepted
answer. Empty XML elements represent source information that is unavailable
for the selected question.
