# Secrets Rotation and Emergency Access Runbook

## Purpose
Provide an operationally safe, auditable procedure for secret rotation and emergency access in development, CI/CD, and Snowflake production contexts.

## Scope
- Codespaces secrets
- GitHub Actions encrypted secrets
- Snowflake user credentials and role bindings
- dbt profile environment variables

## Rotation policy
- Standard cadence: every 90 days.
- Immediate rotation triggers:
  - suspected compromise
  - personnel role change
  - failed access audit
  - unapproved credential exposure event

## Roles and responsibilities
- Security Owner: approves rotation window and incident classification.
- Platform Owner: executes secret updates in GitHub and runtime environments.
- Data Engineering Owner: validates dbt and orchestration flows post-rotation.
- Auditor: verifies evidence and closure.

## Standard rotation procedure
1. Announce maintenance window and freeze production deploys.
2. Rotate Snowflake credentials and verify role grants.
3. Update GitHub Actions secrets and Codespaces secrets.
4. Validate with:
   - `make lint`
   - `make test`
   - `make quality-gate`
5. Validate Snowflake target (if applicable):
   - `make dbt-build-prod`
   - `make dbt-test-prod`
6. Run parity check:
   - `make metric-parity-check-strict`
7. Record evidence in phase/governance logs.

## Emergency access procedure
1. Incident trigger confirmed by Security Owner.
2. Generate short-lived emergency credential (time-boxed, least privilege).
3. Restrict scope to required objects and duration.
4. Capture complete command/action audit trail.
5. Revoke emergency credential immediately after incident resolution.
6. Run post-incident credential rotation and verification.

## Evidence requirements
- Rotation date/time and approver.
- Changed secrets inventory (names only, no values).
- Validation command outputs (pass/fail summaries).
- Incident IDs and remediation notes (if emergency path used).

## Prohibited practices
- Storing live credentials in repository files.
- Shared team credentials without individual accountability.
- Rotation without validation and evidence capture.
