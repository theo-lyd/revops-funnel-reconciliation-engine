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

## Phase 6 Batch 6.1 execution entries

### MK-041
- What: make lint
- Why: validate the Phase 6 email delivery batch after adding the new notification module and CLI wiring
- Who: project maintainer
- When: 2026-04-02, Phase 6 Batch 6.1 validation
- Where: repository root in dev container
- How:
  - Preconditions: dev dependencies installed and new files added
  - Expected output: Ruff and mypy success summaries
  - Recovery: fix import ordering or type issues and rerun

### MK-042
- What: make test
- Why: confirm the full project test suite still passes after the email notification changes
- Who: project maintainer
- When: 2026-04-02, Phase 6 Batch 6.1 validation
- Where: repository root in dev container
- How:
  - Preconditions: project tests available
  - Expected output: pytest pass summary with all tests green
  - Recovery: isolate failing tests, fix root cause, and rerun

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

## Post-Phase 4 hardening entries

### MK-020
- What: make lint && make test && make quality-gate && make metric-parity-check
- Why: validate top-3 hardening improvements (thread controls, semantic contract versioning, parity scaffold)
- Who: project maintainer
- When: 2026-04-01, post-Phase 4 hardening batch
- Where: repository root in dev container
- How:
  - Preconditions: dbt artifacts and local warehouse initialized
  - Expected output: lint/test/quality-gate pass, parity command completes in local-only mode when Snowflake vars are absent
  - Recovery: address failing lint/tests, rerun dbt build before dbt test, then rerun full command chain

### MK-021
- What: make metric-parity-check-strict
- Why: enforce DuckDB↔Snowflake parity in deployment pipelines where Snowflake credentials are present
- Who: project maintainer
- When: introduced in 2026-04-01 hardening batch
- Where: CI/CD or production-ready shell with Snowflake credentials
- How:
  - Preconditions: `SNOWFLAKE_*` env vars and Snowflake connector installed
  - Expected output: parity check pass or non-zero exit on drift
  - Recovery: investigate source-model parity, data lag, and environment configuration mismatches

## Governance and security hardening block 1 entries

### MK-022
- What: make lint && make test && make quality-gate
- Why: validate Block 1 governance/security documentation and policy-linking changes without runtime regressions
- Who: project maintainer
- When: 2026-04-01, Block 1 implementation
- Where: repository root in dev container
- How:
  - Preconditions: standard local development dependencies installed
  - Expected output: lint/test pass, dbt build/test pass, quality scripts pass
  - Recovery: fix any failing stage and rerun full sequence

## Observability and reliability hardening block 2 entries

### MK-023
- What: make lint && make test && make quality-gate && make dbt-source-freshness
- Why: validate Block 2 additions (freshness specs, query-pack runner, release evidence template integration)
- Who: project maintainer
- When: 2026-04-01, Block 2 implementation
- Where: repository root in dev container
- How:
  - Preconditions: dbt profile configured and source data available
  - Expected output: quality-gate pass and freshness pass
  - Recovery: adjust freshness thresholds/filters for static dataset behavior, then rerun

### MK-024
- What: make query-pack-validate
- Why: execute BI query packs as testable reliability artifacts
- Who: project maintainer
- When: 2026-04-01, integrated into quality-gate in Block 2
- Where: repository root in dev container
- How:
  - Preconditions: Gold models materialized and query-pack files present
  - Expected output: per-statement validation messages and final success confirmation
  - Recovery: fix invalid SQL templates or missing model references

### MK-025
- What: make dbt-source-freshness
- Why: enforce dbt-native freshness observability for source recency
- Who: project maintainer
- When: 2026-04-01, Block 2 implementation
- Where: repository root in dev container
- How:
  - Preconditions: source has `loaded_at_field` and freshness config
  - Expected output: PASS for configured source freshness checks
  - Recovery: adjust recency windows for realistic source cadence and rerun

