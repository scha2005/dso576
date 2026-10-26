#!/usr/bin/env python3
"""Apply only approved, lossless rules to the two project CSVs.

Current approved rules preserve occupation codes as text and retain rows when
there are no missing values/date fields. Therefore outputs retain source values
and row counts. Unresolved numeric conversions and duplicate handling are
reported for review but are not applied.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


FILES = {
    "job_exposure.csv": {"ids": ["occ_code"], "numeric_review": ["observed_exposure"]},
    "task_penetration.csv": {"ids": ["task"], "numeric_review": ["penetration"]},
}
LOG_NAME = "cleaning_decision_log.md"


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    # DictReader returns strings, preserving identifiers and raw values.
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        rows = list(reader)
    if not columns:
        raise ValueError(f"No CSV header found in {path}")
    return columns, rows


def md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def num(value: str) -> float | None:
    try:
        result = float(value.strip())
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def missing_by_column(columns: list[str], rows: list[dict[str, str]]) -> dict[str, int]:
    return {column: sum(not (row.get(column) or "").strip() for row in rows) for column in columns}


def write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def exact_duplicate_rows(columns: list[str], rows: list[dict[str, str]]) -> int:
    return len(rows) - len({tuple(row.get(column, "") for column in columns) for row in rows})


def profile_one(name: str, source: Path, output: Path) -> tuple[str, dict[str, Any]]:
    columns, rows_before = read_csv(source)
    before_missing = missing_by_column(columns, rows_before)
    exact_dupes_before = exact_duplicate_rows(columns, rows_before)
    spec = FILES[name]

    # Approved rule: identifiers remain text, byte-for-byte as decoded CSV
    # fields. Approved missing/date rule: retain every row and make no edits.
    rows_after = [dict(row) for row in rows_before]
    assert len(rows_after) == len(rows_before), "Approved rules must retain every source row."
    for identifier in spec["ids"]:
        assert identifier in columns, f"Expected identifier column {identifier!r} in {name}."
        assert all(rows_after[i].get(identifier) == rows_before[i].get(identifier) for i in range(len(rows_before))), "Identifier values must remain unchanged."
    after_missing = missing_by_column(columns, rows_after)
    assert before_missing == after_missing, "Missing counts must not change under approved rules."

    output.parent.mkdir(parents=True, exist_ok=True)
    write_csv(output, columns, rows_after)
    out_columns, rows_written = read_csv(output)
    assert out_columns == columns
    assert rows_written == rows_before, "Output values/rows differ from source; stop for review."

    duplicate_rows_after = exact_duplicate_rows(columns, rows_after)
    id_report = {}
    for identifier in spec["ids"]:
        counts = Counter(row.get(identifier, "") or "" for row in rows_after)
        repeated = [(value, count) for value, count in counts.items() if count > 1]
        id_report[identifier] = {
            "distinct": len(counts),
            "repeated_excess": sum(count - 1 for _, count in repeated),
            "repeated_examples": repeated[:8],
        }
    conversion_report = {}
    metric_report = {}
    for column in spec["numeric_review"]:
        assert column in columns, f"Expected numeric review column {column!r} in {name}."
        failures = [(line + 2, row.get(column, "")) for line, row in enumerate(rows_after)
                    if (row.get(column) or "").strip() and num(row[column]) is None]
        conversion_report[column] = failures
        parsed = [num(row.get(column, "") or "") for row in rows_after]
        numbers = [value for value in parsed if value is not None]
        metric_report[column] = {
            "min": min(numbers) if numbers else None,
            "max": max(numbers) if numbers else None,
            "zeros": sum(value == 0 for value in numbers),
            "valid": len(numbers),
        }

    # No date columns are present in these project schemas. This is an
    # assertion against silently omitting a newly introduced date field.
    date_columns = [column for column in columns if any(term in column.lower() for term in ("date", "datetime", "timestamp"))]
    assert not date_columns, f"New date-like column(s) need a decision before processing: {date_columns}"

    info = {
        "source": source,
        "output": output,
        "columns": columns,
        "before_rows": len(rows_before),
        "after_rows": len(rows_after),
        "before_missing": before_missing,
        "after_missing": after_missing,
        "exact_duplicates_before": exact_dupes_before,
        "exact_duplicates_after": duplicate_rows_after,
        "ids": id_report,
        "conversion_failures": conversion_report,
        "metrics": metric_report,
        "source_sha256": digest(source),
        "output_sha256": digest(output),
        "changed_rows": 0,
        "changed_values": 0,
    }
    if info["source_sha256"] != info["output_sha256"]:
        # CSV formatting can differ while values remain equivalent, so the
        # field-wise equality assertion above is authoritative for changes.
        info["hash_note"] = "Serialization differs from source bytes; parsed rows and values verified identical."
    return render_section(name, info), info


def render_section(name: str, info: dict[str, Any]) -> str:
    lines = [f"## `{name}`", "",
             f"- Output: `{info['output']}`",
             f"- Rows: {info['before_rows']:,} before; {info['after_rows']:,} after; {info['changed_rows']:,} changed or removed.",
             f"- Columns: {len(info['columns']):,} (preserved).",
             f"- Exact duplicate rows: {info['exact_duplicates_before']:,} before; {info['exact_duplicates_after']:,} after; none removed.",
             "- Repeated likely identifier values (reported separately from exact duplicate rows):"]
    for col, report in info["ids"].items():
        lines.append(f"  - `{col}`: {report['distinct']:,} distinct; {report['repeated_excess']:,} repeated occurrences beyond first.")
        if report["repeated_examples"]:
            lines.append("    - Examples: " + "; ".join(f"`{md(value)}` ({count} rows)" for value, count in report["repeated_examples"]))
    lines.append("- Missing values by column (before -> after):")
    for col in info["columns"]:
        lines.append(f"  - `{col}`: {info['before_missing'][col]:,} -> {info['after_missing'][col]:,}.")
    lines.append("- Numeric conversion checks (diagnostic only; no type conversion applied):")
    for col, failures in info["conversion_failures"].items():
        lines.append(f"  - `{col}`: {len(failures):,} failed nonblank conversions.")
        if failures:
            lines.append("    - Examples (CSV line, value): " + "; ".join(f"{line}: `{md(value)}`" for line, value in failures[:8]))
    lines.append("- Suspicious metric checks (diagnostic only):")
    for col, report in info["metrics"].items():
        if report["valid"]:
            zero_share = report["zeros"] / report["valid"]
            lines.append(f"  - `{col}`: range {report['min']:g}..{report['max']:g}; {report['zeros']:,}/{report['valid']:,} values are zero ({zero_share:.1%}); zeros retained.")
    lines.append("- Date conversion checks: no date-like columns; no date conversions attempted.")
    lines.append("- Source SHA-256: `" + info["source_sha256"] + "`.")
    lines.append("- Output SHA-256: `" + info["output_sha256"] + "`.")
    if "hash_note" in info:
        lines.append("- Hash note: " + info["hash_note"])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent,
                        help="Directory containing original CSV files and decision log.")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Output directory (default: <data-dir>/cleaned).")
    args = parser.parse_args()
    data_dir = args.data_dir.resolve()
    output_dir = (args.output_dir or data_dir / "cleaned").resolve()
    if output_dir == data_dir or data_dir in output_dir.parents and output_dir == data_dir:
        parser.error("Output directory must be separate from the original files' directory.")
    for name in FILES:
        if not (data_dir / name).is_file():
            parser.error(f"Missing original input file: {data_dir / name}")

    sections = []
    infos = []
    for name in FILES:
        clean_name = name.removesuffix(".csv") + "_cleaned.csv"
        section, info = profile_one(name, data_dir / name, output_dir / clean_name)
        sections.append(section)
        infos.append(info)

    header = ["# Cleaning Decision Log — Execution Results", "",
              f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}", "",
              "Only rules marked **Approved** in `cleaning_decision_log.md` were applied. The approved rules preserve occupation identifiers as text and retain rows because current missing counts are zero and no date columns exist.", "",
              "No unresolved rule was applied. Numeric parsing, duplicate checks, and repeated identifier checks below are diagnostics only. The outputs retain all source values and rows; 'cleaned' denotes pipeline output, not additional data modifications.", "",
              "## Approved rules and recorded changes", "",
              "| Approved rule | Result | Changed values | Changed/removed rows |", "|---|---|---:|---:|",
              "| Preserve `job_exposure.csv` `occ_code` as text | Applied; all source identifier strings retained | 0 | 0 |",
              "| Retain rows and make no missing/date changes when none are present | Applied; no missing values or date-like columns found | 0 | 0 |",
              "| Preserve all remaining source columns and values pending unresolved decisions | Output values verified equal to parsed originals | 0 | 0 |", "",
              "## Dataset results", "", *sections, "",
              "## Unresolved or suspicious items (flagged, not changed)", "",
              "- Numeric metrics remain strings in the full cleaned CSVs because their conversion rules are unresolved in the decision log.",
              "- Exact duplicate rows and repeated identifier values are counted separately; neither is removed.",
              "- Zero-heavy metric distributions and task-description repetitions remain as in the sources and require source-methodology review.",
              "- No rows were dropped because of missingness; the observed missing counts are zero.", "",
              "The original proposal and status table are retained in `cleaning_decision_log.md`. This generated execution record supplements it without changing unresolved statuses.", ""]
    source_log = data_dir / LOG_NAME
    if not source_log.is_file():
        parser.error(f"Missing decision log: {source_log}")
    log_path = output_dir / "cleaning_decision_log_updated.md"
    output_dir.mkdir(parents=True, exist_ok=True)
    original_log = source_log.read_text(encoding="utf-8")
    original_log = original_log.replace(
        "No cleaning rules have been implemented. **Unresolved** means the decision needs your judgment before it can be approved. Unusual values are flagged for review, not treated as errors by default.",
        "Approved, lossless rules have been applied as documented in the execution results below. **Unresolved** means the decision still needs your judgment before any further transformation. Unusual values are flagged for review, not treated as errors by default.",
    )
    updated_log = original_log.rstrip() + "\n\n---\n\n" + "\n".join(header)
    log_path.write_text(updated_log, encoding="utf-8")
    print(f"Cleaned output directory: {output_dir}")
    print(f"Execution log: {log_path}")


if __name__ == "__main__":
    main()
