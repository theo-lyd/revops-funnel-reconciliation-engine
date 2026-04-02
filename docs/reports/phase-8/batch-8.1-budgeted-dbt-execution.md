# Batch 8.1: Budgeted dbt Execution for Production Build/Test

## Objective
Introduce explicit runtime and concurrency budgets for production dbt build/test execution while preserving local-safe defaults and publishing performance artifacts for auditability.

## Deliverables
- `src/revops_funnel/performance.py`
- `scripts/ops/run_dbt_budgeted.py`
- `tests/test_performance_budget.py`
- `tests/test_run_dbt_budgeted_cli.py`
- `Makefile`
- `.env.example`
- `.github/workflows/release.yml`

## What Changed
1. Added shared performance helper utilities to resolve effective thread caps and timeout budgets by environment.
2. Added budgeted dbt execution CLI to run `dbt build` or `dbt test` with:
   - thread cap enforcement,
   - timeout enforcement,
   - machine-readable execution report artifacts.
3. Updated `Makefile` production dbt build/test targets to use budgeted execution wrappers.
4. Added budget configuration defaults to `.env.example` for local and production tuning.
5. Updated release workflow to expose budget-related workflow variable overrides and publish performance artifacts.
6. Added unit and CLI tests for thread capping, timeout behavior, and report contract output.

## Validation
- Lint/type checks pass.
- Test suite passes with performance budget coverage.

## Notes
- Local development defaults remain conservative and non-blocking.
- Production tuning can be managed via workflow variables without code changes.
