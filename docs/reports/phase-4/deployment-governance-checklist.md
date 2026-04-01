# Deployment Governance Checklist (Snowflake Production)

Use this checklist before every production deployment.

## A) Access and secret readiness
- `SNOWFLAKE_*` secrets are configured in CI and runtime.
- Credentials are not committed to repository files.
- Role and warehouse assignments are approved.

## B) Code and quality readiness
- Branch changes are reviewed and merged.
- `make lint` passes.
- `make test` passes.
- `make quality-gate` passes in development target.

## C) Production dry run and release
- `make dbt-build-prod` passes.
- `make dbt-test-prod` passes.
- `make metric-parity-check-strict` passes.
- Query tags are set via `DBT_QUERY_TAG`.

## D) Post-deploy verification
- Gold models are queryable (`analytics_gold`).
- Metric stability checks are green.
- Dashboards and BI query packs return expected outputs.
- Incident and rollback contacts are on-call.

## E) Audit evidence to store
- Commit hash and release timestamp.
- Command logs and outputs summary.
- Any deviations and approvals.
- Post-deploy metric parity validation summary.
