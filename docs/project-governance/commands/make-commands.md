# Make Command Log (5Ws and H)

This file records Make targets used in the project lifecycle.

## Entry format
- What
- Why
- Who
- When
- Where
- How

## Entries

### MK-001
- What: make lint
- Why: execute Ruff and mypy checks for static quality gates
- Who: project maintainer
- When: during every batch validation
- Where: repository root
- How:
  - Preconditions: dev dependencies installed
  - Expected output: Ruff and mypy success summaries
  - Recovery: fix reported errors and rerun

### MK-002
- What: make test
- Why: run unit and smoke tests
- Who: project maintainer
- When: after lint and before quality gate
- Where: repository root
- How:
  - Preconditions: test dependencies installed
  - Expected output: pytest summary with pass/fail counts
  - Recovery: isolate failing tests and correct code

### MK-003
- What: make quality-gate
- Why: execute end-to-end validation including lint, tests, dbt tests, quality checks, and GE validations
- Who: project maintainer
- When: phase completion checkpoints
- Where: repository root
- How:
  - Preconditions: dbt profile configured and source data loaded
  - Expected output: sequential success across all targets
  - Recovery: rerun failed sub-target and remediate root cause before rerunning full gate

### MK-004
- What: make dbt-deps
- Why: install dbt packages required by project models and tests
- Who: project maintainer
- When: setup or package changes
- Where: repository root
- How:
  - Preconditions: dbt installed
  - Expected output: package installation and lock update
  - Recovery: verify package versions and network access

### MK-005
- What: make dbt-build and make dbt-test
- Why: build model graph and validate model/test contracts
- Who: project maintainer
- When: transformation and quality phases
- Where: repository root
- How:
  - Preconditions: dbt profile configured, warehouse and sources available
  - Expected output: successful model materialization and test pass summary
  - Recovery: fix schema, source, or test-contract mismatches

### MK-006
- What: make ingest-crm, make ingest-leads, make export-bronze, make check-freshness
- Why: execute ingestion and bronze processing pipeline
- Who: project maintainer
- When: ingestion and SLA operations
- Where: repository root
- How:
  - Preconditions: source files/API availability and warehouse path readiness
  - Expected output: loaded bronze tables, parquet outputs, freshness report
  - Recovery: fix missing files, schema mismatches, or ingestion script errors

## Phase 4 Batch 4.1 execution entries

### MK-007
- What: make dbt-build
- Why: validate new Gold models (`fct_revenue_funnel`, `dim_sales_teams`) compile and materialize correctly
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.1 validation
- Where: repository root in dev container
- How:
  - Preconditions: dbt profile configured and source data available
  - Expected output: `PASS=77 WARN=0 ERROR=0 SKIP=0 TOTAL=77`
  - Recovery: inspect failing model/test logs and compiled SQL in dbt `target/`

### MK-008
- What: make dbt-test
- Why: execute all dbt data tests including newly added marts contracts
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.1 validation
- Where: repository root in dev container
- How:
  - Preconditions: models built successfully
  - Expected output: `PASS=61 WARN=0 ERROR=0 SKIP=0 TOTAL=61`
  - Recovery: address test contract failures and rerun

### MK-009
- What: make quality-gate
- Why: ensure full project regression safety after Phase 4 additions
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.1 validation
- Where: repository root in dev container
- How:
  - Preconditions: lint/test/dbt profile readiness
  - Expected output: lint, pytest, dbt-test, quality-checks, and GE validation all succeed
  - Recovery: execute failing sub-target independently, remediate, rerun full gate

## Phase 4 Batch 4.2 execution entries

### MK-010
- What: make dbt-build
- Why: validate semantic contract model materialization and marts contract tests in full graph build
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.2 validation
- Where: repository root in dev container
- How:
  - Preconditions: dbt profile configured and bronze/silver source tables available
  - Expected output: `PASS=84 WARN=0 ERROR=0 SKIP=0 TOTAL=84`
  - Recovery: inspect failing dbt nodes and rerun after model/test corrections

### MK-011
- What: make dbt-test
- Why: verify all dbt data contracts including new `dim_metric_contract` tests
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.2 validation
- Where: repository root in dev container
- How:
  - Preconditions: successful `make dbt-build`
  - Expected output: `PASS=67 WARN=0 ERROR=0 SKIP=0 TOTAL=67`
  - Recovery: resolve failing test SQL and rerun

### MK-012
- What: make quality-gate
- Why: confirm no regression in linting, unit tests, dbt tests, and quality scripts
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.2 validation
- Where: repository root in dev container
- How:
  - Preconditions: all dependencies installed and profile configured
  - Expected output: complete successful sequence across all sub-targets
  - Recovery: remediate failed sub-target first, then rerun full gate

## Phase 4 Batch 4.3 execution entries

### MK-013
- What: make dbt-build
- Why: validate BI aggregate model and expanded test graph for dashboard readiness
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.3 validation
- Where: repository root in dev container
- How:
  - Preconditions: marts and tests defined, dbt profile configured
  - Expected output: `PASS=92 WARN=0 ERROR=0 SKIP=0 TOTAL=92`
  - Recovery: inspect failing model/test nodes and rerun

### MK-014
- What: make dbt-test
- Why: execute full dbt data-test suite including BI readiness stability tests
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.3 validation
- Where: repository root in dev container
- How:
  - Preconditions: successful dbt build
  - Expected output: `PASS=74 WARN=0 ERROR=0 SKIP=0 TOTAL=74`
  - Recovery: fix singular/model contract tests and rerun

### MK-015
- What: make quality-gate
- Why: verify complete project stability after BI readiness additions
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.3 validation
- Where: repository root in dev container
- How:
  - Preconditions: lint/test/dbt tooling available
  - Expected output: lint and mypy success, pytest pass, dbt-test pass, quality and GE validations pass
  - Recovery: isolate failed sub-target, remediate, rerun full gate

## Phase 4 Batch 4.4 execution entries

### MK-016
- What: make lint
- Why: validate code-quality baseline after adding production alignment artifacts
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.4 validation
- Where: repository root in dev container
- How:
  - Preconditions: dev dependencies installed
  - Expected output: Ruff and mypy pass
  - Recovery: remediate lint/type issues and rerun

### MK-017
- What: make test
- Why: ensure no Python test regressions from Batch 4.4 changes
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.4 validation
- Where: repository root in dev container
- How:
  - Preconditions: test dependencies available
  - Expected output: pytest pass summary
  - Recovery: fix failing tests and rerun

### MK-018
- What: make quality-gate
- Why: confirm full project quality pipeline after Snowflake alignment and governance additions
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.4 validation
- Where: repository root in dev container
- How:
  - Preconditions: dbt profile available for local target
  - Expected output: dbt-test pass (`PASS=74`), quality checks pass, GE pass
  - Recovery: fix failed sub-stage and rerun full gate

### MK-019
- What: make dbt-build-prod, make dbt-test-prod, make dbt-deploy-prod
- Why: provide explicit production deployment entrypoints for Snowflake target
- Who: project maintainer
- When: 2026-04-01, Batch 4.4 implementation
- Where: repository root
- How:
  - Preconditions: `SNOWFLAKE_*` credentials, warehouse access, and role grants
  - Expected output: prod-target dbt build/test success in Snowflake environment
  - Recovery: verify secrets, permissions, and profile target settings
