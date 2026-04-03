# Artifact Policy

## Purpose
Keep source control focused on durable source-of-truth changes while preserving auditability for release evidence.

## Policy
- `artifacts/` is ignore-by-default.
- The only allowlisted tracked artifact path is:
  - `artifacts/release-evidence/`
- Runtime artifacts under paths such as `artifacts/promotions/`, `artifacts/monitoring/`, `artifacts/runbooks/`, and `artifacts/performance/` are not committed.

## Rationale
- Reduce noisy diffs and merge conflicts from frequently changing generated files.
- Avoid repository bloat and non-deterministic output churn.
- Reduce secret-scanner false positives from high-entropy fields in generated payloads.
- Keep evidence governance explicit via a dedicated release-evidence path.

## Guardrail
- CI enforces this via `scripts/governance/enforce_artifact_policy.py`.
- Local check is available through `make artifact-policy-check`.

## Exceptions
- A tracked artifact outside `artifacts/release-evidence/` requires explicit governance approval and must be migrated or removed in the next hardening cycle.
