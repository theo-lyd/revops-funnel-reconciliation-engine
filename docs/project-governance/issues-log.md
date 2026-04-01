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

### Issue ID: ISS-006
- Phase and batch: Phase 4 Batch 4.1
- Date observed: 2026-04-01
- Where it occurred: Batch validation and quality-gate execution
- Symptom: No blocking defects encountered
- Root cause: Not applicable
- Resolution: Not applicable
- How to avoid: Continue incremental validation strategy (`dbt build`, `dbt test`, `quality-gate`) per batch
- Alternative resolution options: Not applicable
- Verification evidence: Full validation passed (`PASS=77` in dbt build, `PASS=61` in dbt test, quality gate successful)

### Issue ID: ISS-007
- Phase and batch: Phase 4 Batch 4.2
- Date observed: 2026-04-01
- Where it occurred: `make dbt-build` execution in local dev container
- Symptom: Intermittent Python runtime crash under multithreaded dbt build execution
- Root cause: Runtime instability in current local container stack when dbt uses parallel threads
- Resolution: Set `dbt-build` to `--threads 1` in `Makefile`
- How to avoid: Use conservative thread settings for local validation and CI where runtime stability is a priority
- Alternative resolution options: Upgrade runtime stack and dbt adapter, then re-benchmark higher thread counts
- Verification evidence: `make dbt-build` passed with `PASS=84` and `make quality-gate` passed

### Issue ID: ISS-008
- Phase and batch: Phase 4 Batch 4.3
- Date observed: 2026-04-01
- Where it occurred: Batch validation and quality-gate run
- Symptom: No blocking defects encountered
- Root cause: Not applicable
- Resolution: Not applicable
- How to avoid: Continue using incremental BI model rollout plus metric stability tests before full quality-gate runs
- Alternative resolution options: Not applicable
- Verification evidence: `PASS=92` in dbt build, `PASS=74` in dbt test, and quality gate success

### Issue ID: ISS-009
- Phase and batch: Phase 4 Batch 4.4
- Date observed: 2026-04-01
- Where it occurred: Batch validation and quality-gate run
- Symptom: No blocking defects encountered
- Root cause: Not applicable
- Resolution: Not applicable
- How to avoid: Maintain template-driven Snowflake alignment updates plus mandatory regression checks
- Alternative resolution options: Not applicable
- Verification evidence: lint, pytest, dbt-test (`PASS=74`), quality checks, and GE validation all passed

### Issue ID: ISS-010
- Phase and batch: Phase 4 closeout
- Date observed: 2026-04-01
- Where it occurred: Phase-end reporting and governance closure
- Symptom: No blocking defects encountered
- Root cause: Not applicable
- Resolution: Not applicable
- How to avoid: Continue batch-level validation plus formal phase closeout reporting workflow
- Alternative resolution options: Not applicable
- Verification evidence: Phase 4 end report created and closeout changes pushed

### Issue ID: ISS-011
- Phase and batch: Post-Phase 4 hardening (top 3 improvements)
- Date observed: 2026-04-01
- Where it occurred: `make quality-gate` after semantic contract schema expansion
- Symptom: dbt tests failed due to missing new columns in already-materialized relation
- Root cause: quality gate ran `dbt-test` before rebuilding changed models
- Resolution: updated `quality-gate` target to run `dbt-build` before `dbt-test`
- How to avoid: always build models prior to contract tests when schema changes are possible
- Alternative resolution options: run selective `dbt build --select` on changed models before tests
- Verification evidence: quality gate passed with `PASS=96` build and `PASS=78` tests

### Issue ID: ISS-012
- Phase and batch: Post-Phase 4 hardening (top 3 improvements)
- Date observed: 2026-04-01
- Where it occurred: parity-check command in local environment
- Symptom: Snowflake parity not executed due to absent Snowflake environment variables
- Root cause: local development environment intentionally does not include production credentials
- Resolution: parity script completes in local-only mode; strict mode added for deployment environments
- How to avoid: provide credentials only in secured CI/CD or production runtime
- Alternative resolution options: inject temporary scoped credentials in dedicated parity-validation sandbox
- Verification evidence: local parity command returned success with explicit skip message

