# Batch 0.2 Report: Warehouse and dbt Foundation

## What was done
- Initialized dbt project structure and package dependencies.
- Added dual-environment profile template: DuckDB for development, Snowflake for production.
- Added local warehouse bootstrap SQL and Python initializer for schema creation.
- Added staging source metadata and first staging model for sales pipeline.
- Extended automation commands in `Makefile` for warehouse and dbt workflows.

## How it was done
- Created `dbt/dbt_project.yml`, `dbt/packages.yml`, and profile template under `dbt/profiles/`.
- Added schema bootstrap SQL in `scripts/sql/bootstrap_duckdb.sql`.
- Implemented `scripts/init_warehouse.py` using DuckDB connection APIs.
- Added source contract in `dbt/models/staging/src_crm.yml`.
- Added first canonical staging model `dbt/models/staging/stg_sales_pipeline.sql`.

## Why it was done
- Create a production-like modeling backbone early.
- Ensure local development speed while preserving enterprise deployment portability.
- Establish schema boundaries (`bronze_raw`, `silver_*`, `gold`, observability) before ingestion logic lands.

## Alternatives considered
- Running only Snowflake in all environments: better environment parity, higher cost and slower local iteration.
- DuckDB-only architecture: faster iteration, limited enterprise governance and scaling features.
- Spark-based local simulation: more scalable patterns, excessive complexity for this capstone scope.

## Command sequence used
```bash
mkdir -p dbt/models/{staging,intermediate,marts} dbt/macros dbt/snapshots dbt/profiles scripts/sql
# Created dbt configuration, profile templates, staging metadata/model, and warehouse bootstrap utilities
# (via automated file generation in the coding agent)
```
