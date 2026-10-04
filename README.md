# AI Job Exposure Dashboard

## Project Overview

This project explores AI exposure across occupations and job tasks using data from the Anthropic Economic Index.

## Data Source

Anthropic Economic Index  
Dataset folder: `labor_market_impacts`

Files used:
- `job_exposure.csv`
- `task_penetration.csv`

## Data Cleaning

The original source files were preserved without modification.

The cleaning process included:
- inspecting column types and identifiers
- checking text consistency
- investigating duplicate records
- checking missing values
- checking numeric ranges and suspicious values
- validating the cleaned datasets

No missing values or invalid numeric values were found.

In `task_penetration`, 8 records represented the same task after ignoring capitalization. All had the same penetration value of 0.7263. One record was retained and 7 redundant records were removed.

`job_exposure` remained unchanged at 756 rows.  
`task_penetration` changed from 17,998 to 17,991 rows.

## Cleaned Data

Cleaned files are stored in:

- `data/job_exposure_clean.csv`
- `data/task_penetration_clean.csv`

The cleaning workflow is documented in `cleaning_ella.ipynb`.