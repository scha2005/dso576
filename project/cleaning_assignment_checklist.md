# Data-Cleaning Assignment Checklist

Statuses and evidence below reflect the completed cleaning workflow and its artifacts. **Unresolved** items include the input needed before further cleaning or interpretation.

## 1. Project vision and question — Done

The project vision and business question were supplied in the project brief: a dashboard on AI workforce exposure, asking which jobs are most affected and comparing job exposure with task penetration. The [updated cleaning decision log](cleaned/cleaning_decision_log_updated.md) also states that the business question is identifying the jobs most affected. No claim about job replacement or job loss was added.

## 2. Definition of one row — Unresolved

The [profiling report](data_profile.md) verifies 756 rows of occupation code, title, and exposure in `job_exposure.csv`, and 17,998 rows of task description and penetration in `task_penetration.csv`. But the task file has 17,992 distinct task descriptions and no occupation key. The [reconciliation report](cleaned/reconciliation_report.md), “Type conversions and merge keys,” says the task row's association with an occupation cannot be verified. **Input needed:** confirm the source-defined task row grain or provide a documented task-to-occupation key.

## 3. Source preservation — Done

The [approved cleaning script](apply_approved_cleaning.py) reads the original CSVs and writes separate outputs under `cleaned/`. The [updated cleaning decision log](cleaned/cleaning_decision_log_updated.md), “Dataset results,” records equal source and output SHA-256 hashes for both files; parsed values and rows were also verified identical.

## 4. Columns and types — Done

The [profiling report](data_profile.md), “Columns,” lists inferred types, examples, and missing counts: 3 columns for the 756-row job file and 2 columns for the 17,998-row task file. `occ_code` was preserved as text. The [execution log](cleaned/cleaning_decision_log_updated.md) records zero numeric conversion failures for `observed_exposure` (756 valid values) and `penetration` (17,998 valid values). Numeric conversions were diagnostic only; the cleaned CSV fields remain source text.

## 5. Text standardization — Unresolved

The [updated cleaning decision log](cleaned/cleaning_decision_log_updated.md) records that the `Web` and `web` task descriptions were retained as written. It does not approve capitalization normalization. **Input needed:** decide whether case-only task variants should remain distinct or be standardized; confirm the source meaning first.

## 6. Duplicates — Unresolved

The [reconciliation report](cleaned/reconciliation_report.md), “Duplicate rows and repeated identifiers,” records 0 exact duplicate rows in the job file and 6 in the task file. The task column has 6 repeated occurrences beyond the first; all were retained, with no removal. **Input needed:** confirm whether repeated task rows represent legitimate source records or should be deduplicated.

## 7. Missing data — Done

The [reconciliation report](cleaned/reconciliation_report.md), “Missing values,” records 0 missing values before and after in every column. No rows were removed for missingness. Actual blank-value handling was not tested because neither source contains a missing value.

## 8. Suspicious values — Unresolved

The [reconciliation report](cleaned/reconciliation_report.md), “Suspicious values retained,” records 411 of 756 occupation exposures as zero (54.4%) and 16,644 of 17,998 task penetration values as zero (92.5%). The task metric also reaches 1.0; all values remained unchanged. The workflow flags these values for review, not as errors. **Input needed:** confirm metric definitions and what zero represents using the source methodology.

## 9. Merges — Unresolved

No merge was performed. The [reconciliation report](cleaned/reconciliation_report.md), “Type conversions and merge keys,” records that `task_penetration.csv` has no occupation code or title, so unmatched merge keys cannot be calculated and task values cannot be assigned to jobs from these files alone. **Input needed:** provide or identify a documented task-to-occupation crosswalk if task percentages must be compared by job.

## 10. Reconciliation — Done

The [reconciliation report](cleaned/reconciliation_report.md), “Row counts and row movement,” accounts for all row differences: 756 to 756 for jobs and 17,998 to 17,998 for tasks; 0 rows added or removed in either file. It also records unchanged missing counts, duplicate counts, repeated values, and metrics.

## 11. Calculations — Done

The [reconciliation report](cleaned/reconciliation_report.md), “Metric totals and valid-record denominators,” reports:

- `observed_exposure`: sum **58.1944**, mean **0.0769767196**, denominator **756** before and after.
- `penetration`: sum **1,201.2546**, mean **0.0667437826**, denominator **17,998** before and after.

All metric values were nonmissing and converted successfully for these diagnostic calculations. The report cautions that summing row-level exposure values may not be a meaningful overall exposure score.

## 12. Five individual record checks — Done

The [manual verification results](manual_verification_sample.md) record **5 of 5 checks as matching** their pre-run expectations, with no mismatches:

1. `occ_code=11-1011` preserved as text.
2. Repeated task at source CSV line 17,891 retained among four identical occurrences.
3. `occ_code=11-1031` retained with `observed_exposure=0.0`.
4. Task merge probe remained unassigned because it has no occupation key.
5. Task at source CSV line 343 retained with `penetration=1.0`.

## 13. Reproducibility — Done

The workflow scripts are [profile_datasets.py](profile_datasets.py), [apply_approved_cleaning.py](apply_approved_cleaning.py), and [create_submission_sample.py](create_submission_sample.py). The reconciliation report documents the before-and-after checks; the [sample README](submission_sample/README.md) documents a **48-row** sample split into 23 job rows and 25 task rows.

## 14. Remaining limitations — Unresolved

The [updated cleaning decision log](cleaned/cleaning_decision_log_updated.md) and [reconciliation report](cleaned/reconciliation_report.md) leave task duplicate handling, task-to-job linkage, metric interpretation, and capitalization normalization unresolved. The recorded source version and download date are unknown. Actual missing-value behavior has not been tested because there are no missing values. **Input needed:** resolve the task row grain and crosswalk, source release/date, duplicate policy, text-normalization policy, and metric definitions before making those transformations or interpreting task results by occupation.
