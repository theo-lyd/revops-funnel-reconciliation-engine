# Batch 2.6 Report: Hardening Ingestion and Freshness Reliability

## What was done
- Added ingestion audit logging for CRM ingestion into `observability.ingestion_audit`.
- Refactored synthetic lead ingestion to be idempotent (dedupe on lead_id + created_at + utm_campaign).
- Added fallback company-name derivation from email domain when source payload omits `company_name`.
- Added ingestion audit logging for marketing-leads ingestion.
- Reworked freshness SLA checks to use ingestion audit timestamps (not raw file mtimes).
- Added resilient HTTP retry behavior to synthetic API polling.

## How it was done
- Updated:
  - `scripts/ingest/load_crm_csv_to_duckdb.py`
  - `scripts/ingest/load_leads_jsonl_to_duckdb.py`
  - `scripts/monitor/check_freshness.py`
  - `scripts/ingest/poll_synthetic_leads_api.py`
- Introduced metadata-driven freshness by querying `observability.ingestion_audit`.

## Why it was done
- Eliminate duplicate lead ingestion and metric inflation across reruns.
- Improve robustness when upstream synthetic payload shape changes.
- Make freshness checks operationally meaningful by validating actual ingestion events.
- Reduce transient API failure impact using retry/backoff.

## Alternatives considered
- Full CDC with watermark table per source: strongest control, higher implementation complexity.
- Airbyte-native freshness monitoring only: good integration, less flexible for mixed custom ingestion scripts.
- Queue-based API ingestion (Kafka/Redpanda): high reliability, unnecessary overhead for current project stage.

## Command sequence used
```bash
# Updated ingestion scripts for idempotency and observability audit logging
# Updated freshness monitor to query observability metadata
# Added API polling retries for network resilience
```
