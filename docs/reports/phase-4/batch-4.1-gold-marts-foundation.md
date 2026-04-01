# Batch 4.1 Report: Gold Marts Foundation

## What was done
- Implemented `fct_revenue_funnel` in the Gold layer using reconciled velocity outputs.
- Added leakage classification fields:
  - `leakage_reason`
  - `stage_age_bucket`
  - `is_leakage_point`
- Implemented `dim_sales_teams` with team-level opportunity rollups and win rate.
- Added model contracts and tests for accepted values, not-null constraints, and metric ranges.

## How it was done
- Added marts SQL models under `dbt/models/marts/`.
- Added marts YAML contract file `_marts__models.yml`.
- Reused upstream intermediate models to avoid duplicated logic.

## Why it was done
- Convert Silver-layer technical outputs into business-ready consumption models.
- Provide direct support for executive funnel analytics.
- Create a stable contract for BI and semantic consumers in subsequent batches.

## Validation plan for this batch
```bash
make dbt-build
make dbt-test
make quality-gate
```

## Risks and notes
- Metric semantics (CAC/LTV) are intentionally deferred to Batch 4.2 semantic contract work.
- Snowflake production deployment details are captured in Phase 4 implementation plan and will be operationalized in Batch 4.4.

## Next batch
Batch 4.2: Semantic metric contract and governed metric glossary.
