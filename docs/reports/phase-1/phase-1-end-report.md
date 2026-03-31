# Phase 1 End Report: Data Ingestion and Bronze Layer

## Phase objective
Move raw CRM and synthetic lead data into a reliable Bronze layer with contract checks, privacy controls, and freshness observability.

## Scope delivered
- Batch 1.1: Source contracts and staging model foundations.
- Batch 1.2: CRM + synthetic API ingestion utilities.
- Batch 1.3: Privacy and schema standardization exports to Parquet.
- Batch 1.4: Freshness SLA monitoring and Airflow orchestration.

## What was done
1. Defined source contracts and dbt staging models for CRM and marketing leads.
2. Implemented ingestion scripts for CSV and API-origin events into `bronze_raw`.
3. Added privacy controls with hashing for sensitive personnel/email fields.
4. Standardized currency semantics (`currency_iso`) in Bronze exports.
5. Added freshness SLA monitoring with optional Slack alerts.
6. Added an hourly Airflow DAG orchestrating ingest, transform, and SLA checks.

## How it was done
- Built modular Python scripts under `scripts/ingest/`, `scripts/transform/`, and `scripts/monitor/`.
- Used DuckDB as local warehouse for rapid iteration and low-cost development.
- Encoded source metadata and quality tests in dbt source/model definitions.
- Wired operational commands through `Makefile` for repeatable workflows.

## Why it was done
- Align with hybrid ingestion thesis (batch + API stream-like source).
- Create enterprise-style operational controls from early phase.
- Prepare a clean, trusted foundation for Silver reconciliation logic in Phase 2.

## Alternative implementation paths
1. Airbyte-managed ingestion and normalization end-to-end.
2. Kafka-based stream ingestion for synthetic leads.
3. Direct-to-Snowflake loading without local DuckDB staging.
4. Data contract enforcement via schema registry tooling.

## Command sequence used (phase aggregate)
```bash
# Batch 1.1
mkdir -p docs/reports/phase-1 dbt/models/staging/{crm,marketing}
# Created source contract YAML, staging SQL models, and runbook

# Batch 1.2
mkdir -p scripts/ingest data/raw/marketing
# Created ingestion scripts and Makefile targets

# Batch 1.3
mkdir -p scripts/transform data/processed/bronze
# Created sanitization/export logic and command wrappers

# Batch 1.4
mkdir -p scripts/monitor
# Created SLA monitoring script and Airflow DAG orchestration
```

## Exit criteria status
- Completeness: met.
- Correctness: met via static checks and schema-tested model definitions.
- Usability: met with command-based workflows and runbooks.

## Next phase readiness
Phase 2 can start with funnel stitching, stage-velocity calculations, and reusable conversion macros.
