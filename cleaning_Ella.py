import pandas as pd

# --------------------------------------------------
# 1. Load original data
# --------------------------------------------------

job_exposure = pd.read_csv("data/job_exposure.csv")
task_penetration = pd.read_csv("data/task_penetration.csv")

print("Original data loaded:")
print("job_exposure:", job_exposure.shape)
print("task_penetration:", task_penetration.shape)


# --------------------------------------------------
# 2. Create working copies
# --------------------------------------------------

job_exposure_clean = job_exposure.copy()
task_penetration_clean = task_penetration.copy()


# --------------------------------------------------
# 3. Standardize task text for duplicate comparison
# --------------------------------------------------

task_key = (
    task_penetration_clean["task"]
    .str.strip()
    .str.casefold()
)


# --------------------------------------------------
# 4. Remove redundant task records
# --------------------------------------------------

task_penetration_clean = (
    task_penetration_clean
    .loc[~task_key.duplicated()]
    .reset_index(drop=True)
)


# --------------------------------------------------
# 5. Validate cleaned data
# --------------------------------------------------

clean_task_key = (
    task_penetration_clean["task"]
    .str.strip()
    .str.casefold()
)

# Check missing values
assert job_exposure_clean.isna().sum().sum() == 0
assert task_penetration_clean.isna().sum().sum() == 0

# Check duplicates
assert job_exposure_clean["occ_code"].duplicated().sum() == 0
assert clean_task_key.duplicated().sum() == 0

# Check numeric ranges
assert job_exposure_clean["observed_exposure"].between(0, 1).all()
assert task_penetration_clean["penetration"].between(0, 1).all()

# Check occupation code format
assert (
    job_exposure_clean["occ_code"]
    .str.match(r"^\d{2}-\d{4}$")
    .all()
)

print("\nValidation passed.")

print(
    "job_exposure:",
    len(job_exposure),
    "->",
    len(job_exposure_clean)
)

print(
    "task_penetration:",
    len(task_penetration),
    "->",
    len(task_penetration_clean)
)


# --------------------------------------------------
# 6. Save cleaned outputs
# --------------------------------------------------

job_exposure_clean.to_csv(
    "data/job_exposure_clean.csv",
    index=False
)

task_penetration_clean.to_csv(
    "data/task_penetration_clean.csv",
    index=False
)

print("\nCleaned files saved successfully.")