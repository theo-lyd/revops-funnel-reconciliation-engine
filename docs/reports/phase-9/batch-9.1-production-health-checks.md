# Batch 9.1: Production Health Checks and Liveness Monitoring

## Objective
Add production-grade health checks and liveness monitoring to track data freshness compliance, transformation job duration SLOs, and trigger alerts on health degradation.

## Deliverables
- `src/revops_funnel/health_monitoring.py`
- `scripts/ops/run_health_checks.py`
- `tests/test_health_monitoring.py`
- `tests/test_run_health_checks_cli.py`
- `Makefile`
- `.env.example`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`

## What Changed
1. Added shared health monitoring helpers to evaluate data freshness and job duration against configurable SLO thresholds.
2. Added health status aggregation logic to generate liveness reports (healthy/degraded/unhealthy/skipped).
3. Added a health checks CLI that validates table freshness and transformation job performance against SLA windows.
4. Implemented strict and non-strict health check modes for local-safe vs deployment contexts.
5. Added new make targets for standard and strict health checks.
6. Updated CI deployment integration to run health checks in safe skip mode and publish artifacts.
7. Updated release workflow to run health checks with configurable freshness and job duration thresholds.
8. Added unit and CLI tests for freshness validation, job duration checks, and liveness status aggregation.

## Validation
- Lint/type checks pass.
- Targeted tests for Batch 9.1 health monitoring and CLI pass.

## Notes
- Health checks currently validate `int_funnel_stage_events` freshness and `dbt-build-prod` job duration against local/production artifacts.
- In local contexts without dbt build artifacts, checks emit `skipped` status for transparency.
- Strict mode enforces non-skipped status; non-strict mode defaults to safe skip for local workflows.
