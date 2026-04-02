# Batch 6.3: Release Gate Integrity and Artifact Auditability

## Objective
Harden the release path so promotion is strictly gated by parity outcomes and every release decision emits durable machine-readable evidence.

## Deliverables
- `.github/workflows/release.yml`
- `src/revops_funnel/deployment_ops.py`
- `scripts/ops/promote_deployment.py`
- `tests/test_deployment_ops.py`

## What Changed
1. Added strict parity execution to the release workflow prior to deployment promotion.
2. Added parity baseline setup in release (local DuckDB build + strict Snowflake parity gate).
3. Expanded deployment promotion manifest contract with release metadata and artifact checksums.
4. Added artifact publishing in release workflow for parity, cache refresh, and promotion manifests.

## Validation
- Promotion remains blocked unless parity status is passed.
- Promotion manifest metadata and checksum fields are covered by unit tests.

## Notes
- Local development behavior remains unchanged and non-blocking.
- Strict gating applies only in release/deployment contexts.
