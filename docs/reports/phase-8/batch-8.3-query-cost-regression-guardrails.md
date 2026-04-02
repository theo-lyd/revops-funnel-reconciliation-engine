# Batch 8.3: Query-Cost Regression Guardrails

## Objective
Add artifact-driven regression controls that compare current query-cost attribution against a baseline and enforce configurable thresholds for cost and runtime growth.

## Deliverables
- `src/revops_funnel/cost_observability.py`
- `scripts/ops/check_query_cost_regression.py`
- `tests/test_cost_observability.py`
- `tests/test_check_query_cost_regression_cli.py`
- `Makefile`
- `.env.example`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`

## What Changed
1. Extended cost observability helpers with query-cost regression detection logic and threshold modeling.
2. Added a new regression-check CLI that compares current and baseline attribution artifacts and emits a machine-readable regression report.
3. Implemented strict and non-strict baseline modes to preserve local-safe defaults while enabling deployment-time enforcement.
4. Added new make targets for standard and strict query-cost regression checks.
5. Updated CI deployment integration to run regression checks in safe skip mode and publish regression artifacts.
6. Updated release workflow to run regression checks with configurable threshold and strictness controls.
7. Added unit and CLI tests for regression detection behavior and artifact contract semantics.

## Validation
- Lint/type checks pass.
- Targeted tests for Batch 8.3 cost regression logic and CLI pass.

## Notes
- Regression checks require a usable baseline attribution artifact for strict enforcement.
- In local/non-strict contexts without a baseline, the regression checker emits a `skipped` artifact for auditability.
