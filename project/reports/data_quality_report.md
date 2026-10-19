# Data quality and pipeline report

## Execution

Pipeline completed. Source files are preserved. The BLS workbook supplied in `data/raw/occupation.xlsx` was read from Table 1.2. Employment counts, employment changes, and annual openings were converted from thousands to actual workers by multiplying by 1,000 and rounding to whole workers. Employment growth remains in BLS percentage points (for example, 3.2 means 3.2%). Dashes and suppressed/non-numeric values were left missing.

Detailed dimensions, columns, dtypes, missing counts, duplicate counts, and first five rows for every input are in [input_profiles.md](input_profiles.md).

## Exact task matching

Matched normalized strings case-insensitively after Unicode normalization, whitespace collapse, curly quote normalization, and removal of only a final period. No fuzzy matches were used. The input contained 17,998 rows and 17,991 distinct normalized task strings. Exact matches: 15,714/17,998 source rows (87.31%) and 15,707/17,991 distinct task strings (87.30%); unmatched unique input tasks: 2,284; unmatched source rows excluded from canonical tasks: 2,284. Every unmatched row is retained in [unmatched_tasks.csv](unmatched_tasks.csv). Repeated identical (task, penetration) inputs were collapsed for matching; conflicting duplicate task values are preserved for review in [duplicate_key_review.csv](duplicate_key_review.csv) and excluded from the task join.

O*NET task statements expand each confirmed task to its valid occupation-task relationships; output grain and primary key are `(onet_soc_code, task_id)`. Canonical task rows: 16,687, spanning 768 six-digit SOC codes and 15,707 normalized task descriptions.

## Anthropic interaction modes

The source is `data/raw/automation_vs_augmentation_by_task.csv` (3,364 rows × 7 columns; 3,364 unique task names; no missing cells or exact duplicate rows). It contains normalized task text and six ratios, with no task IDs, O*NET-SOC codes, or task counts. Each ratio is between 0 and 1 and the six columns sum to one per row. The official [release README](https://huggingface.co/datasets/Anthropic/EconomicIndex/blob/main/release_2025_03_27/README.md) defines directive and feedback_loop as automation patterns, validation, task_iteration, and learning as augmentation patterns, and filtered as excluded. Accordingly, automation = directive + feedback_loop and augmentation = validation + task_iteration + learning; the source columns are retained on canonical task rows. We do not force the two mode shares to sum to one: their sum equals 1 - filtered.

There is no compatible stable task ID to join on. Exact original task-text matches were 0/3,364 mode keys against penetration and 0/3,364 against O*NET. Deterministic normalized matching links 2,837/3,364 mode keys (84.33%) to penetration tasks and 3,364/3,364 to O*NET. There are no duplicate normalized keys in the mode file. The normalized join covers 3,466/16,687 canonical occupation-task rows; those matched keys expand to multiple valid O*NET relationships without multiplying within the `(onet_soc_code, task_id)` key. Unmatched mode tasks stay missing; no fuzzy matches were used.

The deterministic normalizer produces 0 distinct-text collision key(s) in the mode source, 1 in penetration input, and 1 in O*NET task text. The penetration and O*NET collisions are capitalization variants (`Web`/`web`) under case-insensitive normalization. All are listed in [duplicate_key_review.csv](duplicate_key_review.csv).

Occupation mode aggregation uses penetration-weighted shares over rows where both source-derived mode shares are known. Tasks without a mode-source match are excluded from that denominator but remain included in task counts and penetration statistics. Occupation-level augmentation and automation shares are present for 310/756 occupations (41.01%); task-level shares are present for 3,466/16,687 rows (20.77%). A zero supported penetration denominator remains missing. `dominant_mode` uses the 0.005 tolerance.

## Join audit and coverage

See [join_audit.csv](join_audit.csv) for rows and distinct keys before/after, matched rates, unmatched key counts, duplicate keys, row multiplication, and field-level missingness before, after, and introduced by unmatched keys. The full unmatched keys from both sides are in [unmatched_join_keys.csv](unmatched_join_keys.csv). Summary: task text to O*NET = 15,707/17,991 (87.30%); exposure to task aggregate = 670/756 (88.62%); exposure to BLS = 755/756 (99.87%); exposure to SOC hierarchy = 756/756 (100.00%).

Unmatched occupation keys are in [unmatched_occupation_codes.csv](unmatched_occupation_codes.csv); normalized-title differences are in [title_disagreements.csv](title_disagreements.csv). BLS employment fields have actual worker units. Canonical occupation rows: 756, unique SOC codes: 756; canonical task rows: 16,687, unique `(onet_soc_code, task_id)` keys: 16,687.

## Validation

`backend_analysis.validate_spec_alignment` passed on in-memory frames and after CSV round-trip. `build_dashboard_outputs` smoke test completed. Both output files were byte-identical across two pipeline runs. Occupation exposure, penetration, and any populated mode shares are proportions in [0, 1]; missing values remain missing. No `priority_score` is stored.

## Missing-value audit

The original processed file had 647 missing related-experience values and 296 missing training values. The raw BLS workbook contains 1,037 literal `None` cells; pandas' default Excel NA parsing converted the meaningful categories in these two columns to nulls. The corrected reader preserves literal `None`, maps it field-specifically, and leaves blank cells null. The matched output now has 1 missing value in each of those columns (the unmatched `11-1031` occupation); no valid rows were removed.

The remaining missing fields and counts are documented in [missing_value_audit.csv](missing_value_audit.csv). The four missing wages comprise three BLS em-dash values (Actors, Dancers, Musicians and Singers; suppressed/unavailable) and one unmatched SOC (`11-1031`). Employment and education fields each have one unmatched BLS SOC. The 86 missing task-penetration summary values reflect zero mapped task denominator. Occupation mode shares are unavailable when no supported mode penetration can be calculated. Task mode columns each have 13,221 rows without a matching mode source task. These values are not replaced with zero. Tasks and occupations remain available to calculations that do not require the missing field; mode calculations exclude unsupported mode records and task-count/penetration calculations continue to use mapped tasks.

## Sources and versions

- Anthropic Economic Index release `2025_03_27`: O*NET task statements, automation/augmentation category file, and SOC structure from the release URLs listed in the execution prompt.
- BLS Occupational Projections and Worker Characteristics, 2025–2035, Table 1.2, 2025 National Employment Matrix (workbook in `data/raw/occupation.xlsx`).
- Local input `cleaned/job_exposure_cleaned.csv`: 756 rows × 3 columns (`occ_code`, `title`, `observed_exposure`); SHA-256 `4f0a3adf5feeb2ec5f5d02ab18cc5e851a2a4b8470bde84c0c9335017be12d68`. Known publisher/dataset family: Anthropic Economic Index is indicated by project records; this file-level attribution and version are not confirmed. No defensible local acquisition date is recorded. **Upstream release/date not independently verified.** The family attribution is an inference from project records and naming, not confirmation.
- Local input `cleaned/task_penetration_cleaned.csv`: 17,998 rows × 2 columns (`task`, `penetration`); SHA-256 `85bee872db1d55d3e9a7f4e89da5ae4a5d59aa8ec875d728fbf4b7d820984616`. Known publisher/dataset family: Anthropic Economic Index is indicated by project records; this file-level attribution and version are not confirmed. No defensible local acquisition date is recorded. **Upstream release/date not independently verified.** The family attribution is an inference from project records and naming, not confirmation.

## Reproduction

From repository root: `python -m src.clean_and_join_data`. Tests: `python -m unittest discover -s tests -v`.
