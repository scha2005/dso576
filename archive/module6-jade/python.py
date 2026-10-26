"""Module 6: clean the two supplied datasets without changing the originals.

Setup: python -m pip install pandas==2.2.3 numpy==2.3.5
Run:   python python.py
Keep this script and both original CSV files in the same folder.
Final data goes in cleaning_output/final-cleanoutput/; audits stay in cleaning_output/.
No network access is needed.
"""

from pathlib import Path
from collections import Counter
from decimal import Decimal
import csv
import hashlib
import json
import shutil

import numpy as np
import pandas as pd


BASE = Path(__file__).resolve().parent
OUT = BASE / "cleaning_output"
FILES = {
    "job_exposure": ("job_exposure(1).csv", "occ_code", "observed_exposure"),
    "task_penetration": ("task_penetration(1).csv", "task", "penetration"),
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(filename, value):
    (OUT / filename).write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def save_csv(df, filename):
    df.to_csv(OUT / filename, index=False, encoding="utf-8", lineterminator="\n")


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "raw").mkdir(exist_ok=True)

    # Define rules and expected results BEFORE applying transformations.
    rules = [
        {"rule": "Preserve source bytes and keep identifiers as strings.",
         "reason": "Keep provenance and identifier formatting.",
         "check": "Compare SHA-256 before/after; check occupation-code syntax."},
        {"rule": "Trim and collapse whitespace; preserve case and punctuation.",
         "reason": "Avoid erasing meaningful label differences.",
         "check": "Log every changed text cell and flag case-only task variants."},
        {"rule": "Convert rate fields explicitly; retain blanks as missing and real zeros as zero.",
         "reason": "Missing observations are not measured zeros.",
         "check": "Count missing values and failed conversions; reject invalid or infinite rates."},
        {"rule": "Remove exact duplicate business rows, retaining the first source record.",
         "reason": "The chosen analytical unit is a distinct task description, not source-row frequency.",
         "check": "Independently count duplicates with csv/Counter; reconcile removed rows and rates."},
        {"rule": "Keep case-only task variants; stop on conflicting repeated keys.",
         "reason": "There are no authoritative task IDs to resolve uncertain identity.",
         "check": "Write case_variant_review.csv and verify key uniqueness after exact deduplication."},
        {"rule": "Require rates in [0,1]; retain valid boundaries and high observations.",
         "reason": "An unusual value is not necessarily an error; bounds are provisional without a codebook.",
         "check": "Check all numeric values and occupation codes; no date columns exist."},
        {"rule": "Do not merge the two tables. Use unweighted, nonmissing-rate denominators.",
         "reason": "No shared occupation-task key or population weights are supplied.",
         "check": "Report metric denominators and reconcile occupation-group counts."},
    ]
    save_json("cleaning_rules.json", rules)

    # source_record means 1-based data record, excluding the header, not file line.
    expectations = [
        {"case": "C1", "dataset": "job_exposure", "source_record": 3,
         "expected_action": "keep", "expected_rate": "0.0000", "expected_key": "11-1031",
         "reason": "Legislators has a real zero; do not replace it with missing."},
        {"case": "C2", "dataset": "job_exposure", "source_record": 74,
         "expected_action": "keep", "expected_rate": "0.7451", "expected_key": "15-1251",
         "reason": "Computer Programmers has a high but valid observed exposure."},
        {"case": "C3", "dataset": "task_penetration", "source_record": 342,
         "expected_action": "keep", "expected_rate": "1.0000",
         "expected_key": "Advise customers on use and care of merchandise.",
         "reason": "One is a valid boundary under the provisional proportion interpretation."},
        {"case": "C4", "dataset": "task_penetration", "source_record": 17891,
         "expected_action": "remove_exact_duplicate", "expected_rate": "0.7263",
         "expected_retained_record": 17890,
         "reason": "This exact duplicate must be removed while its first occurrence remains."},
        {"case": "C5", "dataset": "task_penetration", "source_record": 17894,
         "expected_action": "keep", "expected_rate": "0.7263", "expected_case_flag": True,
         "reason": "Keep lowercase web and flag its case-only difference from Web."},
    ]
    save_json("record_expectations.json", expectations)

    audits, originals, cleaned = {}, {}, {}
    source_manifest, column_audit, removals, changes, metrics, selections = [], [], [], [], [], []
    case_variants = pd.DataFrame()

    for name, (filename, key, rate) in FILES.items():
        source = BASE / filename
        if not source.exists():
            raise FileNotFoundError(f"Put {filename} next to python.py: {BASE}")
        before_hash = sha256(source)
        backup = OUT / "raw" / filename
        if backup.exists() and sha256(backup) != before_hash:
            raise ValueError(f"Existing raw backup differs: {backup}. Review it before rerunning.")
        if not backup.exists():
            shutil.copyfile(source, backup)
        source_manifest.append({"file": filename, "sha256": before_hash,
                                "source": "User-supplied CSV attachment",
                                "publisher_version": "Not provided",
                                "original_download_date": "Not provided"})

        raw = pd.read_csv(source, dtype="string", keep_default_na=False)
        originals[name] = raw.copy()
        text_columns = ["occ_code", "title"] if name == "job_exposure" else ["task"]
        business_columns = text_columns + [rate]
        if list(raw.columns) != business_columns:
            raise ValueError(f"Unexpected columns in {filename}: {list(raw.columns)}")

        with source.open(encoding="utf-8-sig", newline="") as handle:
            records = list(csv.DictReader(handle))
        counts = Counter(tuple(row[c] for c in business_columns) for row in records)
        independent_duplicates = sum(n - 1 for n in counts.values())
        assert independent_duplicates == int(raw.duplicated().sum())

        df = raw.copy()
        text_change_counts = {}
        for col in text_columns:
            df[col] = df[col].str.replace(r"\s+", " ", regex=True).str.strip()
            changed = raw[col] != df[col]
            text_change_counts[col] = int(changed.sum())
            for idx in raw.index[changed]:
                changes.append({"dataset": name, "source_record": int(idx + 1),
                                "column": col, "before": raw.at[idx, col], "after": df.at[idx, col]})

        df = df.replace(r"^\s*$", pd.NA, regex=True)
        numeric = pd.to_numeric(df[rate], errors="coerce").astype("float64")
        failures = int((df[rate].notna() & numeric.isna()).sum())
        if failures:
            raise ValueError(f"{filename}: {failures} nonblank values cannot be converted to numbers.")
        if not np.isfinite(numeric.dropna()).all() or not numeric.dropna().between(0, 1).all():
            raise ValueError(f"{filename}: nonfinite or out-of-range rates require review.")
        df[rate] = numeric
        if name == "job_exposure" and not df[key].str.fullmatch(r"\d{2}-\d{4}", na=True).all():
            raise ValueError("Malformed occupation code: review the original data.")
        df["source_record"] = np.arange(1, len(df) + 1)

        repeated = df[key].notna() & df[key].duplicated(keep=False)
        for _, group in df.loc[repeated].groupby(key):
            if len(group[business_columns].drop_duplicates()) > 1:
                raise ValueError(f"Conflicting repeated key in {filename}; do not choose a value arbitrarily.")

        duplicate = df.duplicated(subset=business_columns, keep="first")
        seen = {}
        for _, row in df.iterrows():
            signature = tuple(None if pd.isna(row[c]) else row[c] for c in business_columns)
            if signature in seen:
                removals.append({"dataset": name, "removed_source_record": int(row.source_record),
                                 "kept_source_record": seen[signature], "key": row[key],
                                 "removed_rate": None if pd.isna(row[rate]) else float(row[rate])})
            else:
                seen[signature] = int(row.source_record)
        result = df.loc[~duplicate].copy().reset_index(drop=True)
        cleaned[name] = result
        save_csv(result, f"{name}_clean.csv")

        # Decimal controls use original CSV tokens, independently of pandas sums.
        total_before = sum((Decimal(r[rate]) for r in records if r[rate].strip()), Decimal(0))
        removed_ids = set(df.loc[duplicate, "source_record"].astype(int))
        total_removed = sum((Decimal(records[i - 1][rate]) for i in removed_ids
                             if records[i - 1][rate].strip()), Decimal(0))
        with (OUT / f"{name}_clean.csv").open(encoding="utf-8", newline="") as handle:
            output_records = list(csv.DictReader(handle))
        total_after = sum((Decimal(r[rate]) for r in output_records if r[rate].strip()), Decimal(0))
        assert total_before - total_removed == total_after
        assert len(raw) - int(duplicate.sum()) == len(result)
        assert sha256(source) == sha256(backup) == before_hash
        for row in output_records:
            original = records[int(row["source_record"]) - 1]
            if row[rate].strip():
                assert Decimal(row[rate]) == Decimal(original[rate])

        for col in business_columns:
            column_audit.append({"dataset": name, "column": col, "type_after": str(result[col].dtype),
                                 "missing_before": int(raw[col].str.strip().eq("").sum()),
                                 "missing_after": int(result[col].isna().sum()),
                                 "text_changes": text_change_counts.get(col, 0),
                                 "failed_conversions": failures if col == rate else 0})
        audits[name] = {
            "rows_before": len(raw), "rows_after": len(result), "removed_rows": int(duplicate.sum()),
            "exact_duplicate_excess_before": independent_duplicates,
            "exact_duplicate_excess_after": int(result.duplicated(business_columns).sum()),
            "repeated_key_groups_before": int(df.loc[repeated, key].nunique()),
            "rows_in_repeated_key_groups_before": int(repeated.sum()),
            "repeated_key_excess_before": int(df.loc[df[key].notna(), key].duplicated().sum()),
            "repeated_key_excess_after": int(result.loc[result[key].notna(), key].duplicated().sum()),
            "conflicting_keys": 0, "invalid_rates": 0,
            "sum_before": str(total_before), "sum_removed": str(total_removed), "sum_after": str(total_after),
            "source_hash_unchanged": True, "all_retained_rates_match_raw": True,
        }
        values = result[rate]
        valid_n = int(values.notna().sum())
        metrics.append({"dataset": name, "rows": len(result), "valid_n": valid_n,
                        "missing_n": int(values.isna().sum()), "zero_n": int(values.eq(0).sum()),
                        "one_n": int(values.eq(1).sum()), "positive_n": int(values.gt(0).sum()),
                        "mean": float(values.mean()) if valid_n else None,
                        "positive_share": float(values.gt(0).sum() / valid_n) if valid_n else None})
        print(f"{filename}: {len(raw):,} -> {len(result):,} rows; {int(duplicate.sum())} removed")

    tasks = cleaned["task_penetration"]
    folded = tasks.task.str.casefold()
    case_variants = tasks.loc[folded.notna() & folded.duplicated(keep=False)].copy()
    case_variants["decision"] = "Keep: case-only difference; authoritative task IDs unavailable"
    save_csv(case_variants, "case_variant_review.csv")

    # Sensitivity only: the primary cleaned output retains the case-only variants.
    sensitive = tasks.assign(casefold_key=folded)
    for _, group in sensitive.groupby("casefold_key"):
        if group.penetration.nunique(dropna=False) > 1:
            raise ValueError("Case-only variants have conflicting rates; review sensitivity calculation.")
    sensitive = sensitive.drop_duplicates("casefold_key")
    audits["casefold_sensitivity"] = {"primary_rows": len(tasks), "primary_mean": float(tasks.penetration.mean()),
                                     "sensitivity_rows": len(sensitive), "sensitivity_mean": float(sensitive.penetration.mean())}

    checks = []
    for expected in expectations:
        name, rid = expected["dataset"], expected["source_record"]
        _, key, rate = FILES[name]
        original = originals[name].iloc[rid - 1].to_dict()
        retained = cleaned[name].loc[cleaned[name].source_record.eq(rid)]
        action = "keep" if len(retained) else "remove_exact_duplicate"
        kept_id = rid if len(retained) else next(r["kept_source_record"] for r in removals
                                                if r["dataset"] == name and r["removed_source_record"] == rid)
        actual = cleaned[name].loc[cleaned[name].source_record.eq(kept_id)].iloc[0]
        case_flag = name == "task_penetration" and rid in set(case_variants.source_record)
        passed = action == expected["expected_action"] and Decimal(str(actual[rate])) == Decimal(expected["expected_rate"])
        passed = passed and actual[key] == expected.get("expected_key", original[key])
        passed = passed and kept_id == expected.get("expected_retained_record", rid)
        passed = passed and case_flag == expected.get("expected_case_flag", False)
        checks.append({**expected, "original": original, "actual_action": action,
                       "actual_rate": float(actual[rate]), "actual_key": actual[key],
                       "actual_retained_record": int(kept_id), "actual_case_flag": case_flag, "pass": bool(passed)})
    save_json("record_checks.json", checks)
    assert all(c["pass"] for c in checks), "A pre-specified record check failed; inspect record_checks.json."

    # Exactly 50 cleaned rows total: hard cases first, then source-order coverage.
    for name, result in cleaned.items():
        _, _, rate = FILES[name]
        selected = {}
        for case in expectations:
            if case["dataset"] == name:
                rid = case.get("expected_retained_record", case["source_record"])
                selected.setdefault(rid, []).append(case["case"] + " retained representative")
        if name == "task_penetration":
            for rid in case_variants.source_record:
                selected.setdefault(int(rid), []).append("case-only variant")
        for label, idx in [("minimum", result[rate].idxmin()), ("maximum", result[rate].idxmax())]:
            selected.setdefault(int(result.loc[idx, "source_record"]), []).append(label)
        for rid in result.source_record:
            if len(selected) >= 25:
                break
            selected.setdefault(int(rid), ["source-order coverage"])
        sample = result.loc[result.source_record.isin(selected)].sort_values("source_record")
        assert len(sample) == 25
        save_csv(sample, f"{name}_sample.csv")
        selections.extend({"dataset": name, "source_record": int(rid), "reason": "; ".join(selected[rid])}
                          for rid in sample.source_record)

    jobs = cleaned["job_exposure"].copy()
    jobs["major_group"] = jobs.occ_code.str[:2].fillna("Unknown")
    groups = jobs.groupby("major_group", dropna=False).observed_exposure.agg(rows="size", valid_n="count", mean="mean").reset_index()
    assert int(groups.rows.sum()) == len(jobs)
    assert np.isclose(np.average(groups["mean"], weights=groups.valid_n), jobs.observed_exposure.mean())
    save_csv(groups.sort_values(["mean", "major_group"], ascending=[False, True]), "occupation_groups.csv")
    save_csv(pd.DataFrame(column_audit), "column_audit.csv")
    save_csv(pd.DataFrame(removals), "duplicate_removed.csv")
    save_csv(pd.DataFrame(changes, columns=["dataset", "source_record", "column", "before", "after"]), "text_changes.csv")
    save_csv(pd.DataFrame(metrics), "metrics.csv")
    save_csv(pd.DataFrame(selections), "sample_selection.csv")
    save_json("source_manifest.json", source_manifest)
    save_json("dataset_audit.json", audits)

    # Move the verified full datasets into their final delivery folder.
    final_dir = OUT / "final-cleanoutput"
    final_dir.mkdir(exist_ok=True)
    for name in FILES:
        filename = f"{name}_clean.csv"
        (OUT / filename).replace(final_dir / filename)

    print("PASS: five record checks, source preservation, row counts and rate totals.")
    print(f"Outputs: {OUT}")
    print(f"Final cleaned datasets: {final_dir}")
    print("No merge performed. Sources/version, metric definitions and task identity still need confirmation.")


if __name__ == "__main__":
    main()