## Production readiness and parity enforcement block 3 entries

### MK-026
- What: make lint && make test && make quality-gate
- Why: validate Block 3 automation changes without regressing baseline quality controls
- Who: project maintainer
- When: 2026-04-01, Block 3 implementation
- Where: repository root in dev container
- How:
  - Preconditions: standard local development dependencies installed
  - Expected output: lint/test pass, dbt build/test pass, query-pack and quality checks pass
  - Recovery: fix failing stage and rerun full sequence

### MK-027
- What: make metric-parity-check-report
- Why: generate machine-readable parity artifact for release evidence bundles
- Who: project maintainer
- When: 2026-04-01, Block 3 implementation
- Where: repository root in dev container
- How:
  - Preconditions: local Gold model is materialized
  - Expected output: `artifacts/parity/metric_parity_report.json` written
  - Recovery: run `make dbt-build` if relation missing; validate output path permissions

### MK-028
- What: make release-readiness-gate
- Why: execute ordered production-readiness checks in local-safe mode
- Who: project maintainer
- When: 2026-04-01, Block 3 implementation
- Where: repository root in dev container
- How:
  - Preconditions: script dependencies available
  - Expected output: local-safe skip message when Snowflake env vars are absent
  - Recovery: set required `SNOWFLAKE_*` env vars and run strict target for production pipelines

## Governance automation and stop-gate orchestration block 4 entries

### MK-029
- What: make production-stop-gate
- Why: run final local-safe stop-gate sequence as one command
- Who: project maintainer
- When: 2026-04-01, Block 4 implementation
- Where: repository root in dev container
- How:
  - Preconditions: local dbt profile and source data available
  - Expected output: quality-gate success, parity-report artifact generation, release-readiness gate local-safe completion
  - Recovery: remediate failing subcommand and rerun full stop-gate

### MK-030
- What: RELEASE_ID=<id> make release-evidence-bundle
- Why: generate auditable release evidence markdown artifact from template-backed automation
- Who: project maintainer
- When: 2026-04-01, Block 4 implementation
- Where: repository root in dev container
- How:
  - Preconditions: `RELEASE_ID` provided
  - Expected output: artifact written to `artifacts/release-evidence/release-evidence-bundle.md`
  - Recovery: set required environment variable and rerun

### MK-031
- What: RELEASE_ID=<id> make production-stop-gate-strict
- Why: enforce strict pre-release checks in secured production contexts
- Who: project maintainer
- When: introduced in Block 4 implementation
- Where: CI/CD or production shell
- How:
  - Preconditions: complete Snowflake credentials and `RELEASE_ID`
  - Expected output: strict parity and readiness checks pass, evidence bundle generated
  - Recovery: resolve credentials/parity/build failures and rerun

## CI/CD hardening and conditional parity job entries

### MK-032
- What: GitHub Actions conditional production-parity-check job in .github/workflows/ci.yml
- Why: enforce strict production parity only on master pushes with Snowflake secrets present; preserve local and PR workflows
- Who: project engineering
- When: 2026-04-02, final CI/CD hardening step
- Where: .github/workflows/ci.yml (new job added to existing quality job)
- How:
  - Preconditions: Snowflake secrets configured in repository settings (SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA, SNOWFLAKE_WAREHOUSE, SNOWFLAKE_ROLE)
  - Trigger condition: `if: github.event_name == 'push' && github.ref == 'refs/heads/master' && secrets.SNOWFLAKE_ACCOUNT != ''`
  - Expected output: job skipped on PR or local branch pushes; on master push with secrets, job runs full parity check with PARITY_TOLERANCE_STRICT=0.0 and passes/fails workflow accordingly
  - Recovery: investigate parity delta; resolve discrepancies between DuckDB and Snowflake Gold layers; retry push when parity passes

## Phase 5: Analytics and Visualization targets

