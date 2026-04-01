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

## Post-Phase 4 hardening entries

### PDD-015
- What: python scripts/quality/run_metric_parity_check.py
- Why: compare key metrics between DuckDB and Snowflake when available, while staying non-breaking locally
- Who: project maintainer
- When: 2026-04-01, top-3 hardening implementation
- Where: repository root
- How:
  - Preconditions: local DuckDB gold model exists
  - Expected output: local-only completion when Snowflake creds are absent, or parity delta report when present
  - Recovery: set missing Snowflake variables or run strict mode in deployment environment

### PDD-016
- What: python scripts/quality/run_metric_parity_check.py --strict-snowflake
- Why: fail fast in deployment pipelines if Snowflake parity cannot be executed or fails tolerance
- Who: project maintainer
- When: introduced in 2026-04-01 hardening implementation
- Where: CI/CD or production shell
- How:
  - Preconditions: Snowflake connector and complete `SNOWFLAKE_*` variables
  - Expected output: parity pass summary or non-zero exit on failure
  - Recovery: fix credentials, connector installation, or metric drift before deployment

## Production readiness and parity enforcement block 3 entries

### PDD-017
- What: python scripts/quality/run_metric_parity_check.py --output-json artifacts/parity/metric_parity_report.json
- Why: produce a reusable JSON artifact for deployment evidence and parity traceability
- Who: project maintainer
- When: 2026-04-01, Block 3 implementation
- Where: repository root
- How:
  - Preconditions: local DuckDB Gold model exists
  - Expected output: parity report JSON with status, tolerance, and metric deltas
  - Recovery: rebuild dbt models and rerun if source relation is missing

### PDD-018
- What: python scripts/quality/run_release_readiness_gate.py
- Why: run ordered production checks in non-strict mode to preserve local developer workflow
- Who: project maintainer
- When: 2026-04-01, Block 3 implementation
- Where: repository root
- How:
  - Preconditions: Python runtime and project dependencies available
  - Expected output: local-safe skip when Snowflake env vars are not set
  - Recovery: provide required environment variables to execute full checks

### PDD-019
- What: python scripts/quality/run_release_readiness_gate.py --strict
- Why: enforce build/test/parity sequence for controlled production release pipelines
- Who: project maintainer
- When: 2026-04-01, Block 3 implementation
- Where: CI/CD or production shell
- How:
  - Preconditions: complete Snowflake credentials and connector availability
  - Expected output: non-zero failure on missing credentials or failing prod checks
  - Recovery: remediate credentials/configuration or failing dbt/parity stages before release

## Governance automation and stop-gate orchestration block 4 entries

### PDD-020
- What: python scripts/governance/generate_release_evidence_bundle.py --release-id <id>
- Why: auto-generate release evidence bundle artifact for audit and stop-gate documentation
- Who: project maintainer
- When: 2026-04-01, Block 4 implementation
- Where: repository root
- How:
  - Preconditions: repository is a valid git working tree
  - Expected output: markdown evidence bundle written under `artifacts/release-evidence/`
  - Recovery: verify output path permissions and rerun with valid release id

## Phase 5: Analytics and Visualization entries

### PDD-021
- What: python scripts/analytics/setup_metabase.py
- Why: initialize Metabase data sources (DuckDB and Snowflake) for Phase 5 dashboard foundation
- Who: data engineer or analytics lead
- When: 2026-04-02, Batch 5.1 implementation
- Where: repository root (or any directory with network access to Metabase)
- How:
  - Preconditions: Metabase instance deployed and running; METABASE_HOST, METABASE_PORT, METABASE_ADMIN_EMAIL, METABASE_ADMIN_PASSWORD configured in environment
  - Expected output: database sources registered, schema synced, confirmation output with next steps
  - Recovery: 1) verify Metabase is running (`curl $METABASE_HOST:$METABASE_PORT`), 2) check admin credentials, 3) review error output and retry

### PDD-022
- What: python scripts/analytics/setup_metabase.py --host <host> --port <port> --email <email> --password <password>
- Why: run Metabase setup with custom host/port/credentials (useful for cloud deployments)
- Who: data engineer or analytics lead
- When: as needed for non-standard Metabase deployments
- Where: repository root
- How:
  - Preconditions: Metabase instance deployed at specified host:port with admin credentials
  - Expected output: same as standard setup; custom host/port used
  - Recovery: verify network connectivity to custom host; check credential format

### PDD-023
- What: streamlit run scripts/analytics/streamlit_app.py --server.port <port>
- Why: launch Batch 5.2 self-service analytics app with governed query templates and visualization widgets
- Who: data engineer or analytics developer
- When: 2026-04-02, Batch 5.2 implementation
- Where: repository root
- How:
  - Preconditions: Streamlit and Plotly installed; DuckDB warehouse initialized
  - Expected output: local web UI available with template controls, charts, and CSV download
  - Recovery: run `make setup`; verify `DUCKDB_PATH` and Phase 4 Gold models exist

### PDD-024
- What: streamlit run scripts/analytics/streamlit_app.py --server.port <port>
- Why: launch Batch 5.3 AI-assisted analytics app with governed intent routing and audit logging
- Who: data engineer or analytics developer
- When: 2026-04-02, Batch 5.3 implementation
- Where: repository root
- How:
  - Preconditions: Batch 5.2 dependencies installed; `OPENAI_API_KEY` optional for LLM mode
  - Expected output: Streamlit app starts with AI Query Assistant, deterministic fallback routing, and JSONL audit logging
  - Recovery: if OpenAI SDK or credentials are unavailable, app should continue in heuristic mode; verify `LLM_AUDIT_LOG_PATH` permissions

### PDD-025
- What: python scripts/analytics/anomaly_monitor.py --source duckdb --output-json <path> --output-markdown <path>
- Why: generate Batch 5.4 anomaly report and stakeholder-ready monitoring summary
- Who: data engineer or analytics developer
- When: 2026-04-02, Batch 5.4 implementation
- Where: repository root
- How:
  - Preconditions: DuckDB warehouse initialized; monitoring environment variables configured; output directories writable
  - Expected output: JSON anomaly report and Markdown summary written to artifact paths; exit code 2 if severe anomalies are detected
  - Recovery: check monitoring thresholds and source data cadence; rerun after restoring access or adjusting configuration
