# Dataset Profile

Generated: 2026-10-05T00:06:37-07:00

This report describes the source files without modifying them.

## `job_exposure.csv`

### Source and provenance

- Source: Anthropic Economic Index (project brief; file-level attribution not independently verified)
- Source URL: https://huggingface.co/datasets/Anthropic/EconomicIndex
- Dataset/file version: Unknown / not recorded
- Download date: Unknown / not recorded
- Local file modified time (not a download date): 2026-09-17T17:15:58-07:00
- File: `C:\Users\sumed\dso576\project\job_exposure.csv`

### Shape

- Rows: 756
- Columns: 3
- Exact duplicate rows (all columns equal): 0

### Columns

| Column | Inferred type | Example values | Missing values |
|---|---|---|---:|
| `occ_code` | string (identifier; leading zeros preserved) | 11-1011; 11-1021; 11-1031 | 0 |
| `title` | string | Chief Executives; General and Operations Managers; Legislators | 0 |
| `observed_exposure` | numeric | 0.0333; 0.1378; 0.0 | 0 |

### Likely identifier checks

- `occ_code`: 756 distinct values; 0 repeated occurrences beyond the first; 0 blank values.

### Numeric conversion checks

- `observed_exposure`: 0 failed conversions; numeric range 0 to 0.7451.

### Date conversion checks

No date-like columns found; no date conversions attempted.

### Invalid, impossible, or suspicious values

- `observed_exposure`: 411 of 756 valid values (54.4%) are zero; review whether this concentration is expected by the source methodology.

### Profiling notes

- Profiling only: no values were changed, normalized, imputed, or removed.
- All CSV fields were read as text first; numeric/date parsing was used only for checks, preserving leading zeros.
- Proportion-range checks assume these named metrics are fractions on a 0..1 scale; confirm against source documentation.

## `task_penetration.csv`

### Source and provenance

- Source: Anthropic Economic Index (project brief; file-level attribution not independently verified)
- Source URL: https://huggingface.co/datasets/Anthropic/EconomicIndex
- Dataset/file version: Unknown / not recorded
- Download date: Unknown / not recorded
- Local file modified time (not a download date): 2026-09-17T17:16:00-07:00
- File: `C:\Users\sumed\dso576\project\task_penetration.csv`

### Shape

- Rows: 17,998
- Columns: 2
- Exact duplicate rows (all columns equal): 6

### Columns

| Column | Inferred type | Example values | Missing values |
|---|---|---|---:|
| `task` | string | Accept and check containers of mail from large volume mailers, couriers, and contractors.; Accept and check containers of mail or parcels from large volume mailers, couriers, and contractors.; Accept credit applications and verify credit references to provide check-cashing authorization or to establish house credit accounts. | 0 |
| `penetration` | numeric | 0.0; 0.9162; 0.926 | 0 |

### Likely identifier checks

- `task`: 17,992 distinct values; 6 repeated occurrences beyond the first; 0 blank values.
  - Repeated examples: `Write interesting and effective press releases, prepare information for media kits, and develop and maintain company internet or intranet Web pages.` (4 rows); `Write interesting and effective press releases, prepare information for media kits, and develop and maintain company internet or intranet web pages.` (4 rows)

### Numeric conversion checks

- `penetration`: 0 failed conversions; numeric range 0 to 1.

### Date conversion checks

No date-like columns found; no date conversions attempted.

### Invalid, impossible, or suspicious values

- `penetration`: 16,644 of 17,998 valid values (92.5%) are zero; review whether this concentration is expected by the source methodology.

### Profiling notes

- Profiling only: no values were changed, normalized, imputed, or removed.
- All CSV fields were read as text first; numeric/date parsing was used only for checks, preserving leading zeros.
- Proportion-range checks assume these named metrics are fractions on a 0..1 scale; confirm against source documentation.