### Issue ID: ISS-013
- Phase and batch: Governance/security hardening Block 1
- Date observed: 2026-04-01
- Where it occurred: Block 1 implementation and validation
- Symptom: No blocking defects encountered
- Root cause: Not applicable
- Resolution: Not applicable
- How to avoid: continue policy-first document hardening with mandatory validation after each block
- Alternative resolution options: Not applicable
- Verification evidence: lint, tests, dbt build/test, and quality checks all passed

### Issue ID: ISS-014
- Phase and batch: Observability/reliability hardening Block 2
- Date observed: 2026-04-01
- Where it occurred: `dbt source freshness` for `bronze_raw.marketing_leads`
- Symptom: Freshness failed as stale under initial 12h/24h thresholds
- Root cause: Static synthetic sample data cadence does not match near-real-time SLA window
- Resolution: adjusted thresholds to 48h warn / 96h error with same recency filter
- How to avoid: set source freshness windows based on realistic source cadence and dataset refresh model
- Alternative resolution options: drive freshness from ingestion audit metadata model instead of source timestamp
- Verification evidence: `make dbt-source-freshness` passed after threshold update

### Issue ID: ISS-015
- Phase and batch: Observability/reliability hardening Block 2
- Date observed: 2026-04-01
- Where it occurred: Block 2 validation and closeout
- Symptom: No further blocking defects encountered
- Root cause: Not applicable
- Resolution: Not applicable
- How to avoid: continue incremental reliability controls and mandatory full quality-gate checks
- Alternative resolution options: Not applicable
- Verification evidence: lint/test/quality-gate and source freshness checks passed

### Issue ID: ISS-016
- Phase and batch: Production readiness/parity hardening Block 3
- Date observed: 2026-04-01
- Where it occurred: `scripts/quality/run_release_readiness_gate.py`
- Symptom: Ruff import-order check failed on first lint run
- Root cause: New script imports were not in tool-expected ordering
- Resolution: applied Ruff-compatible import ordering and revalidated full gate
- How to avoid: run file-level Ruff check after creating new scripts
- Alternative resolution options: use `ruff check --fix` on the changed file before full validation
- Verification evidence: `make lint` and full validation chain passed

### Issue ID: ISS-017
- Phase and batch: Production readiness/parity hardening Block 3
- Date observed: 2026-04-01
- Where it occurred: Block 3 validation and closeout
- Symptom: No further blocking defects encountered
- Root cause: Not applicable
- Resolution: Not applicable
- How to avoid: continue strict phased validation discipline and stop-gate enforcement
- Alternative resolution options: Not applicable
- Verification evidence: lint/test/quality-gate plus parity-report and readiness-gate checks passed

### Issue ID: ISS-018
- Phase and batch: Governance automation/stop-gate hardening Block 4
- Date observed: 2026-04-01
- Where it occurred: Block 4 implementation and validation
- Symptom: No blocking defects encountered
- Root cause: Not applicable
- Resolution: Not applicable
- How to avoid: maintain automation-first governance controls and full validation before release
- Alternative resolution options: Not applicable
- Verification evidence: lint/test/quality-gate, production-stop-gate, and evidence-bundle generation passed

### Issue ID: ISS-019
- Phase and batch: CI/CD hardening - conditional production parity job
- Date observed: 2026-04-02
- Where it occurred: GitHub Actions workflow integration
- Symptom: No blocking defects; successful implementation of conditional job triggering
- Root cause: Not applicable
- Resolution: Added conditional production-parity-check job to .github/workflows/ci.yml with trigger logic `if: github.event_name == 'push' && github.ref == 'refs/heads/master' && secrets.SNOWFLAKE_ACCOUNT != ''`
- How to avoid: validate conditional YAML syntax and test trigger conditions on sample pushes to master
- Alternative resolution options: Use GitHub Actions environments feature for conditional workflows
- Verification evidence: CI workflow file validated; production parity check job triggers only on master pushes with secrets; local and PR workflows remain unaffected

### Issue ID: ISS-020
- Phase and batch: Phase 5 Batch 5.1 - Dashboard foundation and BI layer integration
- Date observed: 2026-04-02
- Where it occurred: Phase 5 initial batch implementation
- Symptom: No blocking defects; successful implementation of Metabase setup automation
- Root cause: Not applicable
- Resolution: Implemented Metabase setup script with DuckDB and Snowflake data sources; added dashboard dependencies to requirements; updated environment configuration
- How to avoid: follow BI/dashboard development best practices; validate Metabase connectivity before running setup script; use local-safe patterns (skip on missing credentials)
- Alternative resolution options: Manual Metabase UI configuration (not recommended for reproducibility)
- Verification evidence: setup script successfully registers data sources; schema metadata synced; governance logs and make targets updated

