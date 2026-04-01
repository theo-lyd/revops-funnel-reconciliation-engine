# Phase 4 Semantic Metric Glossary

## Purpose
Provide a governed, non-ambiguous metric dictionary for technical and non-technical stakeholders. This glossary is the business contract for all downstream analytics surfaces.

## Governance rules
- Every metric must define business meaning and SQL-level formula.
- Every metric must define grain, owner, and intended consumption tools.
- Every metric must have contract metadata: `contract_version`, `effective_from`, `approval_status`, and `approved_by`.
- Any metric change requires changelog entry and cross-tool parity validation.

## Core metrics (Batch 4.2)

### leakage_ratio
- Business definition: Percentage of funnel records classified as leakage points.
- Formula: `sum(is_leakage_point::int) / count(*)`
- Grain: Lead-opportunity
- Owner: RevOps Analytics
- Primary source: `fct_revenue_funnel`

### win_rate
- Business definition: Percentage of opportunities that close as Won.
- Formula: `won_opportunities / total_opportunities`
- Grain: Lead-opportunity
- Owner: RevOps Analytics
- Primary source: `fct_revenue_funnel`

### conversion_ratio_lead_to_engaged
- Business definition: Percentage of leads that reached engagement stage.
- Formula: `engaged_leads / total_leads`
- Grain: Lead
- Owner: RevOps Analytics
- Primary source: `fct_revenue_funnel`

### avg_cycle_days
- Business definition: Average cycle duration from lead creation to close for complete journeys.
- Formula: `avg(total_cycle_days)`
- Grain: Lead-opportunity
- Owner: RevOps Analytics
- Primary source: `fct_revenue_funnel`

### cac_proxy
- Business definition: Marketing spend divided by engaged leads.
- Formula: `sum(marketing_spend) / engaged_leads`
- Grain: Campaign-period
- Owner: RevOps Finance
- Primary source: future marketing spend integration + funnel model
- Note: Proxy only until full spend model integration in later phase.

### ltv_proxy
- Business definition: Expected customer value based on won deals and repeat factor assumption.
- Formula: `avg(won_close_value) * expected_repeat_factor`
- Grain: Customer segment
- Owner: RevOps Finance
- Primary source: funnel model plus repeat-assumption table
- Note: Proxy only until customer lifecycle expansion in later phase.

## Cross-tool consistency contract
- Metabase and Streamlit must consume governed definitions from the same semantic contract source.
- Any dashboard-side custom metric that diverges from this glossary is out-of-policy.

## Change control
- Record updates in phase changelog and governance logs.
- Re-run `make quality-gate` after semantic contract changes.
- Follow governed SOP in:
	- `docs/reports/phase-4/semantic-metric-change-control.md`
