# AI Workforce Priority Dashboard - Build Specification

## 1. Current vision

The dashboard serves workforce-planning, HR, and organizational strategy leaders deciding which occupations merit AI enablement, employee training, workflow redesign, or additional governance. It combines observed Claude usage from the Anthropic Economic Index with O*NET task mappings and BLS labor-market data. It improves on exposure-only rankings by showing workforce scale and separating augmentation from automation instead of treating exposure as replacement risk.

Phase 2 supplies the canonical data and reusable analysis functions. Phase 3 builds the interactive interface.

## 2. Core use cases

1. User selects an occupation group and labor-market thresholds -> dashboard shows occupations ranked by Implementation Priority Score with exposure, employment, growth, and openings -> user decides which occupations deserve deeper assessment.
2. User selects an occupation -> dashboard shows augmentation share, automation share, dominant mode, and tasks driving observed use -> user decides whether to emphasize training, workflow redesign, or governance.
3. User selects occupations to compare -> dashboard shows side-by-side AI and labor-market measures -> user decides which occupation to address first.
4. User selects or hovers over a score -> dashboard shows normalized components and weighted contributions -> user verifies why the occupation ranks where it does.
5. User opens an occupation drill-down and sorts tasks -> dashboard shows task penetration and mode -> user identifies candidate tasks for pilots or human-review controls.

Every MVP feature must support one of these use cases.

## 3. Canonical datasets

### data/processed/occupation_dashboard.csv

Grain: exactly one row per six-digit SOC occupation.

Required definitions:

| Column | Definition |
|---|---|
| soc_code | Six-digit SOC code formatted NN-NNNN |
| occupation_title | Canonical Anthropic/O*NET title |
| bls_title | BLS title retained for auditing |
| major_group_code | Two-digit major occupation group |
| major_group_title | Major occupation group label |
| observed_exposure | Anthropic observed exposure, proportion 0-1 |
| mapped_task_count | Number of mapped occupation-task rows |
| positive_penetration_task_count | Count of mapped tasks with penetration above zero |
| positive_penetration_task_pct | Positive task count divided by mapped task count |
| mean_task_penetration | Mean mapped-task penetration |
| augmentation_share | Penetration-weighted documented augmentation interaction share, 0-1; missing if unsupported denominator is zero |
| automation_share | Penetration-weighted documented automation interaction share, 0-1; missing if unsupported denominator is zero |
| dominant_mode | augmentation, automation, balanced, or missing |
| employment_base_year | BLS base-year employment count |
| employment_projection_year | BLS projected employment count |
| employment_change_numeric | Projected employment change in workers |
| employment_growth_pct | BLS projected percentage change |
| annual_openings | BLS average annual openings |
| median_annual_wage | BLS median annual wage in dollars |

Optional: typical_education, related_work_experience, on_the_job_training.

### data/processed/occupation_tasks.csv

Grain: one row per valid occupation-task relationship.

Required definitions:

| Column | Definition |
|---|---|
| onet_soc_code | Full O*NET-SOC code |
| soc_code | Six-digit SOC parent code |
| occupation_title | Occupation title |
| task_id | Required stable O*NET task identifier |
| task | Original task statement |
| task_normalized | Deterministically normalized task text used for auditing joins |
| penetration | Anthropic task penetration, 0-1 |
| augmentation_share | Sum of Anthropic task ratios for validation, task_iteration, and learning |
| automation_share | Sum of Anthropic task ratios for directive and feedback_loop |
| dominant_mode | Task-level dominant mode when both shares exist |

The task table also retains `mode_source_task_name` and the six original source ratio columns (`feedback_loop`, `directive`, `task_iteration`, `validation`, `learning`, `filtered`) for audit. The Anthropic release README defines directive and feedback loop as automation patterns; validation, task iteration, and learning as augmentation patterns; and filtered as excluded. These six proportions are exhaustive, but filtered is excluded from both mode shares, so augmentation plus automation equals `1 - filtered`, not necessarily one. Mode-source rows join using deterministic normalized task text; unmatched tasks remain missing. No fuzzy matching is used.

The cleaning pipeline, this specification, backend code, cleaning prompt, and automated tests must use these exact definitions. A schema or metric change is incomplete until all are updated together.

### Required columns and keys

