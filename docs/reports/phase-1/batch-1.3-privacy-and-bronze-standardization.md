# Batch 1.3 Report: Privacy and Bronze Standardization

## What was done
- Implemented Bronze sanitization/export pipeline to Parquet for downstream ELT processing.
- Added hashing of sales-agent and manager fields before export.
- Standardized sales pipeline output with explicit `currency_iso='USD'`.
- Added command entrypoint `make export-bronze`.

## How it was done
- Added `scripts/transform/export_bronze_parquet.py`.
- Exported core Bronze entities to `data/processed/bronze/*.parquet`.
- Introduced temporary sanitized table for personnel field anonymization.
- Updated repository commands and usage docs.

## Why it was done
- Enforce privacy-by-design before analytical workloads consume data.
- Standardize schema and currency semantics early for consistency.
- Improve interoperability by publishing clean Parquet datasets.

## Alternatives considered
- Keep data only in warehouse tables: simpler pipeline, weaker portability for reproducible analysis outside warehouse.
- Full tokenization service for identity fields: stronger governance, unnecessary complexity at this stage.
- Anonymize at source API only: insufficient coverage for CRM personnel attributes.

## Command sequence used
```bash
mkdir -p scripts/transform data/processed/bronze
# Created Bronze sanitization/export script and command wiring
# Updated README with export step
```
