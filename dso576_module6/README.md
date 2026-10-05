# DSO 576 Module 6 Data Cleaning

## Project and source information

The project reads the original files from `dso576_module6/data/raw/job_exposure.csv` and `dso576_module6/data/raw/task_penetration.csv` (relative to the Git repository root). Both are copied into this project unchanged. No source organization, source URL, release/version, download date, data dictionary, or provenance note was supplied. Those details are unknown and are not inferred. See `submission_checklist.md` for itemized evidence.

Branch name, branch URL, and commit ID are not recorded in the supplied project materials.

## Datasets and relationship

- `job_exposure.csv`: 756 rows with `occ_code`, `title`, and `observed_exposure`.
- `task_penetration.csv`: 17,998 rows with `task` and `penetration`.

The datasets have no shared identifier or documented crosswalk. The workflow performs no merge.

## Environment, dependencies, and running

The script requires Python 3.9 or later and uses only the standard library. `pyproject.toml` declares `requires-python = ">=3.9"` and `dependencies = []`; no package installation is needed. From the repository root, run:

```powershell
python .\dso576_module6\clean_data.py
```

The script also works when run from any directory because it resolves its inputs relative to `clean_data.py`; generated files go to `dso576_module6/outputs/` by default. Alternatively, from this project directory run `python .\clean_data.py`.

Verified in this environment from the repository root with the installed Python 3.13 executable:

```powershell
& 'C:\Users\lutao\AppData\Local\Programs\Python\Python313\python.exe' .\dso576_module6\clean_data.py
```

The shorter `python .\dso576_module6\clean_data.py` command was also attempted, but this machine's `python` resolves to an inaccessible WindowsApps alias. On another machine, use its configured interpreter command, for example `python .\dso576_module6\clean_data.py` when Python is on PATH, or `py -3 .\dso576_module6\clean_data.py` when the Python launcher is installed. The notebook invokes the script through the active kernel's `sys.executable` and expects the notebook to be run from the repository root.

The successful script run recreated files in `outputs/`. It validates numeric fields as finite `Decimal` values, writes canonical numeric values to separate outputs, preserves source text and row order, and reruns itself into a temporary directory to compare SHA-256 hashes of deterministic outputs.

## Deliverables

- `clean_data.py`: cleaning and validation workflow.
- `data_cleaning.ipynb`: inspection, decisions, workflow invocation, and validation assertions. It has not been executed; its code cells have no execution results.
- `cleaning_decision_log.md`: approved cleaning rules and their rationale.
- `pyproject.toml`: runtime and dependency declaration.
- `outputs/job_exposure_cleaned.csv` and `outputs/task_penetration_cleaned.csv`: cleaned exports.
- `outputs/cleaned_data_sample.csv`: 15 data rows (16 lines including the header; maximum permitted: 50), including all eight repeated-task records.
- `outputs/record_checks.csv`: five individual original/expected/actual/match checks.
- `outputs/validation_audit.json`: row, missingness, duplicate, type, range, and summary evidence.
- `outputs/reproducibility_check.json`: result of the successful second run and exact SHA-256 comparisons.
- `submission_checklist.md`: status and evidence for each of the 14 checklist items.

## Cleaning decisions and observed duplicates

Preserve identifiers and descriptive text, validate numeric fields as finite values, export canonical numeric values, and retain all rows and zeros. No missing values were observed, so none are imputed. No deduplication or cross-file merge is performed.

Case-sensitive grouping of the original task records finds two exact task/penetration groups: the spelling ending in `Web pages.` occurs four times, and the spelling ending in `web pages.` occurs four times. All eight records have penetration `0.7263`. Therefore the result is **2 exact duplicate groups and 6 extra duplicate rows**, with all 8 records retained. Case-folding combines the two spellings into one family; it does not make them one exact group. The reason for these records is unknown.

## Validation and limitations

The successful run records before/after counts of 756/756 job rows and 17,998/17,998 task rows. Counts are unchanged because the approved workflow validates and canonicalizes numeric values in separate output files while preserving every input record; it does not remove duplicates, zeros, or other rows. Missing counts remain zero.

All five record checks pass: retained job zero, maximum job exposure, each of the two task capitalization spellings, and maximum task penetration. The reproducibility check reran the script from the unchanged original CSVs and compared SHA-256 hashes of the two cleaned CSVs, sample, record checks, and validation audit; all five comparisons passed.

Source provenance, source URL, version, download date, and data dictionary remain unknown. The cause of the repeated task records is unknown. The task text is not a unique key, and there is no defensible cross-file merge key. CSV does not store native numeric types; numeric validity is checked during processing and canonical numeric text is exported. The notebook was not executed, so its assertions are documented but are not execution evidence. See `submission_checklist.md` for the itemized audit.