Every field listed in either canonical schema table is a required column, even when some row values may be unavailable and therefore missing. The occupation-task primary key is `(onet_soc_code, task_id)`; both parts must be present and nonblank. `soc_code`, `onet_soc_code`, `task_id`, `task`, and `task_normalized` cannot be null, blank, or whitespace-only. `soc_code` must match `NN-NNNN`, and `onet_soc_code` must match `NN-NNNN.NN`. Task identifiers must be unique within each detailed O*NET-SOC code.

Task count columns `mapped_task_count` and `positive_penetration_task_count` must be finite nonnegative whole numbers, with positive count no greater than mapped count. When mapped count is positive, `positive_penetration_task_pct` must equal positive count divided by mapped count within absolute tolerance `1e-9`. When mapped count is zero, positive count must be zero and positive percentage must be missing. `mean_task_penetration` and task percentage, when present, remain within 0–1.

## 4. Metric definitions

### Observed exposure

Use observed_exposure from the cleaned Anthropic occupation file. It measures observed AI exposure, not probability of job loss.

### Positive-penetration task percentage

positive_penetration_task_pct = count(tasks where penetration > 0) / mapped_task_count. Return missing if mapped_task_count is zero; in that case both task counts are zero.

### Occupation mode shares

For each occupation, calculate each mode share as `sum(penetration * task_mode_share) / sum(penetration)` over mapped tasks that have both documented mode shares. Return both shares missing if this supported denominator is zero. Tasks without source matches do not enter the mode denominator; task counts and penetration summaries still use all mapped tasks. Do not force the mode shares to sum to one: filtered interactions are excluded from both.

### Dominant mode

- augmentation when augmentation exceeds automation by more than 0.005;
- automation when automation exceeds augmentation by more than 0.005;
- balanced when their absolute difference is at most 0.005;
- missing when either share is unavailable.

### Implementation Priority Score

This answers: Where should a workforce leader investigate AI implementation first, given observed usage and workforce scale? It is not a risk, displacement, or replacement score.

Among currently eligible occupations, calculate pandas percentile ranks with method=average and pct=True:

- 45% observed-exposure percentile;
- 25% base-year-employment percentile;
- 15% projected-growth percentile;
- 15% annual-openings percentile.

priority_score = 100 times the weighted sum.

Rules:

- Higher values always increase priority.
- Recompute after major-group and numeric eligibility filters.
- All four inputs are required; otherwise the score and rank are missing and priority_score_available is false.
- Display one decimal but retain unrounded values.
- Ties remain tied in score. Table order then uses exposure descending, employment descending, and title ascending.
- Augmentation and automation do not enter the score. They determine the intervention after prioritization and must remain prominent.
- Expose each percentile and weighted contribution.

## 5. Starting view

- All major groups; no numeric or mode restrictions.
- Default full ranking includes only occupations with available scores.
- Sort by priority score descending.
- Default Top N is 25 for `ranking_visual`; `ranking` always contains the complete eligible ranking.
- Select the highest-ranked occupation.
- Show source/version notes and a warning that exposure is not job-loss risk.

Summary cards: occupation count, median exposure, represented employment, and median projected growth.

Main ranking table: rank, occupation, group, score, exposure, employment, growth, openings, wage, and dominant mode.

Overview visuals:

- horizontal bars for top priority scores, based on `ranking_visual`;
- scatterplot of exposure versus growth, sized by employment and colored by dominant mode where available;
- stacked mode bars that include `filtered_share = 1 - augmentation_share - automation_share` for rows with both measured shares; leave the residual missing when mode data is unavailable.

Drill-down: occupation identity, score, labor metrics, mode shares, score components, and a task table ordered by penetration.

## 6. Filters and interactions

| Control | Default | Effect |
|---|---|---|
| Major occupation group | All | Filters all overview outputs |
| Occupation search | Blank | Filters ranking by title or SOC |
| Minimum employment | None | Restricts eligible occupations |
| Growth range | All | Restricts eligible occupations |
| Exposure range | All | Restricts eligible occupations |
| Dominant mode | All | Filters known modes where source coverage exists |
| Include incomplete scores | Off | Reveals unranked incomplete rows |
| Top N | 25 | Limits ranking visual only |
| Reset | Available | Restores defaults |

Selecting a row or chart mark updates the drill-down. Filter changes recompute percentiles and scores within the eligible set. Selecting an occupation does not change filters.

