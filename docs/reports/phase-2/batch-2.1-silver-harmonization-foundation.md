# Batch 2.1 Report: Silver Harmonization Foundation

## What was done
- Added reusable dbt macros for text normalization and deal stage ranking.
- Built intermediate Silver model `int_opportunity_enriched` to harmonize opportunities with account, product, and sales-team context.
- Built deterministic lead-account matcher `int_lead_account_matches` using normalized company/account names.
- Built initial stitched mapping model `int_lead_to_opportunity_base` using account and temporal proximity logic.
- Added model-level tests and documentation for intermediate layer entities.

## How it was done
- Created macros under `dbt/macros/`:
  - `normalize_text.sql`
  - `deal_stage_rank.sql`
- Created intermediate models under `dbt/models/intermediate/`:
  - `int_opportunity_enriched.sql`
  - `int_lead_account_matches.sql`
  - `int_lead_to_opportunity_base.sql`
  - `_intermediate__models.yml`

## Why it was done
- Establish a conformed Silver layer before advanced fuzzy matching and velocity analytics.
- Make matching and stage logic reusable and testable through centralized macros.
- Provide a deterministic baseline to benchmark later probabilistic reconciliation improvements.

## Alternatives considered
- Perform all enrichment in a single wide model: simpler initial setup, poor maintainability and test granularity.
- Python-based record linkage first: stronger fuzzy capability, weaker warehouse-native lineage and SQL transparency.
- Match only by email hash: robust when available, but CRM source currently lacks lead-email alignment fields.

## Command sequence used
```bash
mkdir -p docs/reports/phase-2
# Added Silver harmonization macros, intermediate models, and model tests
# Updated project artifacts for Batch 2.1
```
