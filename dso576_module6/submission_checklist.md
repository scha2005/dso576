# DSO 576 Module 6 submission checklist

Statuses below refer to the deliverables and evidence present at the time of this audit. `PASS` means the item is present and supported by the cited artifact or observed result; it does not imply that the notebook was executed.

| # | Checklist item | Status | Evidence or explanation |
|---:|---|---|---|
| 1 | Python cleaning script is included and runs | PASS | `clean_data.py` is present. The workflow completed with exit code 0 using `C:\Users\lutao\AppData\Local\Programs\Python\Python313\python.exe .\dso576_module6\clean_data.py` (PowerShell invocation uses `&` before the quoted executable). The plain `python` alias on this machine fails before script startup; `README.md` gives both the verified command and portable launcher/PATH alternatives. |
| 2 | Notebook documents the workflow | PASS | `data_cleaning.ipynb` contains inspection/decision documentation, a `sys.executable` workflow invocation, and validation assertions. Notebook JSON has six cells. Its code cells have `execution_count: null` and empty outputs: the notebook itself was not executed. |
| 3 | Source metadata and provenance are reported accurately | PASS | `README.md`, the notebook, and `outputs/validation_audit.json` identify the source/version/download-date limitation. No source organization, URL, release/version, download date, data dictionary, or provenance note was supplied; these details are reported as unknown, not invented. |
| 4 | Runtime and dependencies are declared | PASS | `pyproject.toml` declares Python `>=3.9` and `dependencies = []`. `clean_data.py` imports only Python standard-library modules. |
| 5 | Cleaned sample is within the 50-row limit | PASS | `outputs/cleaned_data_sample.csv` contains 15 data rows (16 physical lines including the header). Its construction includes the eight repeated-task records. |
| 6 | Duplicate evidence is correct and consistent | PASS | Original source inspection and `outputs/validation_audit.json` report **2 exact duplicate groups and 6 extra duplicate rows**: four occurrences of the task spelling ending in `Web pages.` and four ending in `web pages.`, each group at penetration `0.7263`. All 8 records are retained. `README.md`, `cleaning_decision_log.md`, and the notebook state this same case-sensitive result and explain that case-folding combines the spellings into one family. |
| 7 | Cleaning decisions and rationale are logged | PASS | `cleaning_decision_log.md` documents text preservation, numeric validation/canonical export, keeping rows and zeros, retaining unresolved repeats, no imputation, and no merge, with rationale and verification checks. |
| 8 | Validation/audit output is present | PASS | `outputs/validation_audit.json` records source metadata limitation, schemas, before/after rows and missingness, duplicate details, numeric conversion/ranges/statistics, relationship, and record-check summary. The successful workflow generated this file. |
| 9 | Dataset relationship is handled without an unsupported merge | PASS | The source headers have no common identifier or documented crosswalk. `outputs/validation_audit.json` records `merge_performed: false` and `shared_defensible_key: null`; `README.md` explains why no merge was done. |
| 10 | Before/after row counts are checked and explained | PASS | The audit records job exposure 756 before and after, and task penetration 17,998 before and after. Counts stay unchanged because the workflow validates and canonicalizes numeric values into separate outputs while preserving every input row; it does not filter or deduplicate records. |
| 11 | Zero and missing-value treatment is documented | PASS | The decision log and README state that all rows and zero values are retained and no missing values are imputed. The audit reports zero missing values in every source/output column; numeric summaries report 411 job zeros and 16,644 task zeros before and after. |
| 12 | Five individual record checks include all required fields | PASS | `outputs/record_checks.csv` has five rows: retained zero, observed job maximum, the `Web` repeated-task case, the `web` capitalization case, and maximum task penetration. Each row includes original value, expected result, actual cleaned result, and `matches`; all five are `True`. |
| 13 | Reproducibility evidence comes from successful execution and exact output comparison | PASS | `outputs/reproducibility_check.json` was written by the successful script run. The script reruns in a temporary directory from `data/raw/job_exposure.csv` and `data/raw/task_penetration.csv` and compares SHA-256 hashes of both cleaned CSVs, the sample, record checks, and validation audit; all five comparisons are `true`, and `passed` is `true`. This is script execution evidence only; the notebook was not executed. |
| 14 | Remaining limitations are clearly documented | PASS | `README.md` and the notebook limitations section identify unknown provenance/version/date, unexplained repeated records, no defensible merge key, CSV numeric typing, and the notebook's unexecuted status. The run command note also documents the local WindowsApps alias issue and the verified executable command. |

## Deliverable inventory

| Deliverable | Location | Status |
|---|---|---|
| Cleaning script | `clean_data.py` | PASS |
| Notebook | `data_cleaning.ipynb` | PASS; not executed |
| Cleaned data sample (15 rows) | `outputs/cleaned_data_sample.csv` | PASS |
| Dependency/runtime file | `pyproject.toml` | PASS |
| README | `README.md` | PASS |
| Cleaning decision log | `cleaning_decision_log.md` | PASS |
| Validation/audit output | `outputs/validation_audit.json` | PASS |
| Five record checks | `outputs/record_checks.csv` | PASS; 5/5 match |
| Reproducibility evidence | `outputs/reproducibility_check.json` | PASS; 5/5 output hashes match |
| 14-item checklist evidence | `submission_checklist.md` | PASS |

The originals copied to `data/raw/` are byte-for-byte unchanged from the supplied CSVs. The notebook execution status above is the only execution limitation; it is stated explicitly and is not represented as a successful notebook run.
