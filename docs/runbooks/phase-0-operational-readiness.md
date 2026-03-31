# Phase 0 Operational Readiness Runbook

## Objective
Ensure every developer and CI run starts from a known-good environment with security and configuration checks.

## Steps
1. Install dependencies and hooks: `make setup`
2. Verify environment values: `make preflight`
3. Initialize local warehouse schemas: `make init-warehouse`
4. Install dbt packages: `make dbt-deps`
5. Run quality checks: `make lint && make test`

## Failure handling
- If `preflight` fails: set missing environment variables.
- If schema bootstrap fails: verify file permissions under `data/warehouse`.
- If dbt dependency install fails: verify outbound network access.
