# Batch 7.1: Snowflake Key-Pair Auth and Release Access Controls

## Objective
Start Phase 7 by adding secure key-pair authentication support for Snowflake and tightening release workflow access controls.

## Deliverables
- `src/revops_funnel/snowflake_auth.py`
- `scripts/quality/run_metric_parity_check.py`
- `scripts/quality/run_release_readiness_gate.py`
- `scripts/preflight_check.py`
- `.github/workflows/release.yml`
- `dbt/profiles/profiles.yml.example`
- `tests/test_snowflake_auth.py`

## What Changed
1. Added shared Snowflake auth helper supporting password and key-pair modes.
2. Updated parity and release-readiness checks to accept password-or-key auth in strict and local-safe modes.
3. Added release workflow branch/actor access checks and optional key materialization from GitHub secrets.
4. Added dbt profile support for `private_key_path` and `private_key_passphrase`.
5. Updated prod preflight checks to require an auth mode (password or key-pair).
6. Added unit tests for auth-mode validation and connector-auth payload generation.

## Validation
- Lint/type checks pass.
- Test suite passes with new auth helper unit tests.

## Notes
- Password mode remains supported for backwards compatibility.
- Key-pair mode is preferred for release/deployment contexts.
