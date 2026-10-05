# Manual Verification Results

Expected values below are unchanged from the pre-run verification sample. The approved cleaning workflow was rerun using only the original CSVs. Actual values were read from the generated cleaned outputs. `Match: Yes` means actual agrees with the previously recorded expectation.

| Record identifier | Why it is difficult or important | Original value | Expected value (pre-run) | Actual value | Match: Yes or No | Explanation of any mismatch |
|---|---|---|---|---|---|---|
| `job_exposure.csv`, CSV line 2 (`occ_code=11-1011`) | Text/type preservation: identifier contains punctuation and must not be parsed or reformatted. | `occ_code="11-1011"`; `title="Chief Executives"`; `observed_exposure="0.0333"` | Same code `11-1011` and same other field values. | `occ_code="11-1011"`; `title="Chief Executives"`; `observed_exposure="0.0333"` | Yes | None. |
| `task_penetration.csv`, CSV line 17,891 (repeated task record) | This exact row occurs four times; duplicate removal is unresolved. | `task="Write interesting and effective press releases, prepare information for media kits, and develop and maintain company internet or intranet Web pages."`; `penetration="0.7263"` | All four identical occurrences remain, including this occurrence. | Four identical occurrences remain; this row is present at line 17,891 with `penetration="0.7263"`. | Yes | None. |
| `job_exposure.csv`, CSV line 4 (`occ_code=11-1031`) — negative control | Missing-value handling: observed exposure is zero. There are no actual missing values in either source file. | `occ_code="11-1031"`; `title="Legislators"`; `observed_exposure="0.0"` | The row remains with exposure `0.0`. This tests zero preservation and row retention, but cannot test a truly blank value. | `occ_code="11-1031"`; `title="Legislators"`; `observed_exposure="0.0"`; row present. | Yes | None. Actual blank-value behavior remains untested because the source contains no missing values. |
| Merge probe: `job_exposure.csv`, CSV line 2 (`occ_code=11-1011`) and `task_penetration.csv`, CSV line 2 | The job row has an occupation code; the task row has no occupation code or title. These are probes, not an asserted relationship. | Job: `occ_code="11-1011"`, `title="Chief Executives"`; task: `task="Accept and check containers of mail from large volume mailers, couriers, and contractors."`, `penetration="0.0"`; no task-side job key. | No valid match should be produced; leave the task unassigned because it has no merge key. | No merge was performed. The task row has only `task` and `penetration`; it remains unassigned. | Yes | None. An occupation match cannot be evaluated without a documented task-side key or crosswalk. |
| `task_penetration.csv`, CSV line 343 | Boundary case at the upper endpoint of the observed 0–1 range. | `task="Advise customers on use and care of merchandise."`; `penetration="1.0"` | Preserve value `1.0`; do not clamp or rescale it. | `task="Advise customers on use and care of merchandise."`; `penetration="1.0"` | Yes | None. |

## Verification notes

- All five checks matched the pre-run expectations; no mismatches were found.
- The workflow output is value-identical to the original source data. The duplicate, zero, and boundary values remain unchanged.
- The merge check verifies the absence of a task-side occupation key; it does not validate a job-to-task relationship.
- The missing-value check is a negative control only. Testing a true missing value would require a separate synthetic fixture, not a change to the source files.
