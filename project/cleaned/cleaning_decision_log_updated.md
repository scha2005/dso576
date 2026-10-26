# Proposed Data-Cleaning Decision Log

Approved, lossless rules have been applied as documented in the execution results below. **Unresolved** means the decision still needs your judgment before any further transformation. Unusual values are flagged for review, not treated as errors by default.

| Dataset and column | Observed problem | Proposed cleaning rule | Reason the rule supports the project question | Exceptions or values that must be preserved | Verification check | Status |
|---|---|---|---|---|---|---|
| `job_exposure.csv` — `occ_code` | All 756 values are present and unique. Codes look like identifiers, not quantities. | Keep as text; do not strip punctuation, cast to numbers, or reformat. | Preserves occupation identifiers for reliable job comparisons and possible joins. | Preserve each original code exactly, including leading zeros or punctuation if present. | Confirm 756 nonmissing, unique codes before and after any future processing; compare values with source. | Approved |
| `job_exposure.csv` — `title` | All 756 titles are present and unique in this file. | Preserve original title text; do not use title alone as a join key. | Titles make job comparisons readable, while the code is a more stable identifier. | Preserve wording, capitalization, and punctuation from source. **Judgment required:** whether to add a display-only standardized title later. | Confirm titles are unchanged; check any future title mapping against `occ_code`. | Unresolved |
| `job_exposure.csv` — `observed_exposure` | No missing or failed numeric values; range is 0 to 0.7451. About 54.4% are zero. | Parse to numeric for analysis; preserve the original value and retain zeros. Flag zero concentration for interpretation, not deletion. | Enables sorting and comparing jobs by exposure while retaining potentially meaningful low or zero values. | Preserve zero and all source values in range. **Judgment required:** confirm the metric's definition and whether zeros represent measured zero exposure. | Check conversion failures, min/max, count of zeros, and compare row count and values with source. | Unresolved |
| `task_penetration.csv` — `task` | No missing task text; 17,992 distinct descriptions among 17,998 rows. Two descriptions each occur four times; they differ only in `Web`/`web` capitalization. | Preserve task text as supplied. Do not deduplicate or normalize capitalization until row meaning is confirmed. | Task descriptions may be needed to explain exposure patterns and connect task-level findings to jobs. | Preserve all repeated rows and both capitalization variants for now. **Judgment required:** are repeated rows legitimate task-to-occupation records or accidental duplicates? | Count exact task strings and exact full rows; inspect source structure and any available occupation mapping. | Unresolved |
| `task_penetration.csv` — `penetration` | No missing or failed numeric values; range is 0 to 1. About 92.5% are zero. | Parse to numeric for analysis; preserve original values and zeros. Review the high zero share before interpreting it. | Enables task-level comparisons while avoiding unsupported removal of low or zero-penetration tasks. | Preserve zeros and all values in range. **Judgment required:** confirm the metric definition and what a zero means. | Check conversion failures, min/max, zero count, and compare with source documentation. | Unresolved |
| `task_penetration.csv` — `task` and `penetration` together | Six exact duplicate rows exist. The task column repeats, and this file has no occupation code or title. | Do not drop duplicates or assign tasks to jobs without confirming the source row grain and obtaining a valid occupation link. | The business question asks which jobs are most affected; task values need a defensible job association for job-level task comparisons. | Preserve all six repeated rows and their values pending confirmation. **Judgment required:** whether duplicates are redundant and whether an external crosswalk is intended. | Confirm documented row grain and available join key; then compare row counts and task-to-job links before and after any approved action. | Unresolved |
| Both files — all columns | No missing values were found; neither file has date-like columns. | Make no missing-value or date-conversion changes. If missing values appear in later versions, retain those rows and report missingness unless a separate rule is approved. | Avoids dropping potentially relevant jobs or tasks and keeps the current profile reproducible. | Preserve current rows; do not infer dates or remove rows based on missingness. | Re-profile missing values, row counts, and columns on each new source version. | Approved |
| Both files — metric display | Metric values are fractions in the observed range; the project describes exposure and task percentage. | Keep stored source values unchanged. **Judgment required:** approve whether dashboard display should multiply by 100 and label values as percentages. | A consistent display could make exposure and task penetration easier to compare. | Preserve raw fractional values; do not overwrite them with percentage-scaled values. | Check display conversion on known examples, such as 0.5 displaying as 50%, while confirming source definitions. | Unresolved |

