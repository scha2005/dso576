# AI Workforce Priority Dashboard

An interactive dashboard for workforce strategy, HR, and organizational planning teams deciding which occupations merit closer review for AI enablement, employee training, workflow redesign, or governance. Its rankings help prioritize investigation; they are not predictions of job loss or automation.

## Links

- **App:** [Source (`app.py`)](app.py) · [Run locally](#run-locally). No public deployment URL is currently recorded.
- **Demo video:** No shareable recording link is currently available. The [demo script](demo_video_script.md) is provided.
- **Repository:** [dso576 project](https://github.com/scha2005/dso576/tree/Sumedha)

## Run locally

From this `project` directory, with Python 3.11 or later:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit. The app expects the canonical files in `data/processed/` to be present.

## Data scope and sample disclosure

The dashboard uses `data/processed/occupation_dashboard.csv` (756 occupations) and `data/processed/occupation_tasks.csv` (16,687 mapped occupation-task rows). These combine observed Claude usage/exposure inputs associated with the Anthropic Economic Index, O*NET task statements and task interaction categories, and BLS 2025–2035 occupational projections (Table 1.2). The local observed-exposure and task-penetration inputs have **48 rows total in the separately supplied cleaning sample** (23 occupation and 25 task rows); **that sample is not what the dashboard loads**. The app uses the canonical processed datasets above.

Task descriptions are matched deterministically to O*NET descriptions. 87.30% of distinct penetration descriptions matched; unmatched rows are excluded from the dashboard’s mapped task data and retained in the [data quality report](reports/data_quality_report.md). See the [build specification](BUILD_SPEC.md) for data definitions.

## Current limitations

- Observed exposure reflects Claude usage in the source data, not every AI tool, worker, or workplace; exposure is not a measure of displacement.
- The task mapping is incomplete, and the original local Anthropic input release dates and file-level provenance are unverified.
- BLS projections are estimates. The implementation-priority score uses chosen weights (45% exposure, 25% employment, 15% projected growth, 15% annual openings) and percentile ranks within the currently filtered occupations; it is an investigation aid, not a risk score.
- Augmentation and automation shares cover documented task interactions and can sum to less than 100%; missing support is unavailable, not zero.
