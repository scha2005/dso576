"""Reusable backend analysis for the AI Workforce Priority Dashboard.

Implements BUILD_SPEC.md against:
- data/processed/occupation_dashboard.csv
- data/processed/occupation_tasks.csv
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Optional, Sequence

import numpy as np
import pandas as pd


SOC_PATTERN = re.compile(r"^\d{2}-\d{4}$")
ONET_SOC_PATTERN = re.compile(r"^\d{2}-\d{4}\.\d{2}$")
ALLOWED_MODES = {"augmentation", "automation", "balanced"}
TASK_PERCENTAGE_TOLERANCE = 1e-9
OCCUPATION_REQUIRED_COLUMNS = {
    "soc_code", "occupation_title", "bls_title", "major_group_code",
    "major_group_title", "observed_exposure", "mapped_task_count",
    "positive_penetration_task_count", "positive_penetration_task_pct",
    "mean_task_penetration", "augmentation_share", "automation_share",
    "dominant_mode", "employment_base_year", "employment_projection_year",
    "employment_change_numeric", "employment_growth_pct", "annual_openings",
    "median_annual_wage",
}
TASK_REQUIRED_COLUMNS = {
    "onet_soc_code", "soc_code", "occupation_title", "task_id", "task",
    "task_normalized", "penetration", "augmentation_share",
    "automation_share", "dominant_mode",
}
SCORE_COMPONENTS = {
    "exposure": ("observed_exposure", 0.45),
    "employment": ("employment_base_year", 0.25),
    "growth": ("employment_growth_pct", 0.15),
    "openings": ("annual_openings", 0.15),
}


class DataValidationError(ValueError):
    """Canonical data violates BUILD_SPEC.md."""


def _require_columns(df: pd.DataFrame, required: set[str], dataset: str) -> None:
    missing = sorted(required - set(df.columns))
    if missing:
        raise DataValidationError(
            f"{dataset} is missing BUILD_SPEC.md columns: {missing}"
        )


def _coerce_numeric(
    df: pd.DataFrame,
    columns: Iterable[str],
    dataset: str = "data",
    required_nonnull: Iterable[str] = (),
) -> pd.DataFrame:
    result = df.copy()
    required_nonnull = set(required_nonnull)
    for column in columns:
        if column in result:
            original = result[column]
            converted = pd.to_numeric(original, errors="coerce")
            malformed = original.notna() & converted.isna()
            if malformed.any():
                examples = original[malformed].astype(str).drop_duplicates().head(10).tolist()
                raise DataValidationError(
                    f"{dataset}.{column} has {int(malformed.sum())} invalid numeric value(s); "
                    f"examples: {examples}. Use numeric values or a true missing value."
                )
            if column in required_nonnull and converted.isna().any():
                rows = converted[converted.isna()].index.tolist()[:10]
                raise DataValidationError(
                    f"{dataset}.{column} has {int(converted.isna().sum())} missing value(s); "
                    f"examples at rows: {rows}. Supply a numeric value."
                )
            result[column] = converted
    return result


def _validate_nonblank(series: pd.Series, column: str, dataset: str) -> pd.Series:
    null_mask = series.isna()
    if null_mask.any():
        examples = series.index[null_mask].tolist()[:10]
        raise DataValidationError(
            f"{dataset}.{column} has {int(null_mask.sum())} null value(s); "
            f"examples at rows: {examples}. Supply a nonblank value."
        )
    values = series.astype("string").str.strip()
    blank_mask = values.eq("").fillna(False)
    if blank_mask.any():
        examples = series.index[blank_mask].tolist()[:10]
        raise DataValidationError(
            f"{dataset}.{column} has {int(blank_mask.sum())} blank value(s); "
            f"examples at rows: {examples}. Supply a nonblank value."
        )
    return values


def _validate_code_series(series: pd.Series, dataset: str, column: str, pattern: re.Pattern) -> pd.Series:
    values = _validate_nonblank(series, column, dataset)
    malformed = ~values.str.fullmatch(pattern, na=False)
    if malformed.any():
        examples = values[malformed].drop_duplicates().head(10).tolist()
        raise DataValidationError(
            f"{dataset}.{column} has {int(malformed.sum())} malformed value(s); "
            f"examples: {examples}. Expected format {pattern.pattern.strip('^$')} with no spaces."
        )
    return values


def _validate_soc_codes(series: pd.Series, dataset: str) -> pd.Series:
    return _validate_code_series(series, dataset, "soc_code", SOC_PATTERN)


def _validate_onet_soc_codes(series: pd.Series, dataset: str) -> pd.Series:
    return _validate_code_series(series, dataset, "onet_soc_code", ONET_SOC_PATTERN)


def _numeric_values(df: pd.DataFrame, column: str, dataset: str) -> pd.Series:
    return _coerce_numeric(df, [column], dataset)[column]


def _validate_proportion(series: pd.Series, column: str, dataset: str) -> None:
    numeric = _numeric_values(pd.DataFrame({column: series}), column, dataset)
    invalid = numeric.notna() & (~numeric.between(0, 1) | ~np.isfinite(numeric))
    if invalid.any():
        raise DataValidationError(
            f"{dataset}.{column} must be within 0-1; "
            f"examples: {series[invalid].head(10).tolist()}"
        )


def _validate_modes(series: pd.Series, dataset: str, column: str = "dominant_mode") -> None:
    normalized = series.astype("string").str.strip()
    normalized = normalized.mask(normalized.eq(""))
    invalid = normalized.notna() & ~normalized.isin(ALLOWED_MODES)
    if invalid.any():
        examples = normalized[invalid].drop_duplicates().head(10).tolist()
        raise DataValidationError(
            f"{dataset}.{column} has {int(invalid.sum())} invalid mode value(s): {examples}. "
            f"Allowed values are {sorted(ALLOWED_MODES)} or missing."
        )


def _validate_occupation_data(occupations: pd.DataFrame) -> None:
    _require_columns(occupations, OCCUPATION_REQUIRED_COLUMNS, "occupation data")
    soc = _validate_soc_codes(occupations["soc_code"], "occupation data")
    duplicate_soc = soc.duplicated(keep=False)
    if duplicate_soc.any():
        examples = soc[duplicate_soc].drop_duplicates().head(10).tolist()
        raise DataValidationError(f"occupation data.soc_code has {int(duplicate_soc.sum())} duplicate key row(s); examples: {examples}.")

    count_cols = ["mapped_task_count", "positive_penetration_task_count"]
    numeric_cols = count_cols + [
        "observed_exposure", "positive_penetration_task_pct", "mean_task_penetration",
        "augmentation_share", "automation_share", "employment_base_year",
        "employment_projection_year", "employment_change_numeric", "employment_growth_pct",
        "annual_openings", "median_annual_wage",
    ]
    numeric = _coerce_numeric(occupations, numeric_cols, "occupation data", required_nonnull=count_cols)
    for column in numeric_cols:
        values = numeric[column]
        non_finite = values.notna() & ~np.isfinite(values)
        if non_finite.any():
            examples = occupations.loc[non_finite, column].head(10).tolist()
            raise DataValidationError(
                f"occupation data.{column} has {int(non_finite.sum())} non-finite value(s): {examples}. "
                "Use finite numeric values or a true missing value."
            )
    for column in count_cols:
        values = numeric[column]
        invalid = values.lt(0) | ~np.isfinite(values) | (values % 1 != 0)
        if invalid.any():
            examples = occupations.loc[invalid, column].head(10).tolist()
            raise DataValidationError(
                f"occupation data.{column} has {int(invalid.sum())} invalid count value(s): {examples}. "
                "Counts must be finite, nonnegative whole numbers."
            )
    mapped = numeric["mapped_task_count"]
    positive = numeric["positive_penetration_task_count"]
    too_many = positive > mapped
    if too_many.any():
        examples = occupations.loc[too_many, ["soc_code"] + count_cols].head(10).to_dict("records")
        raise DataValidationError(
            f"occupation data.positive_penetration_task_count exceeds mapped_task_count in "
            f"{int(too_many.sum())} row(s); examples: {examples}."
        )
    pct = numeric["positive_penetration_task_pct"]
    zero_tasks = mapped.eq(0)
    bad_zero = zero_tasks & (positive.ne(0) | pct.notna())
    if bad_zero.any():
        examples = occupations.loc[bad_zero, ["soc_code"] + count_cols + ["positive_penetration_task_pct"]].head(10).to_dict("records")
        raise DataValidationError(
            f"occupation data has {int(bad_zero.sum())} zero-task row(s) violating the zero-task rule; "
            f"examples: {examples}. Require both counts to be 0 and positive_penetration_task_pct missing."
        )
    positive_tasks = mapped.gt(0)
    if (positive_tasks & pct.isna()).any():
        rows = occupations.index[positive_tasks & pct.isna()].tolist()[:10]
        raise DataValidationError(
            f"occupation data.positive_penetration_task_pct is missing for "
            f"{int((positive_tasks & pct.isna()).sum())} row(s) with mapped tasks; rows: {rows}."
        )
    expected_pct = positive / mapped.where(positive_tasks)
    inconsistent = positive_tasks & ~np.isclose(pct.fillna(-1), expected_pct.fillna(-1), rtol=0, atol=TASK_PERCENTAGE_TOLERANCE)
    if inconsistent.any():
        examples = occupations.loc[inconsistent, ["soc_code"] + count_cols + ["positive_penetration_task_pct"]].head(10).to_dict("records")
        raise DataValidationError(
            f"occupation data.positive_penetration_task_pct is inconsistent with task counts in "
            f"{int(inconsistent.sum())} row(s); examples: {examples}. Tolerance is {TASK_PERCENTAGE_TOLERANCE}."
        )
    for column in ("observed_exposure", "positive_penetration_task_pct", "mean_task_penetration", "augmentation_share", "automation_share"):
        _validate_proportion(occupations[column], column, "occupation data")
    for column in ("employment_base_year", "employment_projection_year", "annual_openings", "median_annual_wage"):
        values = numeric[column]
        invalid = values.notna() & (values.lt(0) | ~np.isfinite(values))
        if invalid.any():
            examples = occupations.loc[invalid, column].head(10).tolist()
            raise DataValidationError(f"occupation data.{column} has {int(invalid.sum())} negative or non-finite value(s): {examples}. Values must be nonnegative or missing.")
    _validate_modes(occupations["dominant_mode"], "occupation data")


def _validate_task_data(tasks: pd.DataFrame) -> None:
    _require_columns(tasks, TASK_REQUIRED_COLUMNS, "task data")
    soc = _validate_soc_codes(tasks["soc_code"], "task data")
    onet = _validate_onet_soc_codes(tasks["onet_soc_code"], "task data")
    for column in ("task_id", "task", "task_normalized"):
        _validate_nonblank(tasks[column], column, "task data")
    task_ids = tasks["task_id"].astype("string").str.strip()
    duplicate_key = pd.DataFrame({"onet_soc_code": onet, "task_id": task_ids}).duplicated(keep=False)
    if duplicate_key.any():
        examples = pd.DataFrame({"onet_soc_code": onet, "task_id": task_ids}).loc[duplicate_key].head(10).to_dict("records")
        raise DataValidationError(
            f"task data has {int(duplicate_key.sum())} duplicate (onet_soc_code, task_id) key row(s); "
            f"examples: {examples}. Each O*NET task ID must be unique within its detailed occupation."
        )
    expected_soc = onet.str.slice(0, 7)
    mismatch = soc.ne(expected_soc)
    if mismatch.any():
        examples = pd.DataFrame({"onet_soc_code": onet, "soc_code": soc}).loc[mismatch].head(10).to_dict("records")
        raise DataValidationError(f"task data has {int(mismatch.sum())} soc_code/onet_soc_code mismatch(es); examples: {examples}.")
    numeric_cols = ["penetration", "augmentation_share", "automation_share"]
    _coerce_numeric(tasks, numeric_cols, "task data")
    for column in numeric_cols:
        _validate_proportion(tasks[column], column, "task data")
    _validate_modes(tasks["dominant_mode"], "task data")


def validate_spec_alignment(
    occupations: pd.DataFrame, tasks: Optional[pd.DataFrame] = None
) -> dict[str, Any]:
    """Validate canonical schemas, keys, values, and units."""

    _validate_occupation_data(occupations)

    report = {
        "occupation_rows": int(len(occupations)),
        "unique_occupations": int(occupations["soc_code"].nunique()),
        "task_rows": None,
        "unique_tasks": None,
    }

    if tasks is not None:
        _validate_task_data(tasks)

        report["task_rows"] = int(len(tasks))
        report["unique_tasks"] = int(tasks["task_normalized"].nunique())

    return report


def load_occupation_data(path: str | Path) -> pd.DataFrame:
    """Load and validate canonical occupation data."""

    df = pd.read_csv(path, dtype={"soc_code": "string", "major_group_code": "string"})
    numeric = [
        "observed_exposure", "mapped_task_count",
        "positive_penetration_task_count", "positive_penetration_task_pct",
        "mean_task_penetration", "augmentation_share", "automation_share",
        "employment_base_year", "employment_projection_year",
        "employment_change_numeric", "employment_growth_pct",
        "annual_openings", "median_annual_wage",
    ]
    validate_spec_alignment(df)
    df["soc_code"] = df.soc_code.str.strip()
    return _coerce_numeric(df, numeric, "occupation data", required_nonnull=("mapped_task_count", "positive_penetration_task_count"))


def load_task_data(path: str | Path) -> pd.DataFrame:
    """Load canonical occupation-task data and validate its schema."""

    df = pd.read_csv(
        path,
        dtype={"onet_soc_code": "string", "soc_code": "string", "task_id": "string"},
    )
    _validate_task_data(df)
    for column in ("onet_soc_code", "soc_code", "task_id"):
        df[column] = df[column].astype("string").str.strip()
    return _coerce_numeric(df, ["penetration", "augmentation_share", "automation_share"], "task data")


def _validate_range(value: Any, parameter: str, proportion: bool = False) -> tuple[Optional[float], Optional[float]]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or len(value) != 2:
        raise ValueError(f"{parameter} must contain exactly two bounds: (minimum, maximum).")
    bounds: list[Optional[float]] = []
    for label, bound in zip(("minimum", "maximum"), value):
        if bound is None:
            bounds.append(None)
            continue
        if isinstance(bound, (bool, np.bool_)):
            raise ValueError(f"{parameter} {label} must be a finite number or None; booleans are invalid.")
        if isinstance(bound, (str, bytes)):
            raise ValueError(f"{parameter} {label} must be numeric or None; received text {bound!r}.")
        try:
            number = float(bound)
        except (TypeError, ValueError):
            raise ValueError(f"{parameter} {label} must be a finite number or None; received {bound!r}.") from None
        if not np.isfinite(number):
            raise ValueError(f"{parameter} {label} must be finite; received {bound!r}.")
        if proportion and not 0 <= number <= 1:
            raise ValueError(f"{parameter} {label} must be between 0 and 1; received {number}.")
        bounds.append(number)
    low, high = bounds
    if low is not None and high is not None and low > high:
        raise ValueError(f"{parameter} minimum ({low}) cannot exceed maximum ({high}).")
    return low, high


def _validate_min_employment(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (bool, np.bool_)):
        raise ValueError("min_employment must be a finite nonnegative number or None; booleans are invalid.")
    if isinstance(value, (str, bytes)):
        raise ValueError(f"min_employment must be numeric or None; received text {value!r}.")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"min_employment must be a finite nonnegative number or None; received {value!r}.") from None
    if not np.isfinite(number) or number < 0:
        raise ValueError(f"min_employment must be finite and nonnegative; received {value!r}.")
    return number


def filter_occupations(
    occupations: pd.DataFrame,
    major_groups: Optional[Sequence[str]] = None,
    search: Optional[str] = None,
    min_employment: Optional[float] = None,
    growth_range: Optional[tuple[Optional[float], Optional[float]]] = None,
    exposure_range: Optional[tuple[Optional[float], Optional[float]]] = None,
    dominant_modes: Optional[Sequence[str]] = None,
) -> pd.DataFrame:
    """Apply dashboard eligibility filters without calculating a score."""

    min_employment = _validate_min_employment(min_employment)
    growth_range = _validate_range(growth_range, "growth_range") if growth_range is not None else None
    exposure_range = _validate_range(exposure_range, "exposure_range", proportion=True) if exposure_range is not None else None
    if dominant_modes is not None:
        if isinstance(dominant_modes, (str, bytes)):
            raise ValueError("dominant_modes must be a sequence of allowed mode names; pass a list or tuple.")
        invalid_modes = [mode for mode in dominant_modes if not isinstance(mode, str) or mode not in ALLOWED_MODES]
        if invalid_modes:
            examples = sorted((repr(mode) for mode in invalid_modes))[:10]
            raise ValueError(f"dominant_modes contains unsupported mode(s): {examples}. Allowed values: {sorted(ALLOWED_MODES)}.")

    result = occupations.copy()

    if major_groups:
        selected = {str(value) for value in major_groups}
        result = result[
            result["major_group_code"].astype(str).isin(selected)
            | result["major_group_title"].astype(str).isin(selected)
        ]

    if search and search.strip():
        query = re.escape(search.strip())
        mask = (
            result["occupation_title"].astype(str).str.contains(query, case=False, na=False)
            | result["soc_code"].astype(str).str.contains(query, case=False, na=False)
        )
        result = result[mask]

    if min_employment is not None:
        result = result[result["employment_base_year"] >= float(min_employment)]

    if growth_range:
        low, high = growth_range
        if low is not None:
            result = result[result["employment_growth_pct"] >= float(low)]
        if high is not None:
            result = result[result["employment_growth_pct"] <= float(high)]

    if exposure_range:
        low, high = exposure_range
        if low is not None:
            result = result[result["observed_exposure"] >= float(low)]
        if high is not None:
            result = result[result["observed_exposure"] <= float(high)]

    if dominant_modes:
        result = result[result["dominant_mode"].isin(dominant_modes)]

    return result.reset_index(drop=True)


def add_priority_score(occupations: pd.DataFrame) -> pd.DataFrame:
    """Add within-view percentiles and weighted score contributions."""

    result = occupations.copy()
    source_columns = [column for column, _ in SCORE_COMPONENTS.values()]
    missing = [column for column in source_columns if column not in result]
    if missing:
        raise DataValidationError(f"Cannot score; missing columns: {missing}")

    complete = result[source_columns].notna().all(axis=1)
    result["priority_score_available"] = complete
    contributions = []

    for name, (source, weight) in SCORE_COMPONENTS.items():
        percentile = f"{name}_percentile"
        contribution = f"{name}_contribution"
        result[percentile] = np.nan
        result[contribution] = np.nan
        if complete.any():
            ranked = result.loc[complete, source].rank(method="average", pct=True)
            result.loc[complete, percentile] = ranked
            result.loc[complete, contribution] = 100 * weight * ranked
        contributions.append(contribution)

    result["priority_score"] = result[contributions].sum(
        axis=1, min_count=len(contributions)
    )
    return result


def rank_occupations(
    occupations: pd.DataFrame,
    top_n: Optional[int] = 25,
    include_incomplete: bool = False,
) -> pd.DataFrame:
    """Score and order eligible occupations using the specified tie breakers."""

    if top_n is not None and (isinstance(top_n, (bool, np.bool_)) or not isinstance(top_n, (int, np.integer)) or top_n <= 0):
        raise ValueError("top_n must be a positive integer or None")

    result = add_priority_score(occupations)
    if not include_incomplete:
        result = result[result["priority_score_available"]]

    result = result.sort_values(
        ["priority_score", "observed_exposure", "employment_base_year", "occupation_title"],
        ascending=[False, False, False, True],
        na_position="last",
        kind="mergesort",
    ).reset_index(drop=True)

    result["rank"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    available = result["priority_score_available"]
    tied_ranks = result.loc[available, "priority_score"].rank(
        method="min", ascending=False
    ).astype("Int64")
    result.loc[available, "rank"] = tied_ranks

    if top_n is not None:
        result = result.head(top_n)
    return result


def calculate_summary_metrics(occupations: pd.DataFrame) -> dict[str, Any]:
    """Return the four starting-view KPI values."""

    return {
        "occupations_analyzed": int(len(occupations)),
        "median_observed_exposure": occupations["observed_exposure"].median(),
        "employment_represented": occupations["employment_base_year"].sum(min_count=1),
        "median_projected_growth_pct": occupations["employment_growth_pct"].median(),
    }


def get_mode_breakdown(occupations: pd.DataFrame) -> pd.DataFrame:
    """Return chart-ready mode shares and the documented filtered residual."""

    columns = [
        "soc_code", "occupation_title", "augmentation_share",
        "automation_share", "dominant_mode",
    ]
    result = occupations[columns].copy()
    supported = result["augmentation_share"].notna() & result["automation_share"].notna()
    result["filtered_share"] = (1 - result["augmentation_share"] - result["automation_share"]).where(supported)
    return result


def get_exposure_growth_scatter(occupations: pd.DataFrame) -> pd.DataFrame:
    """Return chart-ready exposure, growth, and employment data."""

    columns = [
        "soc_code", "occupation_title", "major_group_title",
        "observed_exposure", "employment_growth_pct",
        "employment_base_year", "dominant_mode",
    ]
    return occupations[columns].copy()


def get_task_drilldown(
    tasks: pd.DataFrame, soc_code: str, limit: Optional[int] = None
) -> pd.DataFrame:
    """Return one occupation's tasks sorted by penetration."""

    _require_columns(tasks, TASK_REQUIRED_COLUMNS, "task data")
    if not SOC_PATTERN.fullmatch(str(soc_code)):
        raise ValueError("soc_code must use NN-NNNN format")

    result = tasks[tasks["soc_code"].astype(str) == str(soc_code)].copy()
    result = result.sort_values(
        ["penetration", "task"], ascending=[False, True], na_position="last"
    ).reset_index(drop=True)

    if limit is not None:
        if int(limit) <= 0:
            raise ValueError("limit must be positive or None")
        result = result.head(int(limit))
    return result


