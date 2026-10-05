#!/usr/bin/env python3
"""Read-only profiler for the AI workforce project CSV files.

The input CSVs are opened as text so identifiers such as ``occ_code`` retain
their formatting. The script writes a Markdown report to a separate file.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any


DEFAULT_SOURCE = "Anthropic Economic Index (project brief; file-level attribution not independently verified)"
DEFAULT_SOURCE_URL = "https://huggingface.co/datasets/Anthropic/EconomicIndex"
FILE_SPECS = {
    "job_exposure.csv": {
        "ids": ["occ_code"],
        "numeric": ["observed_exposure"],
        "proportions": ["observed_exposure"],
        "dates": [],
    },
    "task_penetration.csv": {
        "ids": ["task"],
        "numeric": ["penetration"],
        "proportions": ["penetration"],
        "dates": [],
    },
}


def infer_type(values: list[str], column: str) -> str:
    """Infer a display type without coercing identifier-like fields."""
    if re.search(r"(^|_)(id|code|key)(_|$)", column.lower()):
        return "string (identifier; leading zeros preserved)"
    present = [value.strip() for value in values if value.strip()]
    if not present:
        return "unknown (all values missing)"
    lowered = {value.lower() for value in present}
    if lowered <= {"true", "false"}:
        return "boolean-like string"
    parsed: list[float] = []
    for value in present:
        try:
            parsed.append(float(value))
        except ValueError:
            break
    else:
        if all(math.isfinite(number) and number.is_integer() for number in parsed):
            return "integer-like numeric"
        return "numeric"
    return "string"


def parse_number(value: str) -> float | None:
    try:
        result = float(value.strip())
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def parse_date(value: str) -> bool:
    value = value.strip()
    if not value:
        return True
    try:
        # Handle common ISO forms, including timestamps with a Z suffix.
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        pass
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def profile_file(path: Path, source: str, source_url: str, version: str, download_date: str) -> str:
    spec = FILE_SPECS.get(path.name, {"ids": [], "numeric": [], "proportions": [], "dates": []})
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        rows = list(reader)

    lines = [f"## `{path.name}`", "", "### Source and provenance", "",
             f"- Source: {source}", f"- Source URL: {source_url}",
             f"- Dataset/file version: {version}", f"- Download date: {download_date}",
             f"- Local file modified time (not a download date): {datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec='seconds')}",
             f"- File: `{path}`", "", "### Shape", "",
             f"- Rows: {len(rows):,}", f"- Columns: {len(columns):,}",
             f"- Exact duplicate rows (all columns equal): {len(rows) - len({tuple(row.get(c, '') for c in columns) for row in rows}):,}", "",
             "### Columns", "", "| Column | Inferred type | Example values | Missing values |",
             "|---|---|---|---:|"]

    for column in columns:
        values = [row.get(column) or "" for row in rows]
        examples = []
        for value in values:
            if value.strip() and value not in examples:
                examples.append(value)
            if len(examples) == 3:
                break
        lines.append(f"| `{md(column)}` | {md(infer_type(values, column))} | {md('; '.join(examples) if examples else '(none)')} | {sum(not value.strip() for value in values):,} |")

    lines += ["", "### Likely identifier checks", ""]
    if not spec["ids"]:
        lines.append("No identifier columns were configured or inferred.")
    for column in spec["ids"]:
        if column not in columns:
            lines.append(f"- `{column}`: configured identifier column is absent.")
            continue
        values = [row.get(column, "") or "" for row in rows]
        counts = Counter(values)
        repeated = [(value, count) for value, count in counts.items() if count > 1]
        lines.append(f"- `{column}`: {len(counts):,} distinct values; {sum(count - 1 for _, count in repeated):,} repeated occurrences beyond the first; {sum(not value.strip() for value in values):,} blank values.")
        if repeated:
            lines.append("  - Repeated examples: " + "; ".join(f"`{md(value)}` ({count} rows)" for value, count in repeated[:8]))
    lines += ["", "### Numeric conversion checks", ""]
    numeric_columns = [column for column in spec["numeric"] if column in columns]
    if not numeric_columns:
        lines.append("No numeric columns configured for this file.")
    for column in numeric_columns:
        failures = [(index + 2, row.get(column, "")) for index, row in enumerate(rows) if (row.get(column) or "").strip() and parse_number(row[column]) is None]
        numbers = [parse_number(row.get(column, "") or "") for row in rows]
        valid = [number for number in numbers if number is not None]
        lines.append(f"- `{column}`: {len(failures):,} failed conversions; numeric range {min(valid):g} to {max(valid):g}." if valid else f"- `{column}`: {len(failures):,} failed conversions; no valid numeric values.")
        if failures:
            lines.append("  - Failed examples (CSV line, value): " + "; ".join(f"{line}: `{md(value)}`" for line, value in failures[:8]))
    lines += ["", "### Date conversion checks", ""]
    date_columns = spec["dates"] or [column for column in columns if re.search(r"date|datetime|timestamp|_at$", column.lower())]
    date_columns = [column for column in date_columns if column in columns]
    if not date_columns:
        lines.append("No date-like columns found; no date conversions attempted.")
    for column in date_columns:
        failures = [(index + 2, row.get(column, "")) for index, row in enumerate(rows) if not parse_date(row.get(column, "") or "")]
        lines.append(f"- `{column}`: {len(failures):,} failed date conversions.")
        if failures:
            lines.append("  - Failed examples (CSV line, value): " + "; ".join(f"{line}: `{md(value)}`" for line, value in failures[:8]))
    lines += ["", "### Invalid, impossible, or suspicious values", ""]
    findings = 0
    for column in spec["proportions"]:
        if column not in columns:
            continue
        invalid = [(index + 2, row.get(column, ""), parse_number(row.get(column, "") or "")) for index, row in enumerate(rows)]
        invalid = [(line, value, number) for line, value, number in invalid if number is None or not 0 <= number <= 1]
        if invalid:
            findings += 1
            lines.append(f"- `{column}`: {len(invalid):,} missing, nonnumeric, or outside the expected 0–1 proportion range.")
            lines.append("  - Examples (CSV line, value): " + "; ".join(f"{line}: `{md(value)}`" for line, value, _ in invalid[:8]))
        values = [parse_number(row.get(column, "") or "") for row in rows]
        valid = [value for value in values if value is not None]
        zero_count = sum(value == 0 for value in valid)
        if valid and zero_count / len(valid) >= 0.5:
            findings += 1
            lines.append(f"- `{column}`: {zero_count:,} of {len(valid):,} valid values ({zero_count / len(valid):.1%}) are zero; review whether this concentration is expected by the source methodology.")
    for column in columns:
        if re.search(r"(^|_)(id|code|key)(_|$)", column.lower()):
            values = [row.get(column, "") or "" for row in rows]
            leading_zero = [value for value in values if len(value) > 1 and value.startswith("0")]
            if leading_zero:
                findings += 1
                lines.append(f"- `{column}`: {len(leading_zero):,} value(s) begin with zero; retained as text to preserve identifier formatting.")
    if findings == 0:
        lines.append("No invalid values detected by the configured checks. This does not establish that values are valid under the source methodology.")
    lines += ["", "### Profiling notes", "",
              "- Profiling only: no values were changed, normalized, imputed, or removed.",
              "- All CSV fields were read as text first; numeric/date parsing was used only for checks, preserving leading zeros.",
              "- Proportion-range checks assume these named metrics are fractions on a 0..1 scale; confirm against source documentation.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent,
                        help="Directory containing the two source CSVs (default: script directory).")
    parser.add_argument("--output", type=Path, default=None,
                        help="Markdown report path (default: <data-dir>/data_profile.md).")
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="Source description to record.")
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL, help="Source URL to record.")
    parser.add_argument("--version", default="Unknown / not recorded", help="Dataset or source-file version, if known.")
    parser.add_argument("--download-date", default="Unknown / not recorded", help="Download date, if known (for example YYYY-MM-DD).")
    args = parser.parse_args()

    output = args.output or (args.data_dir / "data_profile.md")
    inputs = [args.data_dir / name for name in FILE_SPECS]
    missing = [path for path in inputs if not path.is_file()]
    if missing:
        parser.error("Missing input file(s): " + ", ".join(str(path) for path in missing))
    report = ["# Dataset Profile", "", f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
              "", "This report describes the source files without modifying them.", ""]
    for path in inputs:
        report.append(profile_file(path, args.source, args.source_url, args.version, args.download_date))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(report), encoding="utf-8")
    print(f"Profile saved to: {output.resolve()}")


if __name__ == "__main__":
    main()