Filter arguments are validated before filtering. Growth and exposure ranges contain exactly two bounds; either bound may be `None`, but supplied bounds must be finite numeric values and minimum cannot exceed maximum. Exposure bounds must be in [0, 1]. Minimum employment must be finite and nonnegative. Dominant modes may contain only `augmentation`, `automation`, and `balanced`; rows without known dominant mode are excluded only when this filter is applied. An empty dominant-mode list means no mode filter. Invalid filters raise an actionable error. `top_n` must be a positive integer or `None`.

## 7. Backend contracts

The UI calls backend_analysis.py and never reimplements metric logic.

| Function | Output |
|---|---|
| load_occupation_data | Validated occupation dataframe |
| load_task_data | Validated task dataframe |
| filter_occupations | Filtered eligible dataframe |
| add_priority_score | Percentiles, contributions, availability, score |
| rank_occupations | Sorted ranked dataframe |
| calculate_summary_metrics | KPI dictionary |
| get_mode_breakdown | Chart-ready augmentation, automation, dominant mode, and documented filtered residual |
| get_exposure_growth_scatter | Chart-ready scatter dataframe |
| get_occupation_detail | Occupation metrics, components, and tasks |
| get_task_drilldown | Sorted task dataframe |
| validate_spec_alignment | Validation report or actionable exception |

`build_dashboard_outputs` returns `ranking` with every eligible ranked row and `ranking_visual` with at most `top_n` rows. `top_n=None` makes `ranking_visual` a copy of the full ranking. Summary metrics use all filtered eligible occupations, not the visual subset. Functions do not print or depend on UI state. Inputs are explicit; outputs are dataframes or dictionaries.

## 8. Architecture and technical design

Raw sources -> reproducible cleaning/join pipeline -> canonical processed CSVs -> backend_analysis.py -> Phase 3 dashboard.

- Python and pandas handle cleaning and analysis.
- Phase 3 may use Streamlit unless the repository specifies another framework.
- Load processed data once; the UI may cache it.
- Backend code remains framework-independent.
- Missing metrics stay missing and display as unavailable.
- Malformed schemas, duplicate occupation keys, invalid ranges, and bad SOC codes fail clearly.
- Components communicate only through documented schemas and parameters.

## 9. Build order

1. Reconcile source versions and cleaning decisions.
2. Produce canonical processed datasets.
3. Run schema and join audits.
4. Implement and test backend functions.
5. Hand-check selected occupation results.
6. Build shell and starting view.
7. Add filters and score recomputation.
8. Add ranking and overview visuals.
9. Add occupation/task drill-down.
10. Add definitions, sources, and limitations.
11. Run acceptance checks.

## 10. Acceptance checks

1. A clean run creates or loads both datasets without manual path edits.
2. Occupation data has exactly one row per valid soc_code.
3. Every metric uses this file's definition and units.
4. Missing required columns cause an actionable failure.
5. A four-row fixture matches hand-calculated scores and contributions.
6. Eligibility-filter changes recompute percentiles and may change rankings.
7. Reset restores defaults.
8. Selecting an occupation returns only that SOC code's tasks.
9. Tasks sort by penetration descending.
10. Mode shares are never described as displacement probabilities.
11. Missing BLS values do not become zeros.
12. Score-incomplete occupations receive no score or rank.
13. All visuals reconcile to backend outputs.
14. Source versions and limitations are visible.
15. A fresh coding agent can begin Phase 3 without important guesses.

The Phase 3 source/version note must state that local `job_exposure_cleaned.csv` and `task_penetration_cleaned.csv` have unresolved upstream release dates. Include filenames, dimensions, column names, SHA-256 hashes, known publisher/dataset family, and the exact statement “Upstream release/date not independently verified.” Do not present local filesystem timestamps as publisher release dates.

## 11. Limitations displayed in the product

- Anthropic data reflects observed Claude usage, not all AI tools or workers.
- Exposure is not automation, displacement, or job loss.
- Task mapping and occupational crosswalks can be imperfect.
- BLS projections are estimates.
- Score weights are policy choices and must be transparent.
- Missing-input occupations may be excluded from rankings but can remain visible.


## Missing-value handling

Missing values may remain in canonical data when a documented source or coverage limitation prevents a value. The BLS literal category None is preserved and mapped field-specifically to No related work experience required or No on-the-job training required; genuinely blank cells remain null. Optional missing metrics do not justify removing an otherwise valid occupation or task. Missing values display as unavailable and are excluded only from calculations that require that field. Never silently convert missing values to zero. See eports/missing_value_audit.csv for counts and documented reasons.