### MK-033
- What: make metabase-setup
- Why: initialize Metabase with DuckDB and Snowflake data sources for Phase 5 dashboard foundation
- Who: data engineer or analytics lead
- When: 2026-04-02, Batch 5.1 implementation
- Where: repository root in dev container or Metabase deployment environment
- How:
  - Preconditions: Metabase deployed and running at METABASE_HOST:METABASE_PORT; admin credentials configured in .env
  - Expected output: DuckDB and Snowflake data sources registered; database schema synced; confirmation message
  - Recovery: verify Metabase is running; check credentials; review error output and retry

### MK-034
- What: make streamlit-dev
- Why: start Streamlit development server for Phase 5 analytics interface
- Who: data engineer or analytics developer
- When: 2026-04-02, prepared for Batch 5.2
- Where: repository root in dev container
- How:
  - Preconditions: Streamlit installed; `scripts/analytics/streamlit_app.py` exists
  - Expected output: Streamlit server starts on port STREAMLIT_SERVER_PORT (default: 8501)
  - Recovery: verify Streamlit installation; check port availability; run `make setup` to reinstall dependencies

### MK-035
- What: make streamlit-dev
- Why: run Batch 5.2 interactive analytics app with governed query templates over Gold-layer models
- Who: data engineer or analytics developer
- When: 2026-04-02, Batch 5.2 implementation
- Where: repository root in dev container
- How:
  - Preconditions: `scripts/analytics/streamlit_app.py` exists and dependencies are installed
  - Expected output: Streamlit app launches and exposes template-based analytics UI on configured port
  - Recovery: install/update dependencies with `make setup`; check app logs for connector/env issues

### MK-036
- What: make streamlit-dev
- Why: run Batch 5.3 Streamlit app with AI query assistance, template routing, and audit logging
- Who: data engineer or analytics developer
- When: 2026-04-02, Batch 5.3 implementation
- Where: repository root in dev container
- How:
  - Preconditions: `OPENAI_API_KEY` is optional; `scripts/analytics/streamlit_app.py` and dependencies are installed
  - Expected output: Streamlit app launches with the AI Query Assistant sidebar, governed template routing, and audit logging to JSONL
  - Recovery: verify `.env` values for `OPENAI_MODEL`, `LLM_MAX_TOKENS`, and `LLM_AUDIT_LOG_PATH`; if OpenAI is unavailable, app falls back to deterministic routing

### MK-037
- What: make anomaly-check
- Why: run Batch 5.4 anomaly detection over the executive funnel overview and generate a JSON monitoring report
- Who: data engineer or analytics developer
- When: 2026-04-02, Batch 5.4 implementation
- Where: repository root in dev container
- How:
  - Preconditions: DuckDB warehouse is initialized and monitoring config variables are set
  - Expected output: JSON report written to `ANOMALY_REPORT_PATH` and Markdown summary written to `ANOMALY_MARKDOWN_PATH`
  - Recovery: verify `DUCKDB_PATH`, monitoring env vars, and artifact write permissions; rerun if data source is unavailable

### MK-038
- What: make insights-generate
- Why: generate Batch 5.4 monitoring insights and alert-ready summaries for stakeholders
- Who: data engineer or analytics developer
- When: 2026-04-02, Batch 5.4 implementation
- Where: repository root in dev container
- How:
  - Preconditions: same as `make anomaly-check`; markdown output path is writable
  - Expected output: monitoring JSON and Markdown artifacts refreshed with latest anomaly summary
  - Recovery: review anomaly severity thresholds and output permissions; rerun after fixing environment issues

### MK-039
- What: make lint
- Why: validate the shared-module hardening refactor and its associated test updates
- Who: project maintainer
- When: 2026-04-02, post-Phase 5 hardening batch
- Where: repository root
- How:
  - Preconditions: code changes staged or present in working tree
  - Expected output: Ruff and mypy success summaries
  - Recovery: fix reported style or typing errors and rerun

