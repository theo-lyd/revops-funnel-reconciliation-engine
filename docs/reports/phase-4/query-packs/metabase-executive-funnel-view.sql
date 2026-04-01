-- Metabase query pack: Executive Funnel View
-- Purpose: Standard KPI query for leadership dashboard cards and trend charts.

with base as (
    select *
    from analytics_gold.bi_executive_funnel_overview
)

select
    metric_month,
    regional_office,
    total_opportunities,
    won_opportunities,
    lost_opportunities,
    leakage_points,
    round(win_rate, 4) as win_rate,
    round(leakage_ratio, 4) as leakage_ratio,
    round(avg_cycle_days, 2) as avg_cycle_days,
    round(avg_stage_age_days, 2) as avg_stage_age_days
from base
where metric_month >= date_trunc('month', current_date) - interval '12 months'
order by metric_month desc, regional_office;
