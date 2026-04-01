# Python, dbt, and DuckDB Command Log (5Ws and H)

This file records Python, dbt, and DuckDB-specific commands.

## Entry format
- What
- Why
- Who
- When
- Where
- How

## Entries

### PDD-001
- What: python scripts/init_warehouse.py
- Why: create local DuckDB schemas and baseline objects
- Who: project maintainer
- When: setup and environment reset
- Where: repository root
- How:
  - Preconditions: project package importable and path writable
  - Expected output: confirmation of DuckDB initialization path
  - Recovery: verify module import path and filesystem permissions

### PDD-002
- What: python scripts/ingest/load_crm_csv_to_duckdb.py
- Why: load CRM source CSV files into bronze_raw schema
- Who: project maintainer
- When: ingestion runs and test-data refresh
- Where: repository root
- How:
  - Preconditions: data/raw/crm files present
  - Expected output: per-table load confirmation and ingestion audit entries
  - Recovery: validate CSV paths and schema expectations

### PDD-003
- What: python scripts/ingest/load_leads_jsonl_to_duckdb.py
- Why: load synthetic marketing leads into bronze_raw.marketing_leads
- Who: project maintainer
- When: ingestion runs and quality-gate prep
- Where: repository root
- How:
  - Preconditions: data/raw/marketing/leads_raw.jsonl exists
  - Expected output: count of newly loaded lead records
  - Recovery: generate or fetch JSONL source file and rerun

### PDD-004
- What: cd dbt && dbt deps
- Why: install dbt package dependencies such as dbt_utils
- Who: project maintainer
- When: setup and package updates
- Where: dbt project directory
- How:
  - Preconditions: dbt profile and internet access
  - Expected output: package installation summary
  - Recovery: pin versions and retry

### PDD-005
- What: cd dbt && dbt build --profiles-dir profiles
- Why: build full model graph with tests and snapshots
- Who: project maintainer
- When: transformation validation and release readiness
- Where: dbt project directory
- How:
  - Preconditions: valid profile and available source tables
  - Expected output: model/test/snapshot execution summary
  - Recovery: resolve source availability and test contract errors

### PDD-006
- What: cd dbt && dbt test --profiles-dir profiles --threads 1
- Why: execute dbt data tests with stable single-thread behavior in this environment
- Who: project maintainer
- When: quality-gate execution
- Where: dbt project directory
- How:
  - Preconditions: models built and profile configured
  - Expected output: pass/fail totals for data tests
  - Recovery: inspect compiled failing SQL in dbt target output

### PDD-007
- What: python scripts/quality/run_data_quality_checks.py
- Why: execute deterministic quality assertions and write quality audit entries
- Who: project maintainer
- When: Phase 3+ quality checkpoints
- Where: repository root
- How:
  - Preconditions: intermediate model tables exist in target schema
  - Expected output: check-by-check pass/fail with failed row counts
  - Recovery: align schema references and source model state

### PDD-008
- What: python scripts/quality/run_great_expectations.py
- Why: execute additional data quality validations using Great Expectations style checks
- Who: project maintainer
- When: quality-gate execution
- Where: repository root
- How:
  - Preconditions: pandas and great-expectations installed, model tables available
  - Expected output: validation passed summary or listed failures
  - Recovery: fix data contract violations and rerun

## Phase 4 Batch 4.1 execution entries

### PDD-009
- What: cd dbt && dbt build --profiles-dir profiles
- Why: validate newly added Gold marts and tests in full graph execution
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.1 validation
- Where: dbt project directory
- How:
  - Preconditions: profile configured and Bronze/Silver sources present
  - Expected output: successful completion with 77 total tasks and no errors
  - Recovery: check failing nodes in dbt logs and `target/compiled`

### PDD-010
- What: cd dbt && dbt test --profiles-dir profiles --threads 1
- Why: run full data-test suite including marts contracts with stable threading settings
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.1 validation
- Where: dbt project directory
- How:
  - Preconditions: successful dbt build
  - Expected output: 61 tests passed with no errors
  - Recovery: fix failing contracts and rerun test command

## Phase 4 Batch 4.2 execution entries

### PDD-011
- What: cd dbt && dbt build --profiles-dir profiles --threads 1
- Why: validate semantic contract model (`dim_metric_contract`) and expanded marts test graph
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.2 validation
- Where: dbt project directory
- How:
  - Preconditions: dbt dependencies installed and profile configured
  - Expected output: 84 total tasks completed successfully
  - Recovery: inspect dbt logs and compiled SQL under `dbt/target`

### PDD-012
- What: cd dbt && dbt test --profiles-dir profiles --threads 1
- Why: execute semantic contract and funnel data tests with stable single-thread runtime
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.2 validation
- Where: dbt project directory
- How:
  - Preconditions: successful dbt build
  - Expected output: 67 tests passed with no warnings or errors
  - Recovery: resolve failing tests and rerun

## Phase 4 Batch 4.3 execution entries

### PDD-013
- What: cd dbt && dbt build --profiles-dir profiles --threads 1
- Why: validate BI-readiness model `bi_executive_funnel_overview` and new singular stability tests in graph build
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.3 validation
- Where: dbt project directory
- How:
  - Preconditions: marts and tests are added
  - Expected output: 92 tasks completed with no errors
  - Recovery: inspect dbt logs and compiled SQL under `dbt/target`

### PDD-014
- What: cd dbt && dbt test --profiles-dir profiles --threads 1
- Why: run all data tests including win-rate and leakage-ratio stability checks
- Who: project maintainer
- When: 2026-04-01, Phase 4 Batch 4.3 validation
- Where: dbt project directory
- How:
  - Preconditions: successful dbt build
  - Expected output: 74 tests passed with no warnings or errors
  - Recovery: address failing tests and rerun
