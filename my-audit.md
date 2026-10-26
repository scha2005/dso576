# Module 9 Individual Audit — Jade Yan

## App version
86343342ab402922f2f30a93a39ddfed5feafa3b

## Intended user and requirement
The intended user is an HR or workforce-planning manager identifying
tasks for potential AI pilots.

The task drill-down should return only the selected occupation's tasks,
sorted by penetration in descending order.


## Feature audit
I tested the backend task drill-down for Accountants and Auditors
(SOC 13-2011).

Expected and actual results:
- Return 23 tasks belonging only to SOC 13-2011: passed.
- Sort tasks by penetration descending: passed.
- With limit=3, return the first three tasks with penetration values
  0.954, 0.9373, and 0.9107: passed.

For Software Developers (SOC 15-1252), the backend returned no mapped
tasks. Both task counts were zero, and the task percentage was missing.


## Number audit
The metric is positive_penetration_task_pct:
the number of mapped tasks with penetration greater than zero divided
by the total number of mapped tasks.

Using a separate CSV-reading calculation, I counted 23 mapped tasks
and 7 positive-penetration tasks for Accountants and Auditors.

Expected: 7 / 23 = 0.30434782608695654, or approximately 30.43%.
Actual stored value: 0.30434782608695654.
The results matched.

This percentage describes mapped tasks. It is not the percentage of
workers who will lose their jobs or the percentage of work time
replaced by AI.

## Conclusion and limitations
The tested backend filtering, sorting, and limit behavior passed.
The accountant task percentage matched the independent calculation.

These checks do not establish that occupation-task mapping is complete,
that the upstream data is accurate, or that the interactive interface
works correctly. I did not test the interface.

## Requested improvement
Show the numerator and denominator alongside the percentage, such as
7 / 23 mapped tasks (30.43%).

For occupations without mapped tasks, explain that task data is
unavailable rather than implying no AI use.

Change-request ID: CR-JY-01

## Personal contribution and AI assistance
I ran the checks locally and reviewed the outputs.
AI helped draft the verification code and explain the results.

## Reproduction
Requires Python with pandas and numpy installed.
From the repository root, run:

```bash
python jade_audit_check.py
```

The script independently recalculates the accountant task percentage
from the CSV files and checks backend filtering, sorting, the top-three
limit, and zero-task behavior.


## Verification code
import csv
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "project"))
import backend_analysis as backend

DATA = ROOT / "project/data/processed"

# read CSV，重新计算会计的任务占比
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