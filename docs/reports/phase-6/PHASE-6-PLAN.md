# Phase 6 Plan: Monitoring Delivery and Operations Automation

## Phase Objective
Automate the lifecycle of the data product with CI selection, test automation, release gating, Airflow orchestration, cache refreshes, and deployment promotion while preserving the safe local-dev-plus-CI posture.

## Planned Scope
- Batch 6.1: Email notification delivery for monitoring alerts.
- Batch 6.2: CI/CD and operations automation.
- Batch 6.3: Release gate integrity and artifact auditability.
- Batch 6.4: CI slimming and selector determinism.
- Batch 6.5: Airflow operational reliability hardening.
- Batch 6.6: Release concurrency controls and rollback automation.

## Design Principles
- Preserve local-safe behavior when SMTP settings are absent.
- Keep email transport optional and environment-driven.
- Reuse the existing monitoring report and anomaly summaries.
- Keep dbt execution focused on changed models in CI when possible.
- Keep promotion guarded by explicit release gates and reproducible manifests.
- Ensure release workflows produce auditable evidence artifacts for every promotion decision.
- Ensure selector decisions are deterministic and captured as machine-readable CI artifacts.
- Keep scheduled orchestration deterministic, bounded, and resilient for unattended runs.
- Enforce workflow concurrency boundaries and generate rollback evidence automatically on release failures.

## Success Criteria
- Monitoring alerts can be sent through SMTP when configured.
- The CLI still completes without email credentials in dev mode.
- Email behavior is covered by fixture-based tests.
- CI can infer and run only the impacted dbt models.
- Automated release and promotion workflows are documented and executable.
- Release promotion remains blocked unless strict parity gates pass.
- CI avoids duplicate dbt execution paths while preserving confidence by event type.
- Airflow scheduled runs execute deterministic full validation path with explicit recovery gates.
- Release workflow prevents overlapping runs and publishes rollback context when failures occur.
