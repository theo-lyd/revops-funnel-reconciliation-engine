# Batch 2.3 Report: Stage Velocity Analytics

## What was done
- Added eventized journey model to convert lead-opportunity lifecycle into ordered stage events.
- Implemented window-function logic (`LAG`, `LEAD`) to compute event-to-event time deltas.
- Added opportunity-level velocity metric model with lead-to-engage and engage-to-close durations.
- Added stall indicators for open opportunities and slow-close indicators for historical deals.
- Added dbt model tests for stage-event and velocity outputs.

## How it was done
- Created intermediate models:
  - `dbt/models/intermediate/int_funnel_stage_events.sql`
  - `dbt/models/intermediate/int_funnel_velocity_metrics.sql`
- Updated model contracts:
  - `dbt/models/intermediate/_intermediate__models.yml`

## Why it was done
- Establish measurable mid-funnel timing signals required for leakage and friction analysis.
- Provide a reusable metric base for dashboard KPIs and anomaly detection phases.
- Keep lineage and logic transparent through SQL-native transformation patterns.

## Alternatives considered
- Direct aggregate metrics without eventization: simpler SQL, weaker auditability of stage transitions.
- Python velocity jobs outside dbt: flexible logic, weaker governance and warehouse-native testability.
- Full stage history snapshots first: richer chronology, but unnecessary overhead before baseline velocity KPIs.

## Command sequence used
```bash
# Added stage-event and velocity metric intermediate models
# Updated intermediate model test definitions
```
