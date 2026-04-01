with ratios as (
    select
        coalesce(regional_office, 'Unknown') as regional_office,
        cast(sum(case when is_leakage_point then 1 else 0 end) as double) / nullif(count(*), 0) as leakage_ratio
    from {{ ref('fct_revenue_funnel') }}
    group by 1
)

select *
from ratios
where leakage_ratio is null
   or leakage_ratio < 0
   or leakage_ratio > 1
