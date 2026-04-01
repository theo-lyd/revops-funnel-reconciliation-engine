# Post-Phase 4 Hardening Block 2: Observability and Data Reliability

## Objective
Improve observability and operational reliability by adding dbt freshness specifications, release evidence packaging standards, and executable query-pack validation.

## What was implemented
1. dbt source freshness specs for `bronze_raw.marketing_leads`.
2. New Make target `dbt-source-freshness`.
3. New query-pack validation runner script:
   - `scripts/quality/run_query_pack_validation.py`
4. New Make target `query-pack-validate`.
5. Added `query-pack-validate` into `quality-gate`.
6. Release evidence bundle template added and linked into phase checklist.

## Why this improves reliability
- Freshness specs enforce recency monitoring in dbt-native workflows.
- Query packs move from static documentation to executable, validated artifacts.
- Evidence template improves audit quality and defense readiness.

## Validation plan
```bash
make lint
make test
make quality-gate
make dbt-source-freshness
```

## Notes
- Freshness specs use a recency filter aligned with current synthetic data windows.
- Query-pack validation is read-only and does not alter warehouse state.