def get_occupation_detail(
    occupations: pd.DataFrame, tasks: pd.DataFrame, soc_code: str
) -> dict[str, Any]:
    """Return occupation metrics, score components, and tasks."""

    selected = occupations[occupations["soc_code"].astype(str) == str(soc_code)]
    if selected.empty:
        raise KeyError(f"Unknown soc_code: {soc_code}")
    if len(selected) > 1:
        raise DataValidationError(f"Duplicate occupation rows for {soc_code}")

    scored = add_priority_score(occupations)
    row = scored[scored["soc_code"].astype(str) == str(soc_code)].iloc[0]
    components = {
        name: {
            "percentile": row.get(f"{name}_percentile"),
            "contribution": row.get(f"{name}_contribution"),
            "weight": weight,
        }
        for name, (_, weight) in SCORE_COMPONENTS.items()
    }
    return {
        "occupation": row.to_dict(),
        "score_components": components,
        "tasks": get_task_drilldown(tasks, soc_code).to_dict(orient="records"),
    }


def build_dashboard_outputs(
    occupation_path: str | Path = "data/processed/occupation_dashboard.csv",
    task_path: str | Path = "data/processed/occupation_tasks.csv",
    filters: Optional[Mapping[str, Any]] = None,
    top_n: Optional[int] = 25,
    include_incomplete: bool = False,
) -> dict[str, Any]:
    """Load canonical data and create reusable Phase 3 outputs."""

    if top_n is not None and (isinstance(top_n, (bool, np.bool_)) or not isinstance(top_n, (int, np.integer)) or top_n <= 0):
        raise ValueError("top_n must be a positive integer or None")

    occupations = load_occupation_data(occupation_path)
    tasks = load_task_data(task_path)
    validation = validate_spec_alignment(occupations, tasks)
    eligible = filter_occupations(occupations, **dict(filters or {}))
    ranking = rank_occupations(eligible, top_n=None, include_incomplete=include_incomplete)
    ranking_visual = ranking.copy() if top_n is None else ranking.head(top_n).copy()

    return {
        "validation": validation,
        "eligible_occupations": eligible,
        "ranking": ranking,
        "ranking_visual": ranking_visual,
        "summary": calculate_summary_metrics(eligible),
        "mode_breakdown": get_mode_breakdown(eligible),
        "scatter": get_exposure_growth_scatter(eligible),
        "tasks": tasks,
    }


if __name__ == "__main__":
    outputs = build_dashboard_outputs()
    print({
        "validation": outputs["validation"],
        "summary": outputs["summary"],
        "ranking_rows": len(outputs["ranking"]),
    })

