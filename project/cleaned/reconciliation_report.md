# Original-to-Cleaned Data Reconciliation

Compared the original CSVs in `project/` with the generated outputs in `project/cleaned/`. The cleaned outputs currently match their corresponding originals byte-for-byte and row-for-row. No approved rule changed a value or row.

## Row counts and row movement

| Dataset | Starting rows | Final rows | Added | Removed | Numerical explanation for differences |
|---|---:|---:|---:|---:|---|
| `job_exposure.csv` → `job_exposure_cleaned.csv` | 756 | 756 | 0 | 0 | No differences. The approved identifier-preservation and row-retention rules make no row changes. |
| `task_penetration.csv` → `task_penetration_cleaned.csv` | 17,998 | 17,998 | 0 | 0 | No differences. Repeated task descriptions and six exact duplicate rows were retained because duplicate-removal rules are unresolved. |

All row-count differences are accounted for: there are no additions and no removals in either dataset. The source and output CSVs have equal SHA-256 hashes for each pair, and parsed rows and columns are identical.

## Missing values

| Dataset | Column | Before | After | Effect |
|---|---|---:|---:|---|
| `job_exposure.csv` | `occ_code` | 0 | 0 | None; every row has an occupation code. |
| `job_exposure.csv` | `title` | 0 | 0 | None. |
| `job_exposure.csv` | `observed_exposure` | 0 | 0 | None. |
| `task_penetration.csv` | `task` | 0 | 0 | None; every row has task text. |
| `task_penetration.csv` | `penetration` | 0 | 0 | None. |

No rows were removed for missing data. Since there are no missing metric values, the before-and-after sums and averages use every row. If missing metric values occur in a future version, this pipeline currently makes no imputation: a sum would use observed values, and an average's denominator should be the count of valid, nonmissing values. The denominator must be reported alongside the average. No missing values are silently counted as zero.

## Duplicate rows and repeated identifiers

| Dataset | Exact duplicate rows before → after | Likely ID/key column | Distinct values | Repeated occurrences beyond first before → after | Handling |
|---|---:|---|---:|---:|---|
| `job_exposure.csv` | 0 → 0 | `occ_code` | 756 | 0 → 0 | All occupation codes retained. |
| `task_penetration.csv` | 6 → 6 | `task` (candidate identifier only) | 17,992 | 6 → 6 | All repeated task descriptions and all six exact duplicate rows retained. |

Exact full-row duplicates and repeated values in a likely ID column are counted separately. In the task file, each of two task descriptions occurs four times, giving six occurrences beyond the first; these rows are also six exact full-row duplicates because their penetration values match. Neither count was treated as authorization to delete rows.

## Type conversions and merge keys

- Numeric conversion failures: `observed_exposure`, 0 of 756 nonblank values; `penetration`, 0 of 17,998 nonblank values. Numeric parsing was diagnostic only; source values remain unchanged in the cleaned CSVs.
- Date conversions: no date-like columns were found, so no date conversion was attempted.
- Unmatched merge keys: not evaluated because no merge was performed. `job_exposure.csv` has `occ_code`; `task_penetration.csv` has no occupation code or title to join on. Therefore there is no defensible set of task-to-job keys to compare, and task penetration cannot be reconciled to occupations from these two files alone.
- Missing group or occupation keys: the job file has 0 missing `occ_code` values. The task file has no occupation/group key column, so its records are not assigned to occupations or grouped by occupation. No key was inferred from task wording.

## Metric totals and valid-record denominators

These are arithmetic summaries of the stored row-level values for reconciliation. Summing exposure percentages is not necessarily a meaningful overall exposure score; the row-level mean is the unweighted mean over occupations or task records, respectively.

| Dataset / metric | Valid records before → after | Sum before → after | Mean before → after | Min / max (unchanged) |
|---|---:|---:|---:|---:|
| `job_exposure.csv` / `observed_exposure` | 756 → 756 | 58.1944 → 58.1944 | 0.0769767196 → 0.0769767196 | 0.0 / 0.7451 |
| `task_penetration.csv` / `penetration` | 17,998 → 17,998 | 1,201.2546 → 1,201.2546 | 0.0667437826 → 0.0667437826 | 0.0 / 1.0 |

Every reported metric value converted successfully and was nonmissing, so the valid-record denominator equals the row count for each metric. If a future value fails conversion or is missing, it must not enter a numeric sum or average; report the excluded/failed count and compute the average denominator from valid parsed values only. No such exclusions occurred here.

## Suspicious values retained

- `observed_exposure`: 411 of 756 values are zero (54.4%).
- `penetration`: 16,644 of 17,998 values are zero (92.5%).
- The high zero shares are flagged for source-methodology review, not classified as errors and not changed.
- The task file has repeated text and exact duplicates; their row meaning remains unresolved, so they remain in the cleaned output and in the metric denominator.

No unresolved cleaning decisions were applied. See `cleaning_decision_log_updated.md` for the approved rules and execution audit.