### MK-040
- What: make test
- Why: execute fixture-based analytics query and monitoring tests for the shared-module hardening batch
- Who: project maintainer
- When: 2026-04-02, post-Phase 5 hardening batch
- Where: repository root
- How:
  - Preconditions: test dependencies installed
  - Expected output: pytest success summary with analytics tests passing
  - Recovery: inspect failing assertions or fixture data and rerun

## Phase 6 Batch 6.2 execution entries

### MK-041
- What: make lint
- Why: validate the expanded Phase 6 operations automation batch across CI, DAG, and deployment helper updates
- Who: project maintainer
- When: 2026-04-02, Phase 6 Batch 6.2 validation
- Where: repository root
- How:
  - Preconditions: dependencies installed and Phase 6.2 files present
  - Expected output: Ruff and mypy success across repo modules
  - Recovery: fix style/type defects and rerun until clean

### MK-042
- What: make test
- Why: execute full regression tests after adding deployment helper module and operations scripts
- Who: project maintainer
- When: 2026-04-02, Phase 6 Batch 6.2 validation
- Where: repository root
- How:
  - Preconditions: pytest dependencies available
  - Expected output: all tests pass including new deployment helper tests
  - Recovery: isolate failing tests, remediate code path, rerun full suite

## Phase 6 Batch 6.3 execution entries

### MK-043
- What: make lint
- Why: validate release-gate integrity changes across workflow automation and promotion contract updates
- Who: project maintainer
- When: 2026-04-02, Phase 6 Batch 6.3 validation
- Where: repository root
- How:
  - Preconditions: dependencies installed and Phase 6.3 files updated
  - Expected output: Ruff and mypy success across 29 source files
  - Recovery: resolve style/type issues and rerun until clean

### MK-044
- What: make test
- Why: confirm no regressions after promotion metadata and checksum contract expansion
- Who: project maintainer
- When: 2026-04-02, Phase 6 Batch 6.3 validation
- Where: repository root
- How:
  - Preconditions: pytest dependencies available
  - Expected output: full test suite passes including deployment contract tests
  - Recovery: isolate failing tests and remediate before release

## Phase 6 Batch 6.4 execution entries

### MK-045
- What: make lint
- Why: validate CI workflow slimming and selector determinism codepaths after implementation
- Who: project maintainer
- When: 2026-04-02, Phase 6 Batch 6.4 validation
- Where: repository root
- How:
  - Preconditions: dependencies installed and Phase 6.4 files updated
  - Expected output: Ruff and mypy success across repo modules
  - Recovery: fix style/type issues and rerun gates

### MK-046
- What: make test
- Why: verify selector determinism and CI helper tests while preserving prior phase behavior
- Who: project maintainer
- When: 2026-04-02, Phase 6 Batch 6.4 validation
- Where: repository root
- How:
  - Preconditions: pytest dependencies installed
  - Expected output: full suite passes including new selector tests
  - Recovery: isolate and remediate failing test paths before release

## Phase 6 Batch 6.5 execution entries

### MK-047
- What: make lint
- Why: validate DAG reliability hardening changes for style/type safety across code and Airflow modules
- Who: project maintainer
- When: 2026-04-02, Phase 6 Batch 6.5 validation
- Where: repository root
- How:
  - Preconditions: dependencies installed and DAG/report updates applied
  - Expected output: Ruff and mypy pass across source, scripts, and dags
  - Recovery: resolve lint/type findings and rerun

### MK-048
- What: make test
- Why: validate regression safety after deterministic Airflow path and DAG test coverage updates
- Who: project maintainer
- When: 2026-04-02, Phase 6 Batch 6.5 validation
- Where: repository root
- How:
  - Preconditions: pytest dependencies installed
  - Expected output: full test suite pass, with DAG test running when Airflow is available and skipping otherwise
  - Recovery: remediate failing tests; if skip occurs due missing Airflow, confirm environment constraints and continue with local-safe behavior
