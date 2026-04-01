# Phase 4 Snowflake Production Alignment

## Objective
Define how this project transitions from local DuckDB development to governed Snowflake production execution without changing model semantics.

## Environment strategy
- Local development target: DuckDB (`dev`).
- Production target: Snowflake (`prod`).
- Same dbt DAG for both targets; only profile and environment variables differ.

## Target configuration
- Profile file: `dbt/profiles/profiles.yml` from `dbt/profiles/profiles.yml.example`.
- Required environment variables:
  - `SNOWFLAKE_ACCOUNT`
  - `SNOWFLAKE_USER`
  - `SNOWFLAKE_PASSWORD`
  - `SNOWFLAKE_ROLE`
  - `SNOWFLAKE_DATABASE`
  - `SNOWFLAKE_WAREHOUSE`
  - `SNOWFLAKE_SCHEMA`
  - `DBT_QUERY_TAG`

## Naming and schema strategy
- Base schema: `analytics`.
- dbt model-level schema suffixes produce:
  - `analytics_silver_staging`
  - `analytics_silver_intermediate`
  - `analytics_gold`
- Snapshot schema remains `silver_history` by project config.

## Role and access model
- Ingestion role: write to bronze and observability areas.
- Transformation role (`TRANSFORMER`): read bronze, write silver/gold/snapshots.
- BI read-only role: read-only access to gold and approved semantic models.
- Principle: least privilege, segregated duties, auditable grants.
- Detailed role-to-object mapping:
  - `docs/reports/phase-4/snowflake-role-access-matrix.md`

## Execution workflow (production)
1. Set environment secrets in CI/CD and runtime.
2. Run `make dbt-build-prod`.
3. Run `make dbt-test-prod`.
4. Run `make metric-parity-check-strict` to compare key metrics with local baseline.
5. Run `make release-readiness-gate-strict` as a single deployment guardrail command.
6. Promote release only when tests and quality checks pass.

## Cost and observability controls
- Use `DBT_QUERY_TAG` for workload traceability.
- Assign dedicated Snowflake warehouse for transformations.
- Enforce auto-suspend and resource monitors.
- Track query history by tag for incident triage and optimization.

## Parity and governance checks
- Compare key metrics (leakage ratio, win rate, cycle days) between dev and prod slices.
- Validate contract tests before and after deployment.
- Record deployment evidence in phase reports and governance logs.
- Use `scripts/quality/run_metric_parity_check.py` for automated parity checks.
- Use `scripts/quality/run_release_readiness_gate.py` to enforce ordered prod checks.
- Apply semantic metric governance workflow:
  - `docs/reports/phase-4/semantic-metric-change-control.md`
