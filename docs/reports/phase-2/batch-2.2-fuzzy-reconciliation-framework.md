# Batch 2.2 Report: Fuzzy Reconciliation Framework

## What was done
- Added fuzzy lead-to-account candidate model with heuristic similarity scoring.
- Added resolved lead-to-account model that prioritizes deterministic over fuzzy matches.
- Extended lead-to-opportunity base model to use resolved matches and include provenance/confidence metadata.
- Expanded intermediate-layer tests to validate match strategy, type, confidence, and confidence bands.

## How it was done
- Created:
  - `dbt/models/intermediate/int_lead_account_fuzzy_candidates.sql`
  - `dbt/models/intermediate/int_lead_account_resolved.sql`
- Updated:
  - `dbt/models/intermediate/int_lead_to_opportunity_base.sql`
  - `dbt/models/intermediate/_intermediate__models.yml`

## Why it was done
- Improve reconciliation coverage beyond strict exact-name matching.
- Preserve explainability by exposing `match_type`, `match_strategy`, and confidence diagnostics.
- Create a robust base for later anomaly and leakage analytics that require transparent mapping quality.

## Alternatives considered
- Full Levenshtein/Jaro-Winkler model in SQL: stronger string intelligence, engine-specific function risk across adapters.
- Python record-linkage service: richer matching, but introduces orchestration complexity and weaker dbt-native lineage.
- ML classification for matching at this stage: potentially highest recall, but premature without curated training labels.

## Command sequence used
```bash
# Added fuzzy and resolved reconciliation models in dbt intermediate layer
# Updated lead-to-opportunity stitching and model test definitions
```
