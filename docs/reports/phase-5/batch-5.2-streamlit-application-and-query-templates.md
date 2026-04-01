# Batch 5.2: Streamlit Application and Query Templates

## Objective
Deliver an interactive self-service analytics application with governed query templates over Gold-layer models, including caching and optional Snowflake execution path.

## Deliverables
1. Streamlit app implementation.
2. Governed query template catalog for executive and operational analytics.
3. Query controls for date range and regional office filters.
4. CSV export and chart visualization for stakeholder consumption.

## Files Added
- `scripts/analytics/streamlit_app.py`

## Implementation Summary
- Implemented `scripts/analytics/streamlit_app.py` with:
  - Template catalog for:
    - Executive Monthly Overview
    - Sales Team Performance
    - Leakage Reason Analysis
    - Pipeline Velocity
  - Gold-layer data model usage:
    - `analytics_gold.bi_executive_funnel_overview`
    - `analytics_gold.dim_sales_teams`
    - `analytics_gold.fct_revenue_funnel`
  - Streamlit controls:
    - Data source selector (`DuckDB` by default, optional `Snowflake`)
    - Date range picker for date-aware templates
    - Regional office multiselect
  - Performance and reliability:
    - `st.cache_resource` for DB connections
    - `st.cache_data` for query results (TTL from `DASHBOARD_CACHE_SECONDS`)
    - Row limit guard rail using `STREAMLIT_MAX_QUERY_ROWS` (default 5000)
  - Output UX:
    - KPI cards for executive template
    - Plotly line/bar chart rendering
    - Data table and CSV download

## Security and Governance Controls
- Query access is restricted to approved templates (no arbitrary SQL textbox).
- Office filters are sanitized before interpolation.
- Snowflake path is optional and only enabled when credentials exist.
- If Snowflake connector dependency is missing, the app fails gracefully with actionable guidance.

## Make Target
- Existing target `make streamlit-dev` now launches a functional app:
  - `streamlit run scripts/analytics/streamlit_app.py --server.port $${STREAMLIT_SERVER_PORT:-8501}`

## Validation Outcomes
- `make lint` passed after Streamlit app integration.
- `make test` passed.
- App entrypoint and imports validated by static checks.

## Notes
- Snowflake execution in-app requires optional dependency `snowflake-connector-python` in the runtime where Streamlit is launched.
- Batch 5.3 will add LLM orchestration, guard rails, and query audit logging over this template engine.
