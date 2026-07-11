# How to create complete-thread XML

[Documentation home](../README.md) · [Tutorial](../tutorials/first-analysis.md) · [How-to guides](../how-to/access-data-dump.md) · [Reference](../reference/system-reference.md) · [Explanation](../explanation/design-and-scope.md)

> **Goal:** Create one XML file containing one or more questions, each question’s direct comments, and every available answer.

**Before starting:** Prepare a folder containing Posts.xml and Comments.xml, then
collect one or more question post IDs from the same community.

```bash
python src/extract_threads.py \
  --dump-dir /path/to/extracted-dump \
  --output /path/to/results/complete-threads.xml \
  QUESTION_ID [QUESTION_ID ...]
```

> **1. Choose the destination.** Use a new XML path outside the source dump folder.
>
> **2. Run the extractor.** Supply the dump folder, destination, and question IDs in the
> required order.
>
> **3. Open the result.** Inspect the threads root and one thread element for each
> distinct requested ID.
>
> **4. Check the content.** Confirm each thread contains its question, a comments
> container, and an answers container.

> **Completion check:** The command returns successfully, the destination contains well-formed XML, and every selected question has its direct question comments and all available answers. See the [source XML contracts](../reference/system-reference.md#source-xml-contracts) and [output contracts](../reference/system-reference.md#output-contracts).
