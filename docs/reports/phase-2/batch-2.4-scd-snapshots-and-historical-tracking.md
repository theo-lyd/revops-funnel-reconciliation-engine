# Batch 2.4 Report: SCD Snapshots and Historical Tracking

## What was done
- Implemented dbt snapshot for opportunity lifecycle (`snp_opportunity_lifecycle`) using SCD Type 2 semantics.
- Implemented dbt snapshot for lead-account reconciliation outcomes (`snp_lead_account_resolution`).
- Added snapshot schema documentation and baseline tests for `dbt_valid_from` fields.
- Added `make dbt-snapshot` command to operationalize snapshot runs.

## How it was done
- Created snapshot SQL files under `dbt/snapshots/` with `strategy='check'` and explicit `check_cols`.
- Configured hard-delete invalidation to preserve historical audit semantics.
- Added snapshot YAML contract file for metadata and tests.
- Updated command and README workflow for execution.

## Why it was done
- Preserve point-in-time state changes for opportunity stages and reconciliation decisions.
- Enable historically accurate funnel diagnostics and trend analysis.
- Provide auditable lineage for leadership and governance requirements.

## Alternatives considered
- `timestamp` snapshot strategy: simpler for systems with trusted update timestamps, not available consistently in all current models.
- Event-sourcing table only: rich chronology, but does not directly provide SCD2 row validity windows.
- Warehouse-native streams/tasks only: efficient in platform-specific setups, less portable for this capstone.

## Command sequence used
```bash
# Added dbt snapshots and snapshot schema tests
# Updated Makefile and README to run snapshot workflows
```
