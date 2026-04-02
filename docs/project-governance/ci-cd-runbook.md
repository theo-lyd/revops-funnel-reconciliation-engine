# CI/CD Pipeline Documentation

## Overview
The CI/CD pipeline enforces code quality, data model correctness, and production parity across all commits to the repository.

## Workflow Jobs

### 1) Quality Job (Runs on All PRs and Pushes)
**Trigger**: Every pull request and push to any branch.

**Steps**:
- Checkout code
- Setup Python 3.10
- Install dependencies (Airflow, base libraries, dev tools)
- Lint and type-check (Ruff, mypy)
- Unit tests (pytest)
- dbt parse validation (profiles/dependencies)
- dbt build staging and intermediate models
- dbt tests for all models
- Great Expectations validation

**Purpose**: Catch code quality issues and data model regressions early.

**Local Equivalent**: `make quality-gate`

---

### 2) Production Parity Check Job (Conditional, Secure)
**Trigger**: Only on **pushes to master** WITH Snowflake secrets available (e.g., deployment contexts).

**Prerequisites**:
- GitHub repository must have configured secrets:
  - `SNOWFLAKE_ACCOUNT`
  - `SNOWFLAKE_USER`
  - `SNOWFLAKE_PASSWORD` (optional when key-pair auth is configured)
  - `SNOWFLAKE_PRIVATE_KEY_PEM` (recommended for key-pair auth)
  - `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` (optional)
  - `SNOWFLAKE_ROLE`
  - `SNOWFLAKE_DATABASE`
  - `SNOWFLAKE_WAREHOUSE`
  - `SNOWFLAKE_SCHEMA`
  - `ROLLBACK_INCIDENT_WEBHOOK_URL` (optional; required only when incident dispatch is enabled)
  - `ROLLBACK_INCIDENT_WEBHOOK_TOKEN` (optional bearer token for incident webhook)
  - `RELEASE_ALLOWED_ACTORS` / `ROLLBACK_ALLOWED_ACTORS` (optional actor allowlists for release/rollback enforcement)

**Steps**:
- Checkout code
- Setup Python 3.10
- Install dependencies
- Setup local DuckDB warehouse
- Ingest bronze data
- Build local Gold layer models
- Run strict metric parity check (zero-tolerance comparison of DuckDB vs. Snowflake metrics)

**Purpose**:
- Verify that local DuckDB development state matches Snowflake production state.
- Enforce production parity as a deployment control.
- Only blocks production deployments if parity fails; does not affect local contributors or PRs.

**Local Equivalent**: `make metric-parity-check-strict`

**Environment Variables**:
- `PARITY_TOLERANCE_STRICT=0.0` (zero tolerance)
- `DBT_QUERY_TAG=ci-pipeline-parity-check`

---

## How It Works for Different Scenarios

### Scenario 1: Local Contributor (No Snowflake Access)
```
PR created with changes -> Quality job runs -> Passes -> PR ready for review
Production parity job: SKIPPED (no Snowflake secrets in contributor's fork)
```
Effect: **Zero impact on local development workflow.**

### Scenario 2: Merge to Master (Deployment Pipeline, With Secrets)
```
Commit to master -> Quality job runs -> Passes
Production parity job runs -> Compares DuckDB vs. Snowflake -> Passes/Fails
If parity fails: Alert DevOps/Platform team to investigate
If parity passes: Safe to deploy
```
Effect: **Production parity is automatically validated before release.**

### Scenario 3: PR from Contributor Without Fork Secrets
```
PR created -> Quality job runs -> Passes
Production parity job: SKIPPED (no Snowflake secrets on PR)
```
Effect: **Local contributor work is not blocked; merge still allowed after review.**

---

## Setting Up Snowflake Secrets (Repository Admin)

To enable the production parity job:

1. Go to repository Settings > Secrets and variables > Actions
2. Create the following repository secrets:
   - `SNOWFLAKE_ACCOUNT`: Your Snowflake account ID
   - `SNOWFLAKE_USER`: CI/CD user account (recommend service account with limited role)
   - `SNOWFLAKE_PASSWORD`: Service account password (use secure secret management)
   - `SNOWFLAKE_ROLE`: Role assigned to CI user (recommend `TRANSFORMER` or least-privilege equivalent)
   - `SNOWFLAKE_DATABASE`: Target Snowflake database (e.g., `REVOPS`)
   - `SNOWFLAKE_WAREHOUSE`: Warehouse for CI runs (recommend small/dev warehouse)
   - `SNOWFLAKE_SCHEMA`: Schema for CI model builds (recommend `analytics` or similar)

3. **Security Best Practices**:
   - Use a dedicated CI/CD service account with minimal role permissions.
   - Rotate credentials regularly.
  - Prefer Snowflake key-pair authentication in release contexts.
  - Restrict release execution with `RELEASE_ALLOWED_ACTORS` secret.
   - Never commit secrets to repository.

---

## Disabling/Customizing Jobs

### Disable Production Parity for Maintenance
If you want to temporarily skip the parity check (e.g., during maintenance):

1. Go to `.github/workflows/ci.yml`
2. Modify the `if` condition for `production-parity-check` job.
3. Commit to master.

**Example**: Skip parity check (not recommended for production):
```yaml
if: false  # Disables the job
```

To re-enable:
```yaml
if: |
  github.event_name == 'push' &&
  github.ref == 'refs/heads/master' &&
  secrets.SNOWFLAKE_ACCOUNT != ''
```

---

## Monitoring CI Status

### View Pipeline Status
- GitHub: Go to Actions tab in the repository to see workflow runs and detailed logs.
- Each job shows:
  - Run status (✅ passed / ❌ failed / ⏭️ skipped)
  - Duration
  - Logs for debugging

### Common Failure Reasons

**Quality Job Fails**:
- Lint/type errors: Fix with `make format` and `mypy` locally.
- Test failures: Run `make test` locally to debug.
- dbt model errors: Run `make dbt-build` locally.

**Production Parity Job Fails**:
- Parity drift: Snowflake metrics differ from DuckDB by more than 0% (zero-tolerance).
- Causes:
  - Data lag in Snowflake (incomplete ingestion).
  - Differences in model logic between targets.
  - Differing source data timestamps.
- Resolution: Investigate with `scripts/quality/run_metric_parity_check.py --output-json`.

---

## Future Enhancements

1. **Conditional Secret Handling**: Extend logic to handle other environment-specific deployments.
2. **Artifact Retention**: Tune retention windows and centralized indexing for CI evidence artifacts.
3. **Webhook Delivery Robustness**: Add retry/backoff and optional dead-letter queue for incident dispatch failures.
