# DSO 576 — Jade Yan

## Directory guide

- `project/`: current team application backend, canonical data, specifications, and reports. Start with `project/BUILD_SPEC.md`.
- `my-audit.md`: Jade’s Module 9 individual submission.
- `jade_audit_check.py`: Jade’s Module 9 reproducible checks.
- `change-requests.md`: shared audit claims and requested changes.
- `audit_check.py`: Ella’s audit checks.
- `project-start.md`: team project proposal.
- `archive/module6-jade/`: Jade’s earlier Module 6 script, original inputs, and cleaning outputs.
- `pyproject.toml` and `uv.lock`: shared Python environment configuration.

## Run the Module 9 checks

From this repository root, with pandas and numpy installed:

```sh
python jade_audit_check.py
```

## Earlier Module 6 work

The four original root items were moved together into `archive/module6-jade/` without changing their contents. The script resolves inputs relative to its own location.

```sh
cd archive/module6-jade
python python.py
```

Running that script regenerates its cleaning outputs. Existing historical records are preserved as originally written.
