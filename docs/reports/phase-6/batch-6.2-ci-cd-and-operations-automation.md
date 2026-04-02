# Batch 6.2: CI/CD and Operations Automation

## Objective
Implement the operational automation brief for Phase 6 by adding changed-model dbt selection, slim CI execution, an end-to-end Airflow DAG, cache refreshes, and a guarded deployment promotion manifest.

## Deliverables
- `src/revops_funnel/deployment_ops.py`
- `scripts/ops/run_changed_model_dbt.py`
- `scripts/ops/refresh_runtime_caches.py`
- `scripts/ops/promote_deployment.py`
- `dags/revops_end_to_end_pipeline.py`
- `.github/workflows/release.yml`

## What Changed
1. Added a shared deployment helper module to infer dbt selectors from changed files and manage cache/promotion artifacts.
2. Slimmed CI so dbt build and test run against the changed-model selector instead of always running the full model surface.
3. Added a release workflow that runs production dbt deploy steps, refreshes caches, and writes a deployment promotion manifest.
4. Added an Airflow DAG that orchestrates the end-to-end pipeline with cache refresh and promotion steps.

## Validation
- Selector logic is unit-testable and deterministic.
- Promotion is guarded by explicit runtime enablement and a passed parity report.

## Notes
- This batch keeps the repository's pragmatic local-dev-plus-CI posture intact.
- When no relevant model files change, the selector falls back to the full dashboard-oriented model set.
