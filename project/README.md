# AI Workforce Exposure: Individual Data-Cleaning Submission

## Reproducible dashboard data pipeline

The completed Phase 2 pipeline creates `data/processed/occupation_dashboard.csv` and `data/processed/occupation_tasks.csv`. It uses the Anthropic Economic Index release `2025_03_27` O*NET task statements, task mode-category data, and SOC structure, plus the BLS 2025–2035 Occupational Projections workbook (`data/raw/occupation.xlsx`, Table 1.2). Existing local occupation exposure and task penetration inputs are in `cleaned/`.

Required inputs:

- `cleaned/job_exposure_cleaned.csv`
- `cleaned/task_penetration_cleaned.csv`
- `data/raw/onet_task_statements.csv`
- `data/raw/automation_vs_augmentation_by_task.csv`
- `data/raw/SOC_Structure.csv`
- `data/raw/occupation.xlsx`

Source URLs: Anthropic [O*NET task statements](https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/release_2025_03_27/onet_task_statements.csv), [task categories](https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/release_2025_03_27/automation_vs_augmentation_by_task.csv), and [SOC structure](https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/release_2025_03_27/SOC_Structure.csv), release `2025_03_27`; BLS [Occupational Projections and Worker Characteristics](https://www.bls.gov/emp/tables/occupational-projections-and-characteristics.htm), 2025–2035, Table 1.2.

Install dependencies with `python -m pip install pandas openpyxl`. Run the pipeline from the repository root with `python -m src.clean_and_join_data`; run tests with `python -m unittest discover -s tests -v`.

Task matching uses exact normalized descriptions. Unmatched penetration records are written to `reports/unmatched_tasks.csv` and omitted from occupation-task rows. Join coverage, source profiles, unmatched occupation codes, title disagreements, and duplicate-key reviews are under `reports/`. The Anthropic release README documents interaction categories: directive and feedback_loop are automation patterns; validation, task_iteration, and learning are augmentation patterns; filtered interactions are excluded. Canonical task data retains the six source ratios and derived shares; mode shares are not rescaled to sum to one. Matched mode coverage and joins are audited in `reports/`. No priority score is stored.

## Project and business question

**Project vision:** Create a dashboard to assess AI workforce exposure in terms of jobs and tasks.

**Business question:** What jobs have most been affected by AI?

**Main comparison:** Occupation-level observed exposure and task-level penetration. The penetration input has no occupation key on its own; the documented Anthropic O*NET task-statements file provides the task-text bridge. Exact deterministic normalized matching links 87.30% of distinct penetration task descriptions, and unmatched tasks are excluded from the canonical occupation-task dataset and retained for review.

## Data sources and provenance

The team project brief names the [Anthropic Economic Index](https://huggingface.co/datasets/Anthropic/EconomicIndex) as the intended source. The local filenames also match files listed under Anthropic's `labor_market_impacts` folder. The exact release used for these local copies has not been recorded, and the file-level provenance has not been independently verified.

| Local file | Dimensions / columns | SHA-256 | Publisher/dataset family | Provenance status |
|---|---|---|---|---|
| `cleaned/job_exposure_cleaned.csv` | 756 × 3; `occ_code`, `title`, `observed_exposure` | `4f0a3adf5feeb2ec5f5d02ab18cc5e851a2a4b8470bde84c0c9335017be12d68` | Anthropic Economic Index is the intended family, based on project records; file-level provenance is unverified | Upstream release/date not independently verified. Local acquisition date is not known. |
| `cleaned/task_penetration_cleaned.csv` | 17,998 × 2; `task`, `penetration` | `85bee872db1d55d3e9a7f4e89da5ae4a5d59aa8ec875d728fbf4b7d820984616` | Anthropic Economic Index is the intended family, based on project records; file-level provenance is unverified | Upstream release/date not independently verified. Local acquisition date is not known. |

The filenames and project brief suggest Anthropic Economic Index provenance, but this is an inference, not confirmation of the files' source release. Local filesystem timestamps are not treated as acquisition dates.

Do not substitute the local file modified date for a source release or download date.

## Meaning of one row

- **`job_exposure.csv`:** one row contains an occupation code (`occ_code`), occupation title, and `observed_exposure` value. The 756 occupation codes are unique in this file.
- **`task_penetration.csv`:** one row contains a task description and `penetration` value. There are 17,998 rows and 17,992 distinct exact task descriptions. The file has no occupation code or title on its own; the pipeline maps descriptions through O*NET task statements, using exact deterministic normalization and no fuzzy matching. The source-defined row grain remains to be confirmed.

## Original data location and source preservation

Original input files are located in `project/`:

- `project/job_exposure.csv`
- `project/task_penetration.csv`

The cleaning script reads those original files and writes separate files under `project/cleaned/`. It does not overwrite the originals. The execution log records identical source/output SHA-256 hashes for each pair.

My independent verification and acceptance of the `occ_code` text-preservation suggestion is documented in [`occ_code_suggestion_verification.md`](occ_code_suggestion_verification.md).

## Environment setup

From the repository root in Windows PowerShell, with Python 3.11 or later and `uv` available:

```powershell
uv sync --locked
.\.venv\Scripts\Activate.ps1
python --version
```

The repository `pyproject.toml` requires Python 3.11 or later, and `uv.lock` locks the shared course environment. The profiling, cleaning, and sample-generation scripts use Python's standard library; the environment setup above installs the repository's full declared environment.

## Workflow and required execution order

Run these commands from the repository root, in order:

```powershell
# 1. Profile the original CSV files; writes project/data_profile.md.
python project\profile_datasets.py

# 2. Review project/cleaning_decision_log.md and confirm approved statuses.
# 3. Apply the currently approved, lossless rules to the original CSVs.
python project\apply_approved_cleaning.py

# 4. Manually verify the five preselected cases against the cleaned CSVs.
#    Record actual values and matches in project/manual_verification_sample.md.

# 5. Create the submission sample from the cleaned outputs.
python project\create_submission_sample.py
```

The cleaning script currently applies only the approved rules: preserve `occ_code` as text, and retain rows without missing/date changes when there are no missing values or date columns. It leaves unresolved numeric conversion, duplicate handling, normalization, and merge decisions unchanged. The reconciliation report is a saved report, not generated by one of these commands; review `project/cleaned/reconciliation_report.md` after running the workflow.

## Expected outputs

### Profiling

- `project/data_profile.md`

### Cleaning

- `project/cleaned/job_exposure_cleaned.csv`
- `project/cleaned/task_penetration_cleaned.csv`
- `project/cleaned/cleaning_decision_log_updated.md`

Current recorded results: 756 job rows and 17,998 task rows before and after; no rows or values changed; 0 missing values in every column; 0 exact duplicate job rows and 6 exact duplicate task rows retained.

### Reconciliation and manual verification

- `project/cleaned/reconciliation_report.md`
- `project/manual_verification_sample.md`

The manual verification table currently records 5 of 5 cases matching their pre-run expectations. The merge probe is a no-key case, not an occupation-task match.

### Submission sample

- `project/submission_sample/job_exposure_sample.csv`
- `project/submission_sample/task_penetration_sample.csv`
- `project/submission_sample/sample_manifest.csv`
- `project/submission_sample/README.md`

The reproducible sample has 48 cleaned rows total: 23 occupation rows and 25 task rows. It retains each dataset's original columns and keeps the files separate so the sample does not imply a join that the source files cannot support. It deliberately includes the five manual verification cases, repeated task rows and capitalization variants, zero and upper-bound values, a high exposure value, and ordinary records for comparison. There are no missing or formerly missing source records to include; no synthetic missing values were introduced.

## Known limitations

- The exact Anthropic release/version and download date for these local files are unknown. File-level source attribution is not independently verified.
- The task file has no occupation code/title key by itself. Occupation-task links are obtained through O*NET task text; 87.30% of distinct penetration descriptions match, while 2,284 unmatched input rows remain in the unmatched-task report and are excluded from canonical tasks.
- The task row grain and meaning of repeated task rows are not confirmed. Six exact duplicate rows and six repeated task-text occurrences were retained; duplicate removal remains unresolved.
- Two task descriptions differ only in `Web`/`web` capitalization. Text normalization remains unresolved, and both forms were retained.
- The observed exposure metric has 411 zeros among 756 records (54.4%); task penetration has 16,644 zeros among 17,998 records (92.5%). The workflow flags these concentrations for source-methodology review and does not treat them as errors.
- There are no missing values in either source, so true blank-value handling was not empirically tested. The selected zero-valued occupation row is only a negative control.
- Metric sums and means are arithmetic summaries of available row values. The task mean is not an occupation-weighted metric, and summing row-level exposures is not necessarily meaningful as an overall exposure score.

## Git submission details

- **Exact local branch name:** `Sumedha`
- **Branch URL:** https://github.com/scha2005/dso576/tree/Sumedha
  - Constructed from the configured `origin` remote (`https://github.com/scha2005/dso576.git`) and the local branch name. Remote publication/existence of this branch was not verified; confirm after pushing.
- **Submitted commit ID:** **[ENTER the commit ID submitted for grading]**
  - The current checkout HEAD observed while preparing this README was `6d88b60720007a066dfd92fa61875703b8b2c7bc`; it is not claimed to be the submitted commit. Enter the final submitted commit only after committing and submitting the work.
