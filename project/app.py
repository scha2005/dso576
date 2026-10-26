"""AI Workforce Priority Dashboard. Run with: streamlit run app.py"""

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

import backend_analysis as backend


ROOT = Path(__file__).resolve().parent
OCCUPATION_PATH = ROOT / "data" / "processed" / "occupation_dashboard.csv"
TASK_PATH = ROOT / "data" / "processed" / "occupation_tasks.csv"

st.set_page_config(page_title="AI Workforce Priority Dashboard", page_icon="◉", layout="wide", initial_sidebar_state="expanded")
st.markdown(
    """
    <style>
      .stApp { background: #f5f8f8; color: #172b3a; }
      [data-testid="stSidebar"] { background: #edf3f2; }
      .block-container { padding-top: 1.7rem; max-width: 1500px; }
      .eyebrow { color: #2b7a78; font-weight: 700; letter-spacing: .11em; text-transform: uppercase; font-size: .75rem; }
      .lede { color: #627585; font-size: 1rem; margin-top: -.35rem; }
      [data-testid="stMetric"] { background: white; padding: 1rem; border: 1px solid #dce5e9; border-radius: 12px; }
      div[data-testid="stDataFrame"] { border: 1px solid #dce5e9; border-radius: 10px; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="Loading and validating dashboard data…")
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    occupations = backend.load_occupation_data(OCCUPATION_PATH)
    tasks = backend.load_task_data(TASK_PATH)
    validation = backend.validate_spec_alignment(occupations, tasks)
    return occupations, tasks, validation


def fmt(value: Any, digits: int = 0) -> str:
    if value is None or pd.isna(value):
        return "Unavailable"
    return f"{value:,.{digits}f}"


def pct(value: Any) -> str:
    return "Unavailable" if value is None or pd.isna(value) else f"{value:.1%}"


def occupation_label(row: pd.Series) -> str:
    return f"{row['occupation_title']} · {row['soc_code']}"


def reset_filters() -> None:
    for key in ("groups", "search", "employment_enabled", "minimum_employment", "growth_enabled", "growth_bounds", "exposure_enabled", "exposure_bounds", "modes", "include_incomplete", "top_n"):
        st.session_state.pop(key, None)
    st.rerun()


st.markdown('<div class="eyebrow">Workforce strategy · AI enablement</div>', unsafe_allow_html=True)
st.title("AI Workforce Priority Dashboard")
st.markdown('<div class="lede">Find occupations to investigate first, then see the labor-market context and tasks behind each score.</div>', unsafe_allow_html=True)
st.warning("Observed exposure describes Claude usage in the source data. It is not a measure of automation, displacement, or job-loss risk.")

try:
    occupations, tasks, validation = load_data()
except Exception as exc:
    st.error(f"Dashboard data could not be loaded or validated: {exc}")
    st.stop()

group_options = occupations[["major_group_code", "major_group_title"]].drop_duplicates().sort_values("major_group_code")
group_labels = {row.major_group_code: f"{row.major_group_code} · {row.major_group_title}" for row in group_options.itertuples(index=False)}
growth_min = float(occupations["employment_growth_pct"].min())
growth_max = float(occupations["employment_growth_pct"].max())
exposure_min = float(occupations["observed_exposure"].min())
exposure_max = float(occupations["observed_exposure"].max())

with st.sidebar:
    st.markdown("### Explore occupations")
    if st.button("Reset all filters", use_container_width=True):
        reset_filters()
    selected_groups = st.multiselect("Major occupation groups", list(group_labels), format_func=lambda code: group_labels[code], key="groups", help="Leave blank to include every group.")
    search = st.text_input("Occupation or SOC search", key="search", placeholder="e.g. nurses or 29-1141")
    employment_enabled = st.checkbox("Set minimum employment", key="employment_enabled")
    minimum_employment = st.number_input("Base-year employment", min_value=0, value=100_000, step=10_000, disabled=not employment_enabled, key="minimum_employment", help="Occupations below this level are excluded.")
    growth_enabled = st.checkbox("Filter by projected growth", key="growth_enabled")
    growth_bounds = st.slider(
        "Projected employment growth (%)", growth_min, growth_max,
        (growth_min, growth_max), key="growth_bounds", disabled=not growth_enabled,
    )
    exposure_enabled = st.checkbox("Filter by observed exposure", key="exposure_enabled")
    exposure_bounds = st.slider(
        "Observed exposure", exposure_min, exposure_max,
        (exposure_min, exposure_max), format="%.2f", key="exposure_bounds",
        disabled=not exposure_enabled,
        help="Scale is 0 to 1; for example, 0.25 is 25%.",
    )
    selected_modes = st.multiselect("Dominant mode", ["augmentation", "automation", "balanced"], key="modes", help="Choosing modes excludes occupations with unavailable mode data.")
    include_incomplete = st.checkbox("Include occupations with incomplete scores", key="include_incomplete", help="Incomplete occupations remain visible without a score or rank.")
    top_n = st.slider("Occupations in score chart", 5, 50, 25, key="top_n", help="Limits the chart only; the ranking table contains all eligible rows.")

filters: dict[str, Any] = {
    "major_groups": selected_groups or None,
    "search": search or None,
    "min_employment": minimum_employment if employment_enabled else None,
    "growth_range": growth_bounds if growth_enabled else None,
    "exposure_range": exposure_bounds if exposure_enabled else None,
    "dominant_modes": selected_modes,
}
try:
    eligible = backend.filter_occupations(occupations, **filters)
    ranking = backend.rank_occupations(eligible, top_n=None, include_incomplete=include_incomplete)
    ranking_visual = ranking.head(top_n).copy()
    summary = backend.calculate_summary_metrics(eligible)
    mode_data = backend.get_mode_breakdown(eligible)
    scatter = backend.get_exposure_growth_scatter(eligible)
except Exception as exc:
    st.error(f"Could not apply the selected filters: {exc}")
    st.stop()

st.caption(f"Showing {len(eligible):,} eligible occupations · {int(ranking['priority_score_available'].sum()):,} with complete scores · Validated {validation['occupation_rows']:,} occupations and {validation['task_rows']:,} task rows.")
kpis = st.columns(4)
kpis[0].metric("Occupations analyzed", fmt(summary["occupations_analyzed"]))
kpis[1].metric("Median observed exposure", pct(summary["median_observed_exposure"]))
kpis[2].metric("Employment represented", fmt(summary["employment_represented"]))
growth_kpi = summary["median_projected_growth_pct"]
kpis[3].metric("Median projected growth", f"{fmt(growth_kpi, 1)}%" if pd.notna(growth_kpi) else "Unavailable")

overview_tab, detail_tab, compare_tab, notes_tab = st.tabs(["Overview", "Occupation detail", "Compare", "Definitions & sources"])

with overview_tab:
    score_col, scatter_col = st.columns([1.05, 1])
    with score_col:
        st.subheader("Highest implementation priorities")
        st.caption("Scores are recalculated within the currently eligible set.")
        scored = ranking_visual[ranking_visual["priority_score_available"]]
        if scored.empty:
            st.info("No complete scores match these filters. Adjust a filter or include incomplete scores.")
        else:
            st.bar_chart(scored.set_index("occupation_title")[["priority_score"]], horizontal=True, x_label="Priority score (0–100)")
    with scatter_col:
        st.subheader("Exposure and projected growth")
        st.caption("Point size represents base-year employment.")
        points = scatter.dropna(subset=["observed_exposure", "employment_growth_pct"]).copy()
        if points.empty:
            st.info("No occupations have both exposure and growth data in this view.")
        else:
            points["mode"] = points["dominant_mode"].fillna("Unavailable")
            st.scatter_chart(points, x="observed_exposure", y="employment_growth_pct", size="employment_base_year", color="mode", height=360, x_label="Observed exposure (0–1)", y_label="Projected employment growth (%)")

    st.subheader("Mode shares")
    st.caption("Filtered is the residual excluded from measured augmentation and automation shares.")
    supported = mode_data.dropna(subset=["filtered_share"])
    if supported.empty:
        st.info("Mode shares are unavailable for these occupations.")
    else:
        modes = supported.nlargest(20, "augmentation_share").set_index("occupation_title")[["augmentation_share", "automation_share", "filtered_share"]]
        modes.columns = ["Augmentation", "Automation", "Filtered"]
        st.bar_chart(modes, horizontal=True, stack=True, x_label="Interaction share")

    st.subheader("Eligible occupation ranking")
    table = ranking[["rank", "occupation_title", "soc_code", "major_group_title", "priority_score", "observed_exposure", "employment_base_year", "employment_growth_pct", "annual_openings", "median_annual_wage", "dominant_mode"]].rename(columns={
        "rank": "Rank", "occupation_title": "Occupation", "soc_code": "SOC", "major_group_title": "Major group",
        "priority_score": "Priority score", "observed_exposure": "Exposure", "employment_base_year": "Employment",
        "employment_growth_pct": "Growth (%)", "annual_openings": "Annual openings", "median_annual_wage": "Median annual wage",
        "dominant_mode": "Dominant mode",
    })
    st.dataframe(table, use_container_width=True, hide_index=True, column_config={
        "Priority score": st.column_config.NumberColumn(format="%.1f"),
        "Exposure": st.column_config.NumberColumn(format="%.1%"),
        "Employment": st.column_config.NumberColumn(format="%,.0f"),
        "Growth (%)": st.column_config.NumberColumn(format="%.1f%%"),
        "Annual openings": st.column_config.NumberColumn(format="%,.0f"),
        "Median annual wage": st.column_config.NumberColumn(format="$%,.0f"),
    })

with detail_tab:
    st.subheader("Occupation drill-down")
    if eligible.empty:
        st.info("No occupation matches the current filters.")
    else:
        choices = eligible.sort_values("occupation_title").reset_index(drop=True)
        labels = {occupation_label(row): row["soc_code"] for _, row in choices.iterrows()}
        default_soc = ranking.iloc[0]["soc_code"] if not ranking.empty else choices.iloc[0]["soc_code"]
        label_list = list(labels)
        default_label = next(text for text, code in labels.items() if code == default_soc)
        selected_label = st.selectbox("Select an eligible occupation", label_list, index=label_list.index(default_label), key="detail_occupation")
        selected_soc = labels[selected_label]
        # The same filtered set keeps drill-down score components consistent with the ranking.
        detail = backend.get_occupation_detail(eligible, tasks, selected_soc)
        row = detail["occupation"]
        st.markdown(f"### {row['occupation_title']}  \n{row['major_group_title']} · SOC {selected_soc}")
        metrics = st.columns(4)
        metrics[0].metric("Rank", fmt(row.get("rank")))
        metrics[1].metric("Priority score", fmt(row.get("priority_score"), 1))
        metrics[2].metric("Observed exposure", pct(row.get("observed_exposure")))
        metrics[3].metric("Base-year employment", fmt(row.get("employment_base_year")))
        labor_metrics = st.columns(4)
        labor_metrics[0].metric("Projected employment", fmt(row.get("employment_projection_year")))
        growth = row.get("employment_growth_pct")
        labor_metrics[1].metric("Projected growth", f"{fmt(growth, 1)}%" if pd.notna(growth) else "Unavailable")
        labor_metrics[2].metric("Annual openings", fmt(row.get("annual_openings")))
        wage = row.get("median_annual_wage")
        labor_metrics[3].metric("Median annual wage", "$" + fmt(wage) if pd.notna(wage) else "Unavailable")
        mode_metrics = st.columns(3)
        mode_metrics[0].metric("Augmentation share", pct(row.get("augmentation_share")))
        mode_metrics[1].metric("Automation share", pct(row.get("automation_share")))
        mode = row.get("dominant_mode")
        mode_metrics[2].metric("Dominant mode", str(mode).title() if pd.notna(mode) else "Unavailable")
        if row.get("priority_score_available"):
            st.markdown("#### How the score is built")
            components = pd.DataFrame([{"Component": name.title(), "Weight": item["weight"], "Within-filter percentile": item["percentile"], "Weighted points": item["contribution"]} for name, item in detail["score_components"].items()])
            st.dataframe(components, use_container_width=True, hide_index=True, column_config={
                "Weight": st.column_config.NumberColumn(format="%.0%"),
                "Within-filter percentile": st.column_config.NumberColumn(format="%.1%"),
                "Weighted points": st.column_config.NumberColumn(format="%.1f"),
            })
        else:
            st.info("A score is unavailable because one or more required inputs are missing.")
        st.markdown("#### Tasks associated with this occupation")
        task_rows = detail["tasks"]
        if not task_rows:
            st.info("No mapped task rows are available for this occupation.")
        else:
            task_frame = pd.DataFrame(task_rows)
            task_sort = st.radio("Sort tasks by", ["Penetration", "Task name"], horizontal=True)
            if task_sort == "Task name":
                task_frame = task_frame.sort_values("task", na_position="last")
            task_frame = task_frame[["task_id", "task", "penetration", "augmentation_share", "automation_share", "dominant_mode"]].rename(columns={
                "task_id": "Task ID", "task": "Task", "penetration": "Penetration",
                "augmentation_share": "Augmentation", "automation_share": "Automation", "dominant_mode": "Dominant mode",
            })
            st.dataframe(task_frame, use_container_width=True, hide_index=True, column_config={
                "Penetration": st.column_config.NumberColumn(format="%.1%"),
                "Augmentation": st.column_config.NumberColumn(format="%.1%"),
                "Automation": st.column_config.NumberColumn(format="%.1%"),
            })

with compare_tab:
    st.subheader("Compare occupations side by side")
    if eligible.empty:
        st.info("No occupation matches the current filters.")
    else:
        choices = eligible.sort_values("occupation_title").reset_index(drop=True)
        compare_labels = {occupation_label(row): row["soc_code"] for _, row in choices.iterrows()}
        selected = st.multiselect("Choose up to five occupations", list(compare_labels), max_selections=5, key="compare_occupations")
        if selected:
            codes = [compare_labels[value] for value in selected]
            ordered = backend.rank_occupations(eligible, top_n=None, include_incomplete=True)
            comparison = ordered[ordered["soc_code"].isin(codes)].set_index("occupation_title")[[
                "rank", "priority_score", "observed_exposure", "employment_base_year", "employment_growth_pct",
                "annual_openings", "augmentation_share", "automation_share", "dominant_mode",
            ]]
            comparison.columns = ["Rank", "Priority score", "Observed exposure", "Employment", "Projected growth (%)", "Annual openings", "Augmentation", "Automation", "Dominant mode"]
            st.dataframe(comparison, use_container_width=True, column_config={
                "Priority score": st.column_config.NumberColumn(format="%.1f"),
                "Observed exposure": st.column_config.NumberColumn(format="%.1%"),
                "Employment": st.column_config.NumberColumn(format="%,.0f"),
                "Projected growth (%)": st.column_config.NumberColumn(format="%.1f%%"),
                "Annual openings": st.column_config.NumberColumn(format="%,.0f"),
                "Augmentation": st.column_config.NumberColumn(format="%.1%"),
                "Automation": st.column_config.NumberColumn(format="%.1%"),
            })
        else:
            st.caption("Choose occupations to compare their measures.")

with notes_tab:
    st.subheader("How to read this dashboard")
    st.markdown(
        """
        **Implementation Priority Score** is an investigation aid, not a risk score.
        It combines within-filter percentiles: 45% observed exposure, 25% base-year
        employment, 15% projected growth, and 15% annual openings. Scores are
        recalculated whenever eligibility filters change. Augmentation and
        automation are displayed separately and do not enter the score.

        **Mode shares** are penetration-weighted among tasks with documented mode
        data. Their sum may be below 100% because filtered interactions are
        excluded. Missing mode coverage stays unavailable.

        **Task penetration** describes observed task usage in the Anthropic data.
        Task matching uses deterministic normalized task descriptions. Missing
        inputs are not treated as zero.
        """
    )
    st.markdown("#### Limitations")
    st.markdown("- Anthropic data reflects observed Claude usage, not all AI tools or workers.\n- Exposure is not automation, displacement, or job loss.\n- Task mapping and occupational crosswalks can be imperfect.\n- BLS projections are estimates.\n- Score weights are policy choices and should be interpreted transparently.")
    st.markdown("#### Data and provenance")
    st.caption(
        "The dashboard loads data/processed/occupation_dashboard.csv and "
        "data/processed/occupation_tasks.csv. Local Anthropic inputs: "
        "cleaned/job_exposure_cleaned.csv (756 × 3; occ_code, title, "
        "observed_exposure; SHA-256 "
        "4f0a3adf5feeb2ec5f5d02ab18cc5e851a2a4b8470bde84c0c9335017be12d68) "
        "and cleaned/task_penetration_cleaned.csv (17,998 × 2; task, "
        "penetration; SHA-256 "
        "85bee872db1d55d3e9a7f4e89da5ae4a5d59aa8ec875d728fbf4b7d820984616) "
        "have unresolved upstream release dates. Upstream release/date not "
        "independently verified. Source families include Anthropic Economic "
        "Index, O*NET task statements and SOC structure, and BLS 2025–2035 "
        "Occupational Projections, Table 1.2."
    )
    with st.expander("Validation details"):
        st.json(validation)
