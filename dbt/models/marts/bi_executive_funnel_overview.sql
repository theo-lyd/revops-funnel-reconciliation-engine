with base as (
    select *
    from {{ ref('fct_revenue_funnel') }}
)

select
    coalesce(regional_office, 'Unknown') as regional_office,
    date_trunc('month', coalesce(engaged_at, lead_created_at)) as metric_month,
    count(*) as total_opportunities,
    sum(case when deal_stage = 'Won' then 1 else 0 end) as won_opportunities,
    sum(case when deal_stage = 'Lost' then 1 else 0 end) as lost_opportunities,
    sum(case when is_leakage_point then 1 else 0 end) as leakage_points,
    avg(total_cycle_days) as avg_cycle_days,
    avg(current_stage_age_days) as avg_stage_age_days,
    cast(sum(case when deal_stage = 'Won' then 1 else 0 end) as double) / nullif(count(*), 0) as win_rate,
    cast(sum(case when is_leakage_point then 1 else 0 end) as double) / nullif(count(*), 0) as leakage_ratio
from base
group by 1, 2
