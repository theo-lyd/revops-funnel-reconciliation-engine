# Batch 6.5: Airflow Operational Reliability Hardening

## Objective
Harden scheduled orchestration for unattended execution by using deterministic full dbt paths, bounded retries/timeouts, and clearer step sequencing for recovery.

## Deliverables
- `dags/revops_end_to_end_pipeline.py`
- `tests/test_airflow_pipeline_dag.py`

## What Changed
1. Replaced changed-model dbt execution in the scheduled DAG with deterministic full dbt build/test steps.
2. Removed external API polling dependency from scheduled path to reduce orchestration flakiness.
3. Added preflight and freshness checks as explicit pipeline gates.
4. Added bounded reliability controls:
   - task-level execution timeout
   - increased retries with exponential backoff
   - DAG-level run timeout
5. Added parity artifact generation before cache refresh and release readiness.
6. Added DAG-level test coverage for deterministic dbt task path.

## Validation
- DAG structure is validated by automated tests.
- Full lint/type/test gates remain green after orchestration changes.

## Notes
- Local-safe behavior remains unchanged.
- Strict production promotion behavior is still controlled by existing release gate settings.
