# Batch 1.2 Report: Bronze Ingestion Pipelines

## What was done
- Implemented CRM CSV loader to land source tables into `bronze_raw` DuckDB schema.
- Implemented synthetic leads API poller to capture event-like lead data into JSONL landing zone.
- Implemented JSONL-to-DuckDB loader for `bronze_raw.marketing_leads` with email hashing.
- Added Makefile commands to run each ingestion step.
- Updated README with Bronze ingestion workflow.

## How it was done
- Added scripts in `scripts/ingest/`:
  - `load_crm_csv_to_duckdb.py`
  - `poll_synthetic_leads_api.py`
  - `load_leads_jsonl_to_duckdb.py`
- Added command wrappers:
  - `make ingest-crm`
  - `make poll-leads`
  - `make ingest-leads`
- Added ingestion instructions to project documentation.

## Why it was done
- Establish a hybrid ingestion pattern (batch CSV + API events) required by the project thesis.
- Separate collection and loading concerns for better reliability and troubleshooting.
- Ensure PII minimization path is available before analytical consumption.

## Alternatives considered
- Airbyte-only ingestion for both sources: unified UI, less code ownership and portability in local-only contexts.
- One monolithic ETL script: simpler startup, weaker operability and observability.
- Direct API-to-warehouse writes without landing zone: fewer files, lower replayability.

## Command sequence used
```bash
mkdir -p scripts/ingest data/raw/marketing
# Created CRM/API ingestion scripts and Makefile targets
# Updated README ingestion section
```
