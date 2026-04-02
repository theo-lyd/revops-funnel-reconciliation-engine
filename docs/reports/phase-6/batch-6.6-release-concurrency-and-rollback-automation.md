# Batch 6.6: Release Concurrency and Rollback Automation

## Objective
Prevent overlapping release executions and automate rollback evidence generation when release workflows fail.

## Deliverables
- `.github/workflows/release.yml`
- `.github/workflows/ci.yml`
- `src/revops_funnel/deployment_ops.py`
- `scripts/ops/rollback_deployment.py`
- `tests/test_deployment_ops.py`

## What Changed
1. Added workflow-level concurrency controls:
   - release workflow serialization by branch
   - CI cancellation for superseded pull-request runs
2. Added rollback report model and helper in deployment ops shared module.
3. Added rollback CLI (`scripts/ops/rollback_deployment.py`) for automation and reproducibility.
4. Added release workflow failure hook to generate rollback manifest automatically.
5. Included rollback artifact path in release artifact uploads.
6. Added unit test coverage for rollback report generation.

## Validation
- Lint/type and test suites pass with rollback helpers included.
- Release workflow emits rollback artifact on failure when promotion context exists.

## Notes
- Rollback automation is manifest-based and does not force destructive rollback actions.
- Local-safe behavior remains unchanged for non-release execution paths.
