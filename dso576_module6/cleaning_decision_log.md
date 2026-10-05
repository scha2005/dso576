# Cleaning decision log

| Issue/rule | Reason | Rows affected | Verification check |
|---|---|---:|---|
| Preserve `occ_code` as text | It is an occupation code, and leading zeros/categorical form must not be numerically reinterpreted. | 756 | Compare all output strings to source strings; verify `occ_code` remains unique. |
| Preserve `title` as text | Labels are descriptive text. | 756 | Source/output value comparison; no blank or trim anomalies observed. |
| Validate `observed_exposure` as finite numeric; write canonical number to separate output | Supports numeric analysis while preserving original file. | 756 | Conversion failure count 0; compare row count, range, mean, median, and sum before/after. |
| Keep all job rows and zero exposure values | User-approved; zero may be a valid value and no duplicate rows were found. | 756 retained; 427 zero-valued records in the initial inspection | Before/after rows equal; zero count and exact duplicate count compared. |
| Preserve `task` as text | Task descriptions are labels, not numeric data. | 17,998 | Compare source/output values; check blank and whitespace counts. |
| Validate `penetration` as finite numeric; write canonical number to separate output | Supports numeric analysis while preserving original file. | 17,998 | Conversion failure count 0; compare row count, range, mean, median, and sum before/after. |
| Keep all task rows and zero penetration values | User-approved; values may be valid and no evidence supports deletion. | 17,998 retained; 16,644 zero-valued records in initial inspection | Before/after rows equal; zero count and exact duplicate counts compared. |
| Retain repeated task records pending source documentation | Case-sensitive inspection of the original finds two exact task strings: `Web` occurs 4 times and `web` occurs 4 times; all 8 values are 0.7263. There are 2 exact task/penetration groups and 6 extra rows. Case-folding combines the strings into one 8-row family. An earlier inspection mistakenly reported one exact group of 8 because it grouped case-insensitively. Whether the repeats are erroneous is unknown. | 8 records (2 exact groups; 6 extra rows) | Audit exact spellings, pair counts, row positions, penetration frequencies, and retained output rows. |
| Do not merge datasets | No shared identifier or documented crosswalk exists in the files. | N/A | Confirm source headers and document no merge performed. |
| No missing-value imputation | No missing values were observed in either file. | 0 | Compare per-column missing counts before/after. |
