# Phase 3 Changelog

## 2026-04-01
- Fixed lint and type-check debt across ingestion, monitoring, quality, DAG, and core validator modules.
- Added `types-requests` dev dependency for stable mypy checks.
- Corrected local DuckDB profile path and aligned quality scripts to dbt output schemas.
- Updated stage-engagement dbt test rules to permit `Prospecting` opportunities without `engage_date`.
- Stabilized `dbt test` in quality gate by running with single-thread execution in this environment.
- Added `.gitignore` coverage for dbt-generated artifacts and local dbt profile files.
