with opportunities as (
    select *
    from {{ ref('int_opportunity_enriched') }}
),
aggregated as (
    select
        sales_agent,
        manager,
        regional_office,
        count(*) as opportunities_total,
        sum(case when deal_stage = 'Won' then 1 else 0 end) as opportunities_won,
        sum(case when deal_stage = 'Lost' then 1 else 0 end) as opportunities_lost,
        sum(case when deal_stage not in ('Won', 'Lost') then 1 else 0 end) as opportunities_open,
        avg(close_value) as avg_close_value,
        max(close_value) as max_close_value
    from opportunities
    group by sales_agent, manager, regional_office
)

select
    sales_agent,
    manager,
    regional_office,
    opportunities_total,
    opportunities_won,
    opportunities_lost,
    opportunities_open,
    case
        when opportunities_total = 0 then 0
        else cast(opportunities_won as double) / cast(opportunities_total as double)
    end as win_rate,
    avg_close_value,
    max_close_value
from aggregated
