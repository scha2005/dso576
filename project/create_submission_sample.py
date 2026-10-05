#!/usr/bin/env python3
"""Create a small, traceable submission sample from the cleaned project CSVs."""

from __future__ import annotations

import csv
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
CLEANED_DIR = PROJECT_DIR / "cleaned"
OUTPUT_DIR = PROJECT_DIR / "submission_sample"


def get_selection(filename: str) -> list[tuple[int, str, str]]:
    """Return (CSV physical line, category, reason), with header as line 1."""
    if filename == "job_exposure_cleaned.csv":
        picks = [
            (2, "manual verification / identifier", "Preselected text-preservation check: retain occ_code 11-1011 exactly as text."),
            (4, "manual verification / zero negative control", "Preselected missingness negative control: complete record with observed_exposure 0.0; no source row is missing."),
            (75, "unusual valid value", "High observed_exposure value (0.7451); retained as a valid observed value."),
            (3, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (5, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (6, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (7, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (8, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (9, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (10, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (11, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (12, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (13, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (14, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (15, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (16, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (17, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (18, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (19, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (20, "ordinary comparison", "Ordinary early-file occupation for comparison."),
            (300, "ordinary comparison", "Middle-file occupation for comparison."),
            (500, "ordinary comparison", "Middle-file occupation for comparison."),
            (700, "ordinary comparison", "Late-file occupation for comparison."),
        ]
    elif filename == "task_penetration_cleaned.csv":
        picks = [
            (2, "manual verification / merge-key probe", "Preselected merge probe: task record has no occupation code or title; do not assign it to a job."),
            (343, "manual verification / upper boundary", "Preselected upper-bound record: penetration is 1.0 and is retained unchanged."),
            (17891, "manual verification / exact duplicate group", "First instance of an exact repeated task row; all occurrences are retained."),
            (17892, "exact duplicate group", "Second identical occurrence; demonstrates duplicate retention."),
            (17893, "exact duplicate group", "Third identical occurrence; demonstrates duplicate retention."),
            (17894, "exact duplicate group", "Fourth identical occurrence; demonstrates duplicate retention."),
            (17895, "capitalization variant / repeated task", "First occurrence of case-only Web/web task-text variant; text is preserved."),
            (17896, "capitalization variant / repeated task", "Repeated occurrence of the case-only task-text variant; text is preserved."),
            (17897, "capitalization variant / repeated task", "Repeated occurrence of the case-only task-text variant; text is preserved."),
            (17898, "capitalization variant / repeated task", "Repeated occurrence of the case-only task-text variant; text is preserved."),
            (3, "ordinary comparison", "Ordinary early-file task for comparison."),
            (4, "ordinary comparison", "Ordinary early-file task for comparison."),
            (5, "ordinary comparison", "Ordinary early-file task for comparison."),
            (6, "ordinary comparison", "Ordinary early-file task for comparison."),
            (7, "ordinary comparison", "Ordinary early-file task for comparison."),
            (8, "ordinary comparison", "Ordinary early-file task for comparison."),
            (9, "ordinary comparison", "Ordinary early-file task for comparison."),
            (10, "ordinary comparison", "Ordinary early-file task for comparison."),
            (100, "ordinary comparison", "Early-file task outside the opening block for comparison."),
            (500, "ordinary comparison", "Early-file task outside the opening block for comparison."),
            (1000, "ordinary comparison", "Task from a different file section for comparison."),
            (5000, "ordinary comparison", "Task from a different file section for comparison."),
            (9000, "ordinary comparison", "Task from a different file section for comparison."),
            (12000, "ordinary comparison", "Task from a different file section for comparison."),
            (17000, "ordinary comparison", "Late-file task for comparison."),
        ]
    else:
        raise ValueError(filename)
    return sorted(picks, key=lambda item: item[0])


def extract(source: Path, selections: list[tuple[int, str, str]]) -> tuple[list[str], list[tuple[int, dict[str, str], str, str]]]:
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        wanted = {line: (category, reason) for line, category, reason in selections}
        found: dict[int, tuple[dict[str, str], str, str]] = {}
        for line_number, row in enumerate(reader, start=2):
            if line_number in wanted:
                category, reason = wanted[line_number]
                found[line_number] = (row, category, reason)
    absent = sorted(set(wanted) - set(found))
    assert not absent, f"Selected source line(s) absent from {source.name}: {absent}"
    return columns, [(line, *found[line]) for line, _, _ in selections]


def write_csv(path: Path, columns: list[str], items: list[tuple[int, dict[str, str], str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(row for _, row, _, _ in items)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_rows: list[tuple[str, int, dict[str, str], str, str]] = []
    counts: dict[str, int] = {}
    for source_name, sample_name in [
        ("job_exposure_cleaned.csv", "job_exposure_sample.csv"),
        ("task_penetration_cleaned.csv", "task_penetration_sample.csv"),
    ]:
        source = CLEANED_DIR / source_name
        assert source.is_file(), f"Missing cleaned input: {source}"
        picks = get_selection(source_name)
        columns, items = extract(source, picks)
        assert columns, f"No columns found in {source}"
        write_csv(OUTPUT_DIR / sample_name, columns, items)
        counts[sample_name] = len(items)
        all_rows.extend((sample_name, line, row, category, reason) for line, row, category, reason in items)

    total = len(all_rows)
    assert total <= 50, f"Submission sample exceeds 50 rows: {total}"

    with (OUTPUT_DIR / "sample_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["sample_file", "source_cleaned_csv_line", "selection_category", "selection_reason"])
        for sample_file, line, _, category, reason in all_rows:
            writer.writerow([sample_file, line, category, reason])

    difficult = [row for row in all_rows if row[3] != "ordinary comparison"]
    lines = [
        "# Submission Sample", "",
        f"Created: {__import__('datetime').datetime.now().astimezone().isoformat(timespec='seconds')}", "",
        f"This submission sample contains **{total} cleaned data rows total** (maximum allowed: 50), split by original dataset grain.", "",
        "## Sample files", "",
        f"- [`job_exposure_sample.csv`](job_exposure_sample.csv): {counts['job_exposure_sample.csv']} rows; original job columns retained.",
        f"- [`task_penetration_sample.csv`](task_penetration_sample.csv): {counts['task_penetration_sample.csv']} rows; original task columns retained.",
        "- [`sample_manifest.csv`](sample_manifest.csv): source line, category, and selection rationale for every sample row.", "",
        "The sample was generated from `project/cleaned/` by `project/create_submission_sample.py`. It does not join the two datasets and does not add synthetic values.", "",
        "## Why difficult records were selected", "",
        "| Sample file and source CSV line | Selected record / challenge | Reason selected |", "|---|---|---|"]
    for sample_file, line, row, category, reason in difficult:
        identifier = row.get("occ_code") or row.get("task", "")
        lines.append(f"| `{sample_file}`, line {line} | `{identifier}` ({category}) | {reason} |")
    lines += [
        "", "## Coverage notes", "",
        "- The five manual-verification cases are included: occupation code `11-1011`; the repeated task row; occupation `11-1031` with zero exposure; the task-side merge-key probe; and the task with penetration `1.0`.",
        "- The repeated task group includes all four exact occurrences of each of the `Web` and `web` capitalization variants. Exact duplicate handling remains unresolved, so every occurrence is retained.",
        "- There are no missing or formerly missing source values to sample. The complete zero-valued occupation record is included as a negative control; no synthetic missing values were introduced.",
        "- No occupation-linked task rows or actual merge matches can be supplied: `task_penetration.csv` has no occupation code/title key or documented crosswalk. The task merge probe is retained as an unassigned task record, not falsely matched.",
        "- An upper-bound task penetration of `1.0`, a high occupation exposure value, and several ordinary early-, middle-, and late-file rows are included for comparison.",
        "- The data are occupation/task measures without personal-level records or direct identifiers. Original source values are retained in these samples.", ""]
    (OUTPUT_DIR / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {total} sample rows to {OUTPUT_DIR}")
    for name, count in counts.items():
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
