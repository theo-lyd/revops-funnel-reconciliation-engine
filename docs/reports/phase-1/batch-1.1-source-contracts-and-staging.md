# Batch 1.1 Report: Source Contracts and Staging Definitions

## What was done
- Defined canonical source contracts for CRM and synthetic lead sources.
- Added staging models for accounts, products, sales teams, sales pipeline, and marketing leads.
- Introduced standard casting, null handling, and naming normalization in staging SQL.
- Removed superseded staging files to prevent duplicate model definitions.
- Added source contract runbook for operational usage.

## How it was done
- Created `dbt/models/staging/crm/_crm__sources.yml` with source metadata and model tests.
- Added SQL transformations under `dbt/models/staging/crm/` and `dbt/models/staging/marketing/`.
- Normalized product naming inconsistencies in pipeline model.
- Removed obsolete files at `dbt/models/staging/src_crm.yml` and `dbt/models/staging/stg_sales_pipeline.sql`.
- Added `docs/runbooks/source-contracts.md` documenting contracts and checks.

## Why it was done
- Establish strict source contracts before ingestion automation.
- Ensure downstream models consume standardized, type-safe datasets.
- Reduce ambiguity and runtime failures caused by inconsistent raw values.

## Alternatives considered
- Source contracts in an external catalog (OpenMetadata/DataHub): richer governance, higher setup overhead.
- Keep all staging logic in Python ETL layer: simpler dbt, weaker lineage and testing semantics in analytics layer.
- Single combined staging model: fewer files, but poor modularity and maintainability.

## Command sequence used
```bash
mkdir -p docs/reports/phase-1 dbt/models/staging/{crm,marketing}
# Created source contract YAML and staging SQL models
# Removed superseded staging files
# Added source contract runbook
```
