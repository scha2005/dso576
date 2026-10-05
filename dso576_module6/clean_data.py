#!/usr/bin/env python3
"""Reproducibly validate and export the DSO 576 Module 6 source CSVs.

Uses only the Python standard library. Source files are read-only; all generated
files are written beneath this script's outputs/ directory.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import subprocess
import sys
import tempfile
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = {
    "job_exposure": HERE / "data" / "raw" / "job_exposure.csv",
    "task_penetration": HERE / "data" / "raw" / "task_penetration.csv",
}
EXPECTED_HEADERS = {
    "job_exposure": ["occ_code", "title", "observed_exposure"],
    "task_penetration": ["task", "penetration"],
}
REPEAT_TASK = (
    "Write interesting and effective press releases, prepare information for media kits, "
    "and develop and maintain company internet or intranet Web pages."
)


def read_csv(path: Path, expected: list[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != expected:
            raise ValueError(f"Unexpected headers in {path.name}: {reader.fieldnames!r}")
        rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError(f"Malformed row with extra fields in {path.name}")
    return rows


def number(value: str, field: str, row_index: int) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field} failed numeric conversion at data row {row_index}") from exc
    if not result.is_finite():
        raise ValueError(f"{field} is not finite at data row {row_index}")
    return result


def canonical(value: Decimal) -> str:
    return format(value, "f")


def missing_counts(rows: list[dict[str, str]], fields: list[str]) -> dict[str, int]:
    return {field: sum(row.get(field) in (None, "") for row in rows) for field in fields}


def duplicate_counts(rows: list[dict[str, str]], fields: list[str]) -> dict[str, int]:
    counts = Counter(tuple(row[field] for field in fields) for row in rows)
    return {"groups": sum(n > 1 for n in counts.values()),
            "extra_rows": sum(n - 1 for n in counts.values() if n > 1)}


def numeric_stats(values: list[Decimal]) -> dict[str, object]:
    nums = [float(v) for v in values]
    return {
        "count": len(values), "min": canonical(min(values)), "max": canonical(max(values)),
        "mean": statistics.mean(nums), "median": statistics.median(nums),
        "sum": canonical(sum(values, Decimal(0))),
        "zero_count": sum(v == 0 for v in values),
        "positive_count": sum(v > 0 for v in values),
    }


def text_format_counts(rows: list[dict[str, str]], fields: list[str]) -> dict[str, dict[str, int]]:
    result = {}
    for field in fields:
        values = [row[field] for row in rows]
        result[field] = {
            "leading_or_trailing_whitespace_rows": sum(v != v.strip() for v in values),
            "blank_rows": sum(v == "" for v in values),
        }
    return result


def write_csv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def inspect(name: str) -> dict[str, object]:
    headers = EXPECTED_HEADERS[name]
    rows = read_csv(SOURCES[name], headers)
    numeric_field = "observed_exposure" if name == "job_exposure" else "penetration"
    text_fields = [h for h in headers if h != numeric_field]
    converted = [number(row[numeric_field], numeric_field, i + 1) for i, row in enumerate(rows)]
    key_field = "occ_code" if name == "job_exposure" else "task"
    key_counts = Counter(row[key_field] for row in rows)
    repeat_tasks = {}
    repeat_task_families = {}
    if name == "task_penetration":
        grouped: dict[str, list[tuple[int, str]]] = {}
        folded: dict[str, list[tuple[int, str, str]]] = {}
        for i, row in enumerate(rows, 1):
            grouped.setdefault(row["task"], []).append((i, row["penetration"]))
            folded.setdefault(row["task"].casefold(), []).append((i, row["penetration"], row["task"]))
        repeat_tasks = {task: occurrences for task, occurrences in grouped.items() if len(occurrences) > 1}
        repeat_task_families = {key: occurrences for key, occurrences in folded.items() if len(occurrences) > 1}
    return {
        "rows": rows, "headers": headers, "numeric_field": numeric_field,
        "numeric_values": converted, "text_fields": text_fields,
        "key_field": key_field, "key_repeat_groups": sum(n > 1 for n in key_counts.values()),
        "key_extra_rows": sum(n - 1 for n in key_counts.values() if n > 1),
        "missing": missing_counts(rows, headers),
        "exact_duplicates": duplicate_counts(rows, headers),
        "text_format": text_format_counts(rows, text_fields),
        "numeric_stats": numeric_stats(converted), "repeat_tasks": repeat_tasks,
        "repeat_task_families": repeat_task_families,
    }


def build_checks(job: dict[str, object], task: dict[str, object], out: Path) -> list[dict[str, object]]:
    checks = []
    jr = job["rows"]
    jvals = job["numeric_values"]
    cleaned_job_rows = read_csv(out / "job_exposure_cleaned.csv", job["headers"])
    zero_i = next(i for i, v in enumerate(jvals) if v == 0)
    max_i = next(i for i, v in enumerate(jvals) if v == max(jvals))
    checks.extend([
        {"check_id": "J1", "dataset": "job_exposure", "row_index": zero_i + 1,
         "field": "observed_exposure", "original_value": jr[zero_i]["observed_exposure"],
         "expected_result": canonical(jvals[zero_i]),
         "actual_cleaned_result": cleaned_job_rows[zero_i]["observed_exposure"],
         "matches": cleaned_job_rows[zero_i]["observed_exposure"] == canonical(jvals[zero_i]),
         "case": "zero retained and valid numeric"},
        {"check_id": "J2", "dataset": "job_exposure", "row_index": max_i + 1,
         "field": "observed_exposure", "original_value": jr[max_i]["observed_exposure"],
         "expected_result": canonical(jvals[max_i]),
         "actual_cleaned_result": cleaned_job_rows[max_i]["observed_exposure"],
         "matches": cleaned_job_rows[max_i]["observed_exposure"] == canonical(jvals[max_i]),
         "case": "maximum observed numeric value"},
    ])
    tr = task["rows"]
    tvals = task["numeric_values"]
    cleaned_rows = read_csv(out / "task_penetration_cleaned.csv", task["headers"])
    rep = task["repeat_tasks"]
    occurrences = task["repeat_task_families"][REPEAT_TASK.casefold()]
    for label, occurrence in [("T1", occurrences[0]), ("T2", occurrences[4])]:
        idx, original_pen, original_task = occurrence
        cleaned = cleaned_rows[idx - 1]
        expected = f'{original_task} | {canonical(tvals[idx - 1])}'
        actual = f'{cleaned["task"]} | {cleaned["penetration"]}'
        checks.append({"check_id": label, "dataset": "task_penetration", "row_index": idx,
                       "field": "task / penetration", "original_value": f'{original_task} | {original_pen}',
                       "expected_result": expected,
                       "actual_cleaned_result": actual,
                       "matches": actual == expected,
                       "case": "repeated task capitalization variant retained"})
    tmax_i = next(i for i, v in enumerate(tvals) if v == max(tvals))
    cleaned_max = read_csv(out / "task_penetration_cleaned.csv", task["headers"])[tmax_i]["penetration"]
    checks.append({"check_id": "T3", "dataset": "task_penetration", "row_index": tmax_i + 1,
                   "field": "penetration", "original_value": tr[tmax_i]["penetration"],
                   "expected_result": canonical(tvals[tmax_i]),
                   "actual_cleaned_result": cleaned_max,
                   "matches": cleaned_max == canonical(tvals[tmax_i]),
                   "case": "maximum observed numeric value"})
    return checks


def run(output: Path, write_repro: bool = True) -> None:
    job = inspect("job_exposure")
    task = inspect("task_penetration")
    output.mkdir(parents=True, exist_ok=True)
    # Preserve source row order, all text, all values, and every record. Numeric
    # fields are validated as Decimal and emitted in canonical numeric form.
    cleaned = {}
    for name, detail in [("job_exposure", job), ("task_penetration", task)]:
        cleaned[name] = []
        for row, value in zip(detail["rows"], detail["numeric_values"]):
            copy = dict(row)
            copy[detail["numeric_field"]] = canonical(value)
            cleaned[name].append(copy)
        write_csv(output / f"{name}_cleaned.csv", detail["headers"], cleaned[name])

    sample = []
    def add_sample(name: str, indices: list[int]) -> None:
        detail = job if name == "job_exposure" else task
        for idx in indices:
            row = detail["rows"][idx - 1]
            sample.append({"dataset": name, "original_row_index": idx,
                           **{k: row[k] for k in detail["headers"]}})
    # Representative: first and last occupation rows, zero and maximum scores;
    # task zero, maximum, and all eight unresolved repeated records.
    add_sample("job_exposure", [1, next(i+1 for i,v in enumerate(job["numeric_values"]) if v == 0),
                                next(i+1 for i,v in enumerate(job["numeric_values"]) if v == max(job["numeric_values"])),
                                len(job["rows"])])
    add_sample("task_penetration", [1, next(i+1 for i,v in enumerate(task["numeric_values"]) if v == 0),
                                    next(i+1 for i,v in enumerate(task["numeric_values"]) if v == max(task["numeric_values"]))] +
               [i for i, _, _ in task["repeat_task_families"][REPEAT_TASK.casefold()]])
    write_csv(output / "cleaned_data_sample.csv",
              ["dataset", "original_row_index", "occ_code", "title", "observed_exposure", "task", "penetration"], sample)

    checks = build_checks(job, task, output)
    write_csv(output / "record_checks.csv", list(checks[0].keys()), checks)
    audit = {
        "source_files": {name: path.name for name, path in SOURCES.items()},
        "source_version_or_download_date": "Unknown; no source/version/date metadata was present in the project materials.",
        "datasets": {},
        "relationship": {"merge_performed": False, "shared_defensible_key": None,
                          "basis": "No shared identifier or documented crosswalk appears in the two source files."},
        "record_checks": {"count": len(checks), "all_match": all(c["matches"] for c in checks)},
    }
    for name, detail in [("job_exposure", job), ("task_penetration", task)]:
        output_rows = read_csv(output / f"{name}_cleaned.csv", detail["headers"])
        after_values = [number(r[detail["numeric_field"]], detail["numeric_field"], i+1)
                        for i, r in enumerate(output_rows)]
        repeated = detail["repeat_tasks"]
        duplicate_pair_details = []
        if name == "task_penetration":
            groups: dict[tuple[str, str], list[int]] = {}
            for i, row in enumerate(detail["rows"], 1):
                groups.setdefault((row["task"], row["penetration"]), []).append(i)
            duplicate_pair_details = [{"task": k[0], "penetration": k[1], "count": len(v), "row_indices": v}
                                      for k, v in groups.items() if len(v) > 1]
        audit["datasets"][name] = {
            "columns": detail["headers"],
            "inferred_types": {f: ("numeric (validated as Decimal)" if f == detail["numeric_field"] else "text") for f in detail["headers"]},
            "candidate_key": detail["key_field"],
            "rows_before": len(detail["rows"]), "rows_after": len(output_rows),
            "missing_before": detail["missing"], "missing_after": missing_counts(output_rows, detail["headers"]),
            "exact_duplicates_before": detail["exact_duplicates"],
            "exact_duplicates_after": duplicate_counts(output_rows, detail["headers"]),
            "candidate_key_repeat_groups": detail["key_repeat_groups"],
            "candidate_key_extra_rows": detail["key_extra_rows"],
            "numeric_type_validation": {"field": detail["numeric_field"], "conversion_failures_before": 0,
                                         "conversion_failures_after": 0, "all_values_numeric": True},
            "numeric_before": detail["numeric_stats"], "numeric_after": numeric_stats(after_values),
            "text_format_before": detail["text_format"],
            "repeat_task_groups": len(repeated),
            "casefolded_repeat_task_families": {
                key: {"count": len(value), "distinct_exact_texts": sorted({item[2] for item in value}),
                      "penetration_frequencies": dict(Counter(item[1] for item in value)),
                      "row_indices": [item[0] for item in value]}
                for key, value in detail["repeat_task_families"].items()
            },
            "exact_duplicate_pairs": duplicate_pair_details,
            "unresolved_repeat_task_counts": {k: len(v) for k, v in repeated.items()},
        }
    (output / "validation_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if write_repro:
        files = ["job_exposure_cleaned.csv", "task_penetration_cleaned.csv", "cleaned_data_sample.csv",
                 "record_checks.csv", "validation_audit.json"]
        with tempfile.TemporaryDirectory(prefix="dso576_repro_") as temp:
            second = Path(temp)
            subprocess.run([sys.executable, str(Path(__file__).resolve()), "--output-dir", str(second),
            "--skip-repro-check"], check=True, cwd=HERE)
            comparisons = {}
            for filename in files:
                first_bytes = (output / filename).read_bytes()
                second_bytes = (second / filename).read_bytes()
                comparisons[filename] = hashlib.sha256(first_bytes).hexdigest() == hashlib.sha256(second_bytes).hexdigest()
        (output / "reproducibility_check.json").write_text(json.dumps({
            "method": "Reran this script in a temporary output directory from the unchanged original CSVs; compared SHA-256 hashes.",
            "files_compared": comparisons, "passed": all(comparisons.values())
        }, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "outputs")
    parser.add_argument("--skip-repro-check", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    run(args.output_dir.resolve(), write_repro=not args.skip_repro_check)


if __name__ == "__main__":
    main()
