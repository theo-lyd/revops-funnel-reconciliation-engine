# Phase 4 BI Consumption Templates

## Purpose
Provide standardized consumption guidance so Metabase dashboards and Streamlit workflows use governed models and avoid semantic drift.

## Approved Gold models for BI
- `analytics_gold.fct_revenue_funnel`: row-level funnel fact model.
- `analytics_gold.bi_executive_funnel_overview`: executive aggregate model for dashboard cards and trends.
- `analytics_gold.dim_metric_contract`: governed semantic registry for metric definitions and ownership.

## Naming and usage conventions
- Use Gold models directly for BI; do not query Silver models in dashboards.
- Use `metric_month` for periodic trend visuals.
- Use `regional_office` as a default segmentation dimension.
- Round rate metrics at presentation layer, not in persistence models.

## Filter guardrails
- Always declare date window filters in dashboard queries.
- Treat `Unknown` regional values as valid category, not as null/invalid data.
- For win-rate and leakage-ratio cards, enforce denominator > 0 via source model logic.

## Query packs
- Metabase: `docs/reports/phase-4/query-packs/metabase-executive-funnel-view.sql`
- Streamlit + LLM: `docs/reports/phase-4/query-packs/streamlit-text-to-sql-safe-templates.sql`

## Stability controls
- `test_fct_revenue_funnel_leakage_ratio_bounds.sql`
- `test_bi_executive_funnel_win_rate_bounds.sql`
- Marts-level accepted-range tests in `_marts__models.yml`
