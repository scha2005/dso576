# Cleaning AI workforce data

Use Python 3.10 or newer. The cleaning code uses only the standard library, as recorded in `requirements.txt`. The script locates inputs relative to itself and leaves both original CSV files unchanged.

Run the complete pipeline from this folder:

```text
python clean_data.py
```

On this Windows machine, use `python3.14 clean_data.py` if `python` resolves to the unavailable Microsoft Store alias.

For a guided review, open `cleaning_notebook.ipynb` with this folder as the working directory and choose **Restart / Run All**. The notebook inspects the originals, invokes the same script, reconciles the outputs, and asserts all five record checks.

## Submission metadata

- Branch: `Allen`
- Branch URL: <https://github.com/scha2005/dso576/tree/Allen>
- Cleaning submission commit: pending final commit and push. The current branch head, `6d88b60720007a066dfd92fa61875703b8b2c7bc`, predates the cleaning work and should not be submitted as the cleaning commit.

## Scope and rules

The analysis compares observed AI exposure across occupations and describes task penetration. One job row represents an occupation identified by the text `occ_code`; one cleaned task row represents a distinct, case-sensitive task description. These scores do not establish job displacement or causation.

Rules established after inspecting the inputs, before applying changes:

| Rule | Reason | Check |
|---|---|---|
| Preserve originals and record SHA-256 hashes | Make inputs identifiable and changes reproducible | Check source hashes after processing |
| Keep occupation codes as strings matching two digits, a hyphen, and four digits | Preserve identifier formatting | Validate every code |
| Trim only outer whitespace | Remove accidental padding without changing wording | Record every changed row; none found in current inputs |
| Validate scores as finite decimal numbers in [0, 1]; preserve original numeric precision | Avoid rounding or treating zero as missing | Stop on failed conversions or invalid ranges |
| Retain one occurrence of each exact row | Define a unique-task analytical table without overweighting repeated descriptions | Audit each removed record and reconcile counts and score sums |
| Preserve case and punctuation | No authoritative task ID or mapping establishes equivalence | Retain both “Web” and “web” variants |
| Stop on missing fields, malformed records, or conflicting repeated keys | Do not invent values or choose an arbitrary score | Full-file validation before writing outputs |
| Keep tables separate | There is no shared join key | No merge attempted |

The task deduplication rule is an analytical choice. Repetitions might originate from occupation-specific records upstream, but these files contain no occupation-to-task mapping. Use the original data if occurrence weighting is intended; do not infer occupation relationships from matching text.

## Outputs and verification

Expected outputs in `cleaned/` are:

- `job_exposure_clean.csv` and `task_penetration_clean.csv`
- `job_exposure_sample.csv` and `task_penetration_sample.csv` (25 rows each)
- `cleaning_audit.csv`
- `validation.json`
- `record_checks.json`

Audit record numbers count data records starting at 1, excluding the header.

The sample includes the zero-exposure Legislators row, the highest-exposure Computer Programmers row, a task with penetration 1, and both repeated task descriptions. Remaining sample slots use source order. Five record checks compare source-derived expectations with cleaned rows and retained counts.

The validation report gives full-file missing counts, duplicate counts, row counts, score ranges, zeros, sums, and unweighted means before and after cleaning. Zeros are included in denominators. Missing scores or group keys stop the run; no imputation occurs. Score sums are reconciliation checks, not estimates of aggregate economic impact. There are no date columns.

## Source and limitations

The files come from Anthropic's **Labor market impacts of AI** data release dated March 5, 2026, within the Anthropic Economic Index. They were accessed on October 4, 2026. The local files were checked byte-for-byte against the official revision for each file:

- `job_exposure.csv`: [official revision `7a1cc3c`](https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/7a1cc3c/labor_market_impacts/job_exposure.csv), SHA-256 `4f0a3adf5feeb2ec5f5d02ab18cc5e851a2a4b8470bde84c0c9335017be12d68`
- `task_penetration.csv`: [official revision `01eb1d0`](https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/01eb1d0/labor_market_impacts/task_penetration.csv), SHA-256 `85bee872db1d55d3e9a7f4e89da5ae4a5d59aa8ec875d728fbf4b7d820984616`

This cleaning work does not resolve differences between differently worded or capitalized tasks, provide occupation/task mappings, or validate how upstream scores were constructed. No out-of-range scores or missing values were observed in the supplied files.
