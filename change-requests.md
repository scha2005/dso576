# Team change requests - Module 9

## Claims

| Auditor | Feature | Number | Specific evidence contributed |
|---|---|---|---|
| Ella Liu | Occupation ranking, filters, and launch path | Implementation Priority Score | Independent Python average-rank calculation for all 755 scoreable occupations; four-row hand case; search-denominator example; repository-root launch failure at commit 2d0a434287fd92cc7ccf06c443d442c2524e7ca2 |
| Jade Yan | Occupation task drill-down | Positive-penetration task percentage | Independently count mapped and positive-penetration tasks; verify task filtering, sorting, and zero-task behavior; git rev-parse HEAD 86343342ab402922f2f30a93a39ddfed5feafa3b| 

No existing change-requests.md was found in the checked team repository or Module 9 course folder. This new log uses Claims, Findings, Evidence, and Requested changes. Teammate claims elsewhere were not available, so uniqueness across teammates is unconfirmed.

## CR-EL-01 - Make the documented entry point runnable from repository root

- Status: Open; reproducible local packaging/launch defect.
- User impact: A workforce planner or reviewer cannot obtain the ranking through the backend's default entry point from the repository root.
- Requirement: BUILD_SPEC.md acceptance check 1 requires a clean run without manual path edits.
- Evidence: From the team repository root run `python project/backend_analysis.py`. It exits 1 with `FileNotFoundError: [Errno 2] No such file or directory: 'data/processed/occupation_dashboard.csv'`. The CSV exists at `project/data/processed/occupation_dashboard.csv`. Function defaults at backend_analysis.py:559-561 are relative to the working directory; the __main__ block at lines 590-591 uses those defaults.
- Control: Calling build_dashboard_outputs with both explicit project/data/processed paths succeeds: 756 eligible occupations, 755 ranked, 25 in ranking_visual. Therefore the failure does not establish that the dataset is absent or the score is broken.
- Requested change: Resolve defaults relative to the backend file, or provide and document a root-level launcher with correct paths. Align README pipeline instructions with the checked repository; README references src.clean_and_join_data but no src directory is present in this checkout.
- Acceptance: From a fresh checkout's repository root, the documented command loads both canonical datasets and returns ranking outputs without manual path changes.

## CR-EL-02 - Explain the score's changing comparison population

- Status: Open; interpretation/communication request, not a demonstrated arithmetic bug.
- User impact: A user may compare scores from different filters as though they were absolute measures of AI implementation value.
- Evidence: audit_check.py uses four synthetic occupations with all four inputs increasing together. Alpha scores 25.0 among four occupations. Search='Alpha' leaves one complete row and the same occupation scores 100.0. Its raw exposure, employment, growth, and openings do not change. Filtering minimum employment to 200 changes Beta from 50.0 to 33.3333. These are expected results of within-view average percentile ranking.
- Requested change: Display the scoreable denominator and active filters next to each score; explicitly describe it as relative implementation priority within that comparison set. Explain that 100 is not a probability, replacement risk, or demonstrated ROI. Confirm with the team whether title search should redefine the comparison set or only narrow visible rows; update spec and tests together if behavior changes.
- Acceptance: Users can identify which occupations define the score; a single-row view clearly explains why a score can become 100. Search behavior is agreed and documented.

## Numerical finding requiring no formula change

The independent pure-Python rank calculation agrees with all 755 production scores, maximum absolute difference 2.842170943040401e-14. Synthetic checks cover weights, ties, incomplete input exclusion, filtering, Top N, and invalid ranges. Preserve the documented formula unless the team deliberately changes its policy weights or comparison population. See audit_check.py for reproducible evidence.

## CR-JY-01 - Clarify task coverage and missing percentages

- Status: Open; communication improvement. UI behavior not tested.
- Evidence: Accountants and Auditors has 7 positive-penetration tasks
  out of 23 mapped tasks (30.43%). Software Developers has no mapped
  tasks, and its percentage is missing.
- Requested change: Show the numerator and denominator beside the
  percentage. When no tasks are mapped, explain that task data is
  unavailable rather than implying no AI use.
- Acceptance: Show 7 / 23 (30.43%) for Accountants and Auditors.
  Show N/A with a coverage explanation for Software Developers.