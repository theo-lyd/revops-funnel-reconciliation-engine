# Batch 7.4: Webhook Retry/Backoff and Dead-Letter Hardening

## Objective
Improve rollback incident notification reliability by adding configurable retry/backoff delivery controls and dead-letter artifacts for terminal webhook failures.

## Deliverables
- `src/revops_funnel/deployment_ops.py`
- `scripts/ops/dispatch_rollback_incident.py`
- `.github/workflows/release.yml`
- `.github/workflows/ci.yml`
- `.env.example`
- `Makefile`
- `tests/test_deployment_ops.py`
- `tests/test_dispatch_rollback_incident_cli.py`

## What Changed
1. Extended rollback incident dispatch helper with retry attempts, fixed backoff delay, and dead-letter artifact output.
2. Added delivery metadata to dispatch reports (`attempt_count`, `max_attempts`, dead-letter status/path).
3. Updated rollback incident CLI to expose retry/backoff/dead-letter options and environment defaults.
4. Updated release workflow failure path to apply configurable retry/backoff controls via workflow vars and upload dead-letter artifacts.
5. Extended CI deployment-integration artifact upload to include dead-letter outputs.
6. Added tests for retry-success, terminal failure dead-letter creation, and CLI strict/non-strict behavior.

## Validation
- Lint/type checks pass.
- Test suite passes with expanded rollback incident robustness coverage.

## Notes
- Local/default behavior remains non-blocking unless strict mode is enabled.
- Dead-letter artifacts preserve payload and error context for escalation workflows.
