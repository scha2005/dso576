# Verification of the `occ_code` Text-Preservation Suggestion

## Codex suggestion

> Keep as text; do not strip punctuation, cast to numbers, or reformat.

The suggestion applies to `occ_code` in `job_exposure.csv`.

## Why I checked it

I checked what the occupation codes meant in the context of the data before accepting the suggestion. The codes identify jobs, so changing their formatting or treating them as numeric measurements could damage their use as identifiers. I also considered how the type would support comparing different jobs.

## My independent check

I checked the type of the data and determined that text was the best data type to compare different jobs against each other. I inspected various rows to understand what the occupation codes represented and whether they were unique. I found that the codes were unique and acted as identifiers for the jobs.

## Result and decision

**Decision: Accepted.** Keep `occ_code` as text, preserving its original characters and punctuation. Do not cast it to a number or reformat it.

The workflow profile independently records 756 nonmissing `occ_code` values and 756 distinct values. The manual verification at `job_exposure.csv` CSV line 2 (`11-1011`) matched the expected preserved value in the cleaned output. See [data_profile.md](data_profile.md), [manual_verification_sample.md](manual_verification_sample.md), and [cleaning_decision_log_updated.md](cleaned/cleaning_decision_log_updated.md).

This verification supports identifier preservation for `occ_code`; it does not authorize standardizing occupation titles or task descriptions.
