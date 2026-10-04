"""Validate project CSVs and deduplicate exact rows; Python standard library only."""
import csv
import hashlib
import json
import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "cleaned"
SPECS = {
    "job_exposure": (["occ_code", "title", "observed_exposure"], "occ_code"),
    "task_penetration": (["task", "penetration"], "task"),
}


def write_csv(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def metrics(rows, column):
    numbers = [Decimal(row[column]) for row in rows]
    total = sum(numbers, Decimal(0))
    return {"count": len(numbers), "sum": str(total),
            "mean": str(total / len(numbers)) if numbers else None,
            "min": str(min(numbers)) if numbers else None,
            "max": str(max(numbers)) if numbers else None,
            "zeros": sum(value == 0 for value in numbers)}


def main():
    # Rules are documented in CLEANING_README.md before application.
    prepared, audit, report, checks = {}, [], {}, []
    for name, (columns, key) in SPECS.items():
        source = ROOT / f"{name}.csv"
        original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        with source.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != columns:
                raise ValueError(f"Unexpected schema in {source.name}")
            rows = list(reader)
        cleaned, seen, key_values = [], set(), {}
        metric = columns[-1]
        for line, original in enumerate(rows, 2):
            if set(original) != set(columns) or any(v is None for v in original.values()):
                raise ValueError(f"Malformed CSV record: {name}:{line}")
            row = {c: original[c].strip() for c in columns}
            if any(not value for value in row.values()):
                raise ValueError(f"Missing required value: {name}:{line}")
            try:
                value = Decimal(row[metric])
            except InvalidOperation as error:
                raise ValueError(f"Invalid number: {name}:{line}") from error
            if not value.is_finite() or not Decimal(0) <= value <= Decimal(1):
                raise ValueError(f"Score outside [0, 1]: {name}:{line}")
            if name == "job_exposure" and not re.fullmatch(r"\d{2}-\d{4}", row[key]):
                raise ValueError(f"Invalid occupation code: {name}:{line}")
            signature = tuple(row[c] for c in columns)
            if row[key] in key_values and key_values[row[key]] != signature:
                raise ValueError(f"Conflicting repeated key: {name}:{line}")
            key_values[row[key]] = signature
            if row != original:
                audit.append({"dataset": name, "source_record": line - 1,
                              "action": "trim_outer_whitespace", "original": json.dumps(original),
                              "result": json.dumps(row)})
            if signature in seen:
                audit.append({"dataset": name, "source_record": line - 1,
                              "action": "remove_exact_duplicate", "original": json.dumps(original),
                              "result": "First occurrence retained"})
                continue
            seen.add(signature)
            cleaned.append(row)
        duplicates = len(rows) - len({tuple(r[c] for c in columns) for r in rows})
        counts = Counter(r[key] for r in rows)
        info = {
            "source_sha256": original_hash, "rows_before": len(rows), "rows_after": len(cleaned),
            "removed_rows": len(rows) - len(cleaned), "exact_duplicate_excess_before": duplicates,
            "repeated_key_groups_before": sum(n > 1 for n in counts.values()),
            "repeated_key_excess_before": sum(n - 1 for n in counts.values()),
            "missing_before": {c: sum(not r[c].strip() for r in rows) for c in columns},
            "missing_after": {c: sum(not r[c] for r in cleaned) for c in columns},
            "failed_numeric_conversions": 0, "out_of_range_scores": 0,
            "metrics_before": metrics(rows, metric), "metrics_after": metrics(cleaned, metric),
        }
        info["score_sum_removed"] = str(Decimal(info["metrics_before"]["sum"]) - Decimal(info["metrics_after"]["sum"]))
        assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash
        report[name] = info
        prepared[name] = (columns, rows, cleaned)

    # Expectations use the input records and declared rules, not output values.
    selections = [("job_exposure", "11-1031"), ("job_exposure", "15-1251")]
    tasks = prepared["task_penetration"][1]
    selections += [("task_penetration", "Advise customers on use and care of merchandise.")]
    selections += [("task_penetration", t) for t, n in Counter(r["task"] for r in tasks).items() if n > 1]
    for name, key_value in selections:
        columns, rows, cleaned = prepared[name]
        key = SPECS[name][1]
        originals = [r for r in rows if r[key] == key_value]
        expected = [{c: originals[0][c].strip() for c in columns}]
        actual = [r for r in cleaned if r[key] == key_value]
        checks.append({"dataset": name, "original": originals[0], "original_count": len(originals),
                       "expected": expected, "actual": actual, "matches": actual == expected,
                       "reason": "Retain score and case; retain one occurrence of an exact row."})
        assert actual == expected
    OUT.mkdir(exist_ok=True)
    for name, (columns, rows, cleaned) in prepared.items():
        write_csv(OUT / f"{name}_clean.csv", columns, cleaned)
        selected_keys = {k for dataset, k in selections if dataset == name}
        key = SPECS[name][1]
        sample = [r for r in cleaned if r[key] in selected_keys]
        sample += [r for r in cleaned if r[key] not in selected_keys][:25 - len(sample)]
        write_csv(OUT / f"{name}_sample.csv", columns, sample)
    write_csv(OUT / "cleaning_audit.csv", ["dataset", "source_record", "action", "original", "result"], audit)
    for filename, value in [("validation.json", report), ("record_checks.json", checks)]:
        (OUT / filename).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
