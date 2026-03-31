# Batch 2.5 Report: Hardening Data Model Correctness

## What was done
- Corrected stage-state derivation in velocity metrics to use latest chronological event instead of lexical stage max.
- Added unmatched-lead preservation in reconciliation outputs (`match_strategy = unmatched`).
- Updated lead-to-opportunity stitching to retain unmatched leads with nullable opportunities.
- Updated stage-event generation to include lead-created events for unmatched/unconverted leads.
- Optimized fuzzy matching with blocking keys (name prefix and location compatibility) to reduce cartesian blow-up.
- Updated intermediate model contracts to reflect unmatched-aware semantics.

## How it was done
- Updated models:
  - `dbt/models/intermediate/int_funnel_velocity_metrics.sql`
  - `dbt/models/intermediate/int_funnel_stage_events.sql`
  - `dbt/models/intermediate/int_lead_account_fuzzy_candidates.sql`
  - `dbt/models/intermediate/int_lead_account_resolved.sql`
  - `dbt/models/intermediate/int_lead_to_opportunity_base.sql`
  - `dbt/models/intermediate/_intermediate__models.yml`

## Why it was done
- Prevent stage misclassification and downstream KPI distortion.
- Preserve denominator integrity for leakage analysis by retaining unmatched leads.
- Improve scalability and reduce unnecessary fuzzy-candidate comparisons.
- Align test contracts with real-world matching outcomes.

## Alternatives considered
- Implement warehouse-native edit-distance scoring (Levenshtein/Jaro): stronger fuzzy quality but less cross-adapter portability.
- Move reconciliation to a Python linkage job: richer control at cost of dbt-native lineage transparency.
- Keep unmatched leads in a separate model only: cleaner conversion table but harder executive denominator reporting.

## Command sequence used
```bash
# Updated Silver reconciliation and velocity models to be unmatched-aware and chronologically correct
# Updated intermediate model contracts for revised semantics
```
