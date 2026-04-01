# Project Issues Log

This log tracks implementation issues across all phases.

## Entry template
- Issue ID:
- Phase and batch:
- Date observed:
- Where it occurred:
- Symptom:
- Root cause:
- Resolution:
- How to avoid:
- Alternative resolution options:
- Verification evidence:

## Recorded issues

### Issue ID: ISS-001
- Phase and batch: Phase 3 hardening and quality-gate stabilization
- Date observed: 2026-04-01
- Where it occurred: Pre-commit execution during commit workflow
- Symptom: Hook id ruff-check was rejected by pre-commit
- Root cause: Invalid hook id for current version of ruff-pre-commit
- Resolution: Updated .pre-commit-config.yaml hook id from ruff-check to ruff
- How to avoid: Validate hook IDs against upstream repository before pinning
- Alternative resolution options: Run pre-commit autoupdate and re-pin compatible versions
- Verification evidence: pre-commit run --all-files completed successfully

### Issue ID: ISS-002
- Phase and batch: Phase 3 quality-gate execution
- Date observed: 2026-04-01
- Where it occurred: dbt test execution in quality gate
- Symptom: Intermittent Python runtime crash during multithreaded dbt tests
- Root cause: Runtime instability under current local environment and threading mode
- Resolution: Run dbt test with single thread in Makefile
- How to avoid: Use conservative thread settings in constrained development containers
- Alternative resolution options: Upgrade runtime stack and retest with higher thread count
- Verification evidence: make quality-gate returned success

### Issue ID: ISS-003
- Phase and batch: Phase 3 quality script validation
- Date observed: 2026-04-01
- Where it occurred: scripts/quality/run_data_quality_checks.py and scripts/quality/run_great_expectations.py
- Symptom: Table not found errors for silver_intermediate schema references
- Root cause: dbt schema materialization uses analytics_silver_intermediate naming
- Resolution: Updated script queries to analytics_silver_intermediate
- How to avoid: Use a shared schema constant or dbt metadata mapping for downstream scripts
- Alternative resolution options: Configure dbt schemas to match script expectations
- Verification evidence: quality checks and GE validation passed

### Issue ID: ISS-004
- Phase and batch: Phase 3 local setup for dbt profile
- Date observed: 2026-04-01
- Where it occurred: dbt profile path configuration
- Symptom: DuckDB database file not found
- Root cause: Incorrect relative path in dbt profile example and local profile
- Resolution: Corrected path to ../data/warehouse/revops.duckdb
- How to avoid: Validate profile paths from the dbt working directory
- Alternative resolution options: Use absolute environment-based path values
- Verification evidence: dbt build and dbt test passed

### Issue ID: ISS-005
- Phase and batch: Git push workflow in local container
- Date observed: 2026-04-01
- Where it occurred: Local Git hooks
- Symptom: Push and post-commit warnings due to missing git-lfs binary
- Root cause: Local hooks expected git-lfs while repository had no active LFS tracking config
- Resolution: Removed local git-lfs hook scripts from .git/hooks in this environment
- How to avoid: Install git-lfs when repository policy requires it, or avoid local hook drift
- Alternative resolution options: Install git-lfs package and keep hooks active
- Verification evidence: Push to origin completed successfully