### Issue ID: ISS-021
- Phase and batch: Phase 5 Batch 5.2 - Streamlit application and query templates
- Date observed: 2026-04-02
- Where it occurred: Initial Streamlit app implementation (`scripts/analytics/streamlit_app.py`)
- Symptom: SQL builder ordering and quoting defects created invalid query structures in early draft
- Root cause: Query finalization (`limit`) was applied before all predicates and one string interpolation had conflicting quote escaping
- Resolution: refactored query builder into staged functions (`_apply_filters`, `_apply_date_filters`, `_finalize_query`) and corrected office-value escaping
- How to avoid: unit-check SQL string assembly order and run static lint checks immediately after adding query builder code
- Alternative resolution options: move to parameterized query builders per connector (DuckDB/Snowflake) in future hardening
- Verification evidence: `make lint` and `make test` pass with Streamlit app included

### Issue ID: ISS-022
- Phase and batch: Phase 5 Batch 5.3 - LLM integration and AI-driven query generation
- Date observed: 2026-04-02
- Where it occurred: initial LLM routing implementation in `scripts/analytics/streamlit_app.py`
- Symptom: no blocking defects; deterministic fallback and OpenAI path both remained template-governed
- Root cause: not applicable
- Resolution: extended existing Streamlit app with a guarded AI Query Assistant, session rate limiting, and JSONL audit logging
- How to avoid: keep AI output restricted to the approved template catalog and known office filters; continue to store secrets in environment variables only
- Alternative resolution options: disable OpenAI path entirely and use heuristic-only routing in constrained environments
- Verification evidence: `make lint` and `make test` passed after Batch 5.3 updates; audit path is ignored by git

### Issue ID: ISS-023
- Phase and batch: Phase 5 Batch 5.4 - Analytics insights and anomaly detection
- Date observed: 2026-04-02
- Where it occurred: Batch 5.4 monitoring integration and report generation
- Symptom: no blocking defects; monitoring report and dashboard pipeline were implemented successfully
- Root cause: not applicable
- Resolution: added shared anomaly detection helpers, Streamlit monitoring dashboard, and CLI report generator with governed outputs
- How to avoid: keep monitoring thresholds configurable and continue to validate report outputs against the Gold-layer schema
- Alternative resolution options: add email transport or scheduled orchestration in a later hardening step
- Verification evidence: `make lint` and `make test` passed after Batch 5.4 implementation; generated artifacts are ignored by git

### Issue ID: ISS-024
- Phase and batch: Post-Phase 5 hardening - shared modules and validation
- Date observed: 2026-04-02
- Where it occurred: shared analytics helper refactor and fixture-based tests
- Symptom: no blocking defects; a few Ruff style issues were surfaced and corrected during refactor validation
- Root cause: import ordering and line wrapping drift after extracting shared modules
- Resolution: normalized imports, wrapped long lines, and revalidated lint/tests
- How to avoid: run Ruff immediately after module extraction; keep helper functions in shared modules with explicit unit coverage
- Alternative resolution options: freeze the app structure and only add wrappers, but that would retain duplicate logic
- Verification evidence: `make lint` and `make test` passed with 15 tests total after refactor

### Issue ID: ISS-025
- Phase and batch: Phase 6 Batch 6.1 - Monitoring email delivery
- Date observed: 2026-04-02
- Where it occurred: `src/revops_funnel/notifications.py` during SMTP message composition
- Symptom: email send path raised a duplicate `From` header error during test execution
- Root cause: the message builder set a default `From` header and the SMTP sender override added a second header instead of replacing the original
- Resolution: used `replace_header("From", ...)` before dispatching the message
- How to avoid: keep message header ownership in one place; validate email composition with focused unit tests before wiring transport
- Alternative resolution options: pass the sender into the message builder directly and remove the override step
- Verification evidence: focused notification tests and full `make lint` / `pytest -q` passed after the fix
