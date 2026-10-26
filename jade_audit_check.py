import csv
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "project"))
import backend_analysis as backend

DATA = ROOT / "project/data/processed"

# 独立读取 CSV，重新计算会计的任务占比
with open(DATA / "occupation_tasks.csv", encoding="utf-8") as f:
    rows = [
        row for row in csv.DictReader(f)
        if row["soc_code"] == "13-2011"
    ]

positive = sum(float(row["penetration"]) > 0 for row in rows)
expected = positive / len(rows)

with open(DATA / "occupation_dashboard.csv", encoding="utf-8") as f:
    accountant = next(
        row for row in csv.DictReader(f)
        if row["soc_code"] == "13-2011"
    )

actual = float(accountant["positive_penetration_task_pct"])
assert len(rows) == 23
assert positive == 7
assert math.isclose(expected, actual, rel_tol=0, abs_tol=1e-9)
print(f"PASS: independent calculation = {positive}/{len(rows)} = {expected}")

# 检查后端功能
tasks = backend.load_task_data(DATA / "occupation_tasks.csv")
occupations = backend.load_occupation_data(DATA / "occupation_dashboard.csv")

detail = backend.get_task_drilldown(tasks, "13-2011")
assert len(detail) == 23
assert detail["soc_code"].eq("13-2011").all()
print("PASS: occupation filtering")

assert detail["penetration"].is_monotonic_decreasing
print("PASS: descending task order")

top3 = backend.get_task_drilldown(tasks, "13-2011", limit=3)
assert len(top3) == 3
assert top3.equals(detail.head(3))
for actual_value, expected_value in zip(
    top3["penetration"], [0.954, 0.9373, 0.9107]
):
    assert math.isclose(
        actual_value, expected_value, rel_tol=0, abs_tol=1e-9
    )
print("PASS: top-three limit and values")

empty_detail = backend.get_task_drilldown(tasks, "15-1252")
software = occupations.loc[
    occupations["soc_code"] == "15-1252"
].iloc[0]

assert empty_detail.empty
assert software["mapped_task_count"] == 0
assert software["positive_penetration_task_count"] == 0
assert pd.isna(software["positive_penetration_task_pct"])
print("PASS: zero mapped tasks produce a missing percentage")

print("All checks passed.")