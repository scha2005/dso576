# Submission Sample

Created: 2026-10-05T01:12:17-07:00

This submission sample contains **48 cleaned data rows total** (maximum allowed: 50), split by original dataset grain.

## Sample files

- [`job_exposure_sample.csv`](job_exposure_sample.csv): 23 rows; original job columns retained.
- [`task_penetration_sample.csv`](task_penetration_sample.csv): 25 rows; original task columns retained.
- [`sample_manifest.csv`](sample_manifest.csv): source line, category, and selection rationale for every sample row.

The sample was generated from `project/cleaned/` by `project/create_submission_sample.py`. It does not join the two datasets and does not add synthetic values.

## Why difficult records were selected

| Sample file and source CSV line | Selected record / challenge | Reason selected |
|---|---|---|
| `job_exposure_sample.csv`, line 2 | `11-1011` (manual verification / identifier) | Preselected text-preservation check: retain occ_code 11-1011 exactly as text. |
| `job_exposure_sample.csv`, line 4 | `11-1031` (manual verification / zero negative control) | Preselected missingness negative control: complete record with observed_exposure 0.0; no source row is missing. |
| `job_exposure_sample.csv`, line 75 | `15-1251` (unusual valid value) | High observed_exposure value (0.7451); retained as a valid observed value. |
| `task_penetration_sample.csv`, line 2 | `Accept and check containers of mail from large volume mailers, couriers, and contractors.` (manual verification / merge-key probe) | Preselected merge probe: task record has no occupation code or title; do not assign it to a job. |
| `task_penetration_sample.csv`, line 343 | `Advise customers on use and care of merchandise.` (manual verification / upper boundary) | Preselected upper-bound record: penetration is 1.0 and is retained unchanged. |
| `task_penetration_sample.csv`, line 17891 | `Write interesting and effective press releases, prepare information for media kits, and develop and maintain company internet or intranet Web pages.` (manual verification / exact duplicate group) | First instance of an exact repeated task row; all occurrences are retained. |
| `task_penetration_sample.csv`, line 17892 | `Write interesting and effective press releases, prepare information for media kits, and develop and maintain company internet or intranet Web pages.` (exact duplicate group) | Second identical occurrence; demonstrates duplicate retention. |
| `task_penetration_sample.csv`, line 17893 | `Write interesting and effective press releases, prepare information for media kits, and develop and maintain company internet or intranet Web pages.` (exact duplicate group) | Third identical occurrence; demonstrates duplicate retention. |
| `task_penetration_sample.csv`, line 17894 | `Write interesting and effective press releases, prepare information for media kits, and develop and maintain company internet or intranet Web pages.` (exact duplicate group) | Fourth identical occurrence; demonstrates duplicate retention. |
| `task_penetration_sample.csv`, line 17895 | `Write interesting and effective press releases, prepare information for media kits, and develop and maintain company internet or intranet web pages.` (capitalization variant / repeated task) | First occurrence of case-only Web/web task-text variant; text is preserved. |
| `task_penetration_sample.csv`, line 17896 | `Write interesting and effective press releases, prepare information for media kits, and develop and maintain company internet or intranet web pages.` (capitalization variant / repeated task) | Repeated occurrence of the case-only task-text variant; text is preserved. |
| `task_penetration_sample.csv`, line 17897 | `Write interesting and effective press releases, prepare information for media kits, and develop and maintain company internet or intranet web pages.` (capitalization variant / repeated task) | Repeated occurrence of the case-only task-text variant; text is preserved. |
| `task_penetration_sample.csv`, line 17898 | `Write interesting and effective press releases, prepare information for media kits, and develop and maintain company internet or intranet web pages.` (capitalization variant / repeated task) | Repeated occurrence of the case-only task-text variant; text is preserved. |

## Coverage notes

- The five manual-verification cases are included: occupation code `11-1011`; the repeated task row; occupation `11-1031` with zero exposure; the task-side merge-key probe; and the task with penetration `1.0`.
- The repeated task group includes all four exact occurrences of each of the `Web` and `web` capitalization variants. Exact duplicate handling remains unresolved, so every occurrence is retained.
- There are no missing or formerly missing source values to sample. The complete zero-valued occupation record is included as a negative control; no synthetic missing values were introduced.
- No occupation-linked task rows or actual merge matches can be supplied: `task_penetration.csv` has no occupation code/title key or documented crosswalk. The task merge probe is retained as an unassigned task record, not falsely matched.
- An upper-bound task penetration of `1.0`, a high occupation exposure value, and several ordinary early-, middle-, and late-file rows are included for comparison.
- The data are occupation/task measures without personal-level records or direct identifiers. Original source values are retained in these samples.
