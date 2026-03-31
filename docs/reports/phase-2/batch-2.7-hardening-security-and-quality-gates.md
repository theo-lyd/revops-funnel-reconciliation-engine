# Batch 2.7 Report: Hardening Security and Quality Gates

## What was done
- Removed hardcoded Airflow credentials and enforced secret-based admin bootstrap variables.
- Added constrained Airflow installation pattern in setup to improve dependency reproducibility.
- Expanded lint/type checks to cover `src`, `scripts`, and `dags`.
- Added CI workflow running lint, mypy, pytest, and dbt parse checks.
- Added unit tests for ingestion helper behavior and freshness helper logic.

## How it was done
- Updated:
  - `Makefile`
  - `requirements/base.txt`
  - `README.md`
  - `scripts/ingest/load_leads_jsonl_to_duckdb.py`
- Added:
  - `.github/workflows/ci.yml`
  - `tests/test_ingest_helpers.py`
  - `tests/test_freshness_helpers.py`

## Why it was done
- Eliminate credential leakage risk in developer automation.
- Improve deterministic environment bootstrap for Airflow-heavy stacks.
- Increase confidence through automated quality gates in CI.
- Expand test coverage beyond basic smoke checks.

## Alternatives considered
- Use Poetry with lockfile for full dependency determinism.
- Use dedicated security scanner workflows (CodeQL/GHAS/Trivy) in addition to pre-commit.
- Use tox/nox orchestration for matrix test execution.

## Command sequence used
```bash
# Updated setup and airflow-init commands for secure, constrained installs
# Added CI workflow and helper-level unit tests
# Expanded static checks across runtime scripts and orchestration code
```
