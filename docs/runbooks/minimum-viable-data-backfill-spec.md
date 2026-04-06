# Minimum Viable Data Backfill Spec

## Purpose
Provide enough historical, high-quality funnel data in one iteration so:
- Streamlit Executive Brief shows actionable trend insights.
- Metabase executive charts and cards support stakeholder decisions.

Primary analytics surface in this project uses `analytics_gold.bi_executive_funnel_overview` sourced from DuckDB (`./data/warehouse/revops.duckdb`).

## Target Model And Required Columns
Backfill must produce valid monthly records in `analytics_gold.bi_executive_funnel_overview` with these columns:

- `metric_month` (DATE, month grain, first day of month)
- `regional_office` (STRING, non-null)
- `total_opportunities` (INTEGER, >= 0)
- `won_opportunities` (INTEGER, >= 0)
- `lost_opportunities` (INTEGER, >= 0)
- `leakage_points` (INTEGER, >= 0)
- `avg_cycle_days` (NUMERIC, >= 0)
- `avg_stage_age_days` (NUMERIC, >= 0)
- `win_rate` (NUMERIC, 0.0 to 1.0)
- `leakage_ratio` (NUMERIC, 0.0 to 1.0)

## Minimum Viable Coverage Targets
These are the minimum thresholds for decision-useful output.

- Time coverage: at least `6` consecutive months.
- Office coverage: at least `3` named offices each month.
- Volume coverage: at least `30` opportunities per office-month.
- Outcome coverage: each month must have both won and lost outcomes globally.
- Unknown office cap: `regional_office = 'Unknown'` must be <= `5%` of monthly opportunities.

## Monthly Row Targets
Given minimum coverage above:

- Minimum rows in executive overview:
  - `6 months * 3 offices = 18 rows` minimum.
- Recommended rows for stable comparisons:
  - `12 months * 4 offices = 48 rows`.

## Data Completeness Rules
Every `metric_month` should satisfy:

- `sum(total_opportunities) >= 90`
- `sum(won_opportunities) > 0`
- `sum(lost_opportunities) > 0`
- `avg(win_rate)` between `0.05` and `0.85` (sanity band)
- `avg(leakage_ratio)` between `0.05` and `0.80` (sanity band)

Office-level monthly rules:

- `total_opportunities >= 30`
- `avg_cycle_days` is non-zero for at least `80%` of office-month rows.
- `avg_stage_age_days` is non-zero for at least `80%` of office-month rows.

## Backfill Source Inputs
Populate/verify these raw/staging sources before dbt build:

- CRM opportunities and stage transitions (opportunity id, created/close dates, stage history)
- Lead engagement timestamps
- Account and office mapping dimensions (deterministic office assignment)
- Opportunity value and outcome status fields

## Execution Steps (One Iteration)
1. Load/append raw CRM and marketing source data for at least the last 6 months.
2. Ensure office mapping coverage so unknown attribution stays under 5%.
3. Run transformations and tests:
   - `make init-warehouse`
   - `cd dbt && dbt build --select state:modified+`
4. Validate quality gates:
   - `make quality-gate`
5. Verify executive model thresholds with checks below.

## Verification SQL (DuckDB)
Run against `analytics_gold.bi_executive_funnel_overview`.

```sql
-- Coverage summary
select
  count(distinct metric_month) as distinct_months,
  count(*) as rows_total,
  count(distinct regional_office) as distinct_offices
from analytics_gold.bi_executive_funnel_overview;
```

```sql
-- Monthly viability checks
select
  metric_month,
  sum(total_opportunities) as total_opps,
  sum(won_opportunities) as won_opps,
  sum(lost_opportunities) as lost_opps,
  sum(case when regional_office = 'Unknown' then total_opportunities else 0 end)
    / nullif(sum(total_opportunities), 0)::double as unknown_office_ratio
from analytics_gold.bi_executive_funnel_overview
group by 1
order by 1;
```

```sql
-- Office-month minimum volume
select
  metric_month,
  regional_office,
  total_opportunities
from analytics_gold.bi_executive_funnel_overview
where total_opportunities < 30
order by metric_month, regional_office;
```

## Acceptance Criteria
Backfill is accepted when all are true:

- `distinct_months >= 6`
- `rows_total >= 18`
- no month fails global outcome coverage
- unknown office ratio <= 5% for each month
- no office-month row has `total_opportunities < 30`
- Streamlit Executive Brief displays trend charts with at least 3 month points
- Metabase executive query pack returns non-trivial month-over-month trends

## BI Surface Configuration Notes
- Primary database to use now: DuckDB at `./data/warehouse/revops.duckdb`.
- Optional secondary for production parity: Snowflake.
- Metabase setup script: `scripts/analytics/setup_metabase.py`
- Metabase query pack: `docs/reports/phase-4/query-packs/metabase-executive-funnel-view.sql`
