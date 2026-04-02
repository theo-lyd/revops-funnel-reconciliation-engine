# Batch 8.2: Query-Cost Observability and Spend Attribution Artifacts

## Objective
Add machine-readable warehouse spend attribution artifacts using Snowflake query telemetry to improve cost observability and operational tuning decisions.

## Deliverables
- `src/revops_funnel/cost_observability.py`
- `scripts/ops/generate_query_cost_attribution.py`
- `tests/test_cost_observability.py`
- `tests/test_generate_query_cost_attribution_cli.py`
- `Makefile`
- `.env.example`
- `.github/workflows/release.yml`
- `.github/workflows/ci.yml`

## What Changed
1. Added shared cost observability utilities for aggregating query telemetry by query tag and warehouse.
2. Added a Snowflake-aware CLI to generate query-cost attribution artifacts with strict/non-strict modes.
3. Added local-safe fallback behavior when Snowflake credentials or connector availability is missing.
4. Added new make targets for regular and strict query-cost attribution generation.
5. Updated release workflow to generate and publish query-cost attribution artifacts with configurable lookback and scope settings.
6. Updated CI deployment-integration to run attribution in safe skip mode and publish artifacts.
7. Added tests for attribution aggregation logic and CLI output behavior.

## Validation
- Lint/type checks pass.
- Test suite passes with query-cost observability and attribution coverage.

## Notes
- Attribution accuracy depends on Snowflake query history visibility and role permissions.
- In environments without telemetry access, the artifact is generated in `skipped` or `no-data` mode for transparency.
