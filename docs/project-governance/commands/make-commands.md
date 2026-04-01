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
