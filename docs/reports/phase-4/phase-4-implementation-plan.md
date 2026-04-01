# Phase 4 Implementation Plan: Semantic Layer and Gold Layer

## Phase objective
Define a unified business language and deliver BI-ready Gold marts with clear revenue leakage logic, while preserving cross-target compatibility (DuckDB local and Snowflake production).

## Why this phase matters
- Ensures every stakeholder sees consistent KPI definitions.
- Bridges technical reconciliation outputs into executive-facing analytics.
- Creates an auditable layer for defense with both technical and non-technical audiences.

## In-scope deliverables
1. Gold-layer marts for funnel analysis and sales-team performance.
2. Canonical metric definitions and data contracts.
3. Semantic governance documentation (metric glossary and ownership).
4. Snowflake rollout design from existing DuckDB-first workflow.

## Batch plan

### Batch 4.1: Gold marts foundation (current batch)
- Build `fct_revenue_funnel` and `dim_sales_teams`.
- Add model tests and accepted values contracts.
- Validate through dbt build and quality gate.

### Batch 4.2: Semantic metric contract
- Define metric dictionary for CAC, LTV, win rate, conversion ratio, leakage ratio.
- Add explicit grain, dimensions, filters, and owners.
- Add reconciliation between metric SQL and business definitions.

### Batch 4.3: BI readiness layer
- Add BI-safe model naming and documentation for dashboard consumption.
- Add ready-to-query examples for Metabase and Streamlit use cases.
- Add guardrail tests for metric stability and denominator checks.

### Batch 4.4: Snowflake production alignment
- Add production profile hardening and role model documentation.
- Define object naming strategy for bronze/silver/gold/observability schemas.
- Add deploy checklist for CI/CD and environment promotion.

## Snowflake integration strategy

### Design principles
- Local-first development on DuckDB for fast iteration.
- Production-grade execution on Snowflake with the same dbt DAG.
- Environment-specific configuration, not environment-specific logic.

### Execution approach
1. Keep dbt model SQL target-agnostic wherever possible.
2. Use profiles and environment variables for credentials and warehouse routing.
3. Validate parity between DuckDB and Snowflake outputs on sample slices.
4. Apply RBAC and least privilege in Snowflake for governed access.

### Risks and mitigations
- Risk: metric drift between environments.
  - Mitigation: parity tests on shared samples and metric-contract checks.
- Risk: production cost spikes.
  - Mitigation: warehouse sizing policy, auto-suspend, query tags.
- Risk: semantic ambiguity.
  - Mitigation: mandatory business glossary and metric ownership table.

## Acceptance criteria
- Gold marts build successfully and pass tests.
- Metrics have explicit definitions, grain, and ownership.
- Phase report and command/issue logs are updated.
- Commit and push completed.
- Stop-gate confirmation requested before Phase 5.
