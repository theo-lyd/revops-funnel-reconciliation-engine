with base as (
    select *
    from {{ ref('int_funnel_velocity_metrics') }}
)

select
    lead_id,
    opportunity_id,
    account,
    sales_agent,
    manager,
    regional_office,
    sector,
    office_location,
    product,
    product_series,
    utm_source,
    utm_campaign,
    match_strategy,
    match_confidence,
    match_confidence_band,
    current_deal_stage as deal_stage,
    close_value,
    is_open,
    lead_created_at,
    engaged_at,
    closed_at,
    lead_to_engage_days,
    engage_to_close_days,
    total_cycle_days,
    current_stage_age_days,
    is_mid_funnel_stalled,
    was_slow_closed,
    case
        when is_mid_funnel_stalled then 'stalled_mid_funnel'
        when not is_open and deal_stage = 'Lost' and coalesce(close_value, 0) = 0 then 'closed_lost_no_value'
        when not is_open and deal_stage = 'Lost' then 'closed_lost_with_value'
        else 'healthy_or_won'
    end as leakage_reason,
    case
        when current_stage_age_days is null then 'not_applicable'
        when current_stage_age_days < 5 then '0_to_4_days'
        when current_stage_age_days < 10 then '5_to_9_days'
        when current_stage_age_days < 20 then '10_to_19_days'
        else '20_plus_days'
    end as stage_age_bucket,
    case
        when is_mid_funnel_stalled
            or (not is_open and deal_stage = 'Lost' and coalesce(close_value, 0) = 0)
            then true
        else false
    end as is_leakage_point
from base
