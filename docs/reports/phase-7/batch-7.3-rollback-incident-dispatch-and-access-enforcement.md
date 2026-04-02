# Batch 7.3: Rollback Incident Dispatch and Execution Access Enforcement

## Objective
Harden release failure handling by integrating rollback incident webhook dispatch and tightening rollback playbook execution access controls.

## Deliverables
- `src/revops_funnel/deployment_ops.py`
- `scripts/ops/execute_rollback_playbook.py`
- `scripts/ops/dispatch_rollback_incident.py`
- `.github/workflows/release.yml`
- `.github/workflows/ci.yml`
- `tests/test_deployment_ops.py`
- `tests/test_execute_rollback_playbook_cli.py`
- `Makefile`

## What Changed
1. Added `dispatch_rollback_incident_payload` helper with artifacted dispatch reporting for skipped/sent/failed outcomes.
2. Added `validate_release_actor_access` utility and wired actor-gated execution into rollback playbook CLI (`--require-release-access`).
3. Added dedicated rollback incident dispatch CLI with strict mode for deployment contexts.
4. Updated release workflow failure path to:
   - require release actor access for rollback playbook execution,
   - optionally execute rollback actions in controlled mode,
   - dispatch incident notifications using webhook secrets,
   - enforce dispatch outcome when `ROLLBACK_INCIDENT_STRICT=true`.
5. Extended CI deployment integration job to validate rollback incident dispatch artifact generation in safe skip mode.
6. Added unit and CLI tests for actor allowlist checks and webhook dispatch behaviors.

## Validation
- Lint/type checks pass.
- Test suite passes with expanded deployment and rollback coverage.

## Notes
- Incident dispatch is non-blocking by default to preserve local-safe workflows.
- Strict mode is available for production environments requiring guaranteed incident dispatch.