The profiler recorded the version and download date as unknown. Confirming the exact source release and the task file's row meaning are the main prerequisites for deciding whether any repeated task rows can safely be removed or linked to jobs.

---

# Cleaning Decision Log — Execution Results

Generated: 2026-10-05T01:08:47-07:00

Only rules marked **Approved** in `cleaning_decision_log.md` were applied. The approved rules preserve occupation identifiers as text and retain rows because current missing counts are zero and no date columns exist.

No unresolved rule was applied. Numeric parsing, duplicate checks, and repeated identifier checks below are diagnostics only. The outputs retain all source values and rows; 'cleaned' denotes pipeline output, not additional data modifications.

## Approved rules and recorded changes

| Approved rule | Result | Changed values | Changed/removed rows |
|---|---|---:|---:|
| Preserve `job_exposure.csv` `occ_code` as text | Applied; all source identifier strings retained | 0 | 0 |
| Retain rows and make no missing/date changes when none are present | Applied; no missing values or date-like columns found | 0 | 0 |
| Preserve all remaining source columns and values pending unresolved decisions | Output values verified equal to parsed originals | 0 | 0 |

## Dataset results

## `job_exposure.csv`

- Output: `C:\Users\sumed\dso576\project\cleaned\job_exposure_cleaned.csv`
- Rows: 756 before; 756 after; 0 changed or removed.
- Columns: 3 (preserved).
- Exact duplicate rows: 0 before; 0 after; none removed.
- Repeated likely identifier values (reported separately from exact duplicate rows):
  - `occ_code`: 756 distinct; 0 repeated occurrences beyond first.
- Missing values by column (before -> after):
  - `occ_code`: 0 -> 0.
  - `title`: 0 -> 0.
  - `observed_exposure`: 0 -> 0.
- Numeric conversion checks (diagnostic only; no type conversion applied):
  - `observed_exposure`: 0 failed nonblank conversions.
- Suspicious metric checks (diagnostic only):
  - `observed_exposure`: range 0..0.7451; 411/756 values are zero (54.4%); zeros retained.
- Date conversion checks: no date-like columns; no date conversions attempted.
- Source SHA-256: `4f0a3adf5feeb2ec5f5d02ab18cc5e851a2a4b8470bde84c0c9335017be12d68`.
- Output SHA-256: `4f0a3adf5feeb2ec5f5d02ab18cc5e851a2a4b8470bde84c0c9335017be12d68`.
## `task_penetration.csv`

- Output: `C:\Users\sumed\dso576\project\cleaned\task_penetration_cleaned.csv`
- Rows: 17,998 before; 17,998 after; 0 changed or removed.
- Columns: 2 (preserved).
- Exact duplicate rows: 6 before; 6 after; none removed.
- Repeated likely identifier values (reported separately from exact duplicate rows):
  - `task`: 17,992 distinct; 6 repeated occurrences beyond first.
    - Examples: `Write interesting and effective press releases, prepare information for media kits, and develop and maintain company internet or intranet Web pages.` (4 rows); `Write interesting and effective press releases, prepare information for media kits, and develop and maintain company internet or intranet web pages.` (4 rows)
- Missing values by column (before -> after):
  - `task`: 0 -> 0.
  - `penetration`: 0 -> 0.
- Numeric conversion checks (diagnostic only; no type conversion applied):
  - `penetration`: 0 failed nonblank conversions.
- Suspicious metric checks (diagnostic only):
  - `penetration`: range 0..1; 16,644/17,998 values are zero (92.5%); zeros retained.
- Date conversion checks: no date-like columns; no date conversions attempted.
- Source SHA-256: `85bee872db1d55d3e9a7f4e89da5ae4a5d59aa8ec875d728fbf4b7d820984616`.
- Output SHA-256: `85bee872db1d55d3e9a7f4e89da5ae4a5d59aa8ec875d728fbf4b7d820984616`.

## Unresolved or suspicious items (flagged, not changed)

- Numeric metrics remain strings in the full cleaned CSVs because their conversion rules are unresolved in the decision log.
- Exact duplicate rows and repeated identifier values are counted separately; neither is removed.
- Zero-heavy metric distributions and task-description repetitions remain as in the sources and require source-methodology review.
- No rows were dropped because of missingness; the observed missing counts are zero.

The original proposal and status table are retained in `cleaning_decision_log.md`. This generated execution record supplements it without changing unresolved statuses.
