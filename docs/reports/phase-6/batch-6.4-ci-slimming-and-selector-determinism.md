# Batch 6.4: CI Slimming and Selector Determinism

## Objective
Reduce duplicate CI workload while making dbt selector resolution deterministic, auditable, and strict where appropriate.

## Deliverables
- `.github/workflows/ci.yml`
- `src/revops_funnel/deployment_ops.py`
- `scripts/ops/run_changed_model_dbt.py`
- `tests/test_deployment_ops.py`

## What Changed
1. Split CI dbt behavior by event type:
   - Pull requests: changed-model dbt build/test with strict selector mode.
   - Pushes to master: full dbt build/test over staging, intermediate, and marts.
2. Added deterministic selector-decision resolution with fallback reason tracking.
3. Added selector decision artifact output (`artifacts/ci/selector_decision.json`) and CI upload.
4. Added tests for selector fallback behavior, strict-mode failure, and selector report writing.

## Validation
- Lint/type and tests remain green after CI and selector changes.
- Selector strict mode fails fast on unresolved git diff in PR contexts.

## Notes
- Local development remains fallback-safe by default.
- Strict determinism is enforced in CI where reproducibility matters most.
