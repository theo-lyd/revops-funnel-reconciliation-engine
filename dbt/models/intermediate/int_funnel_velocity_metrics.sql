with stage_events as (
    select *
    from {{ ref('int_funnel_stage_events') }}
),
aggregated as (
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
        max(deal_stage) as current_deal_stage,
        max(close_value) as close_value,
        bool_or(is_open) as is_open,
        min(case when stage_event = 'lead_created' then event_ts end) as lead_created_at,
        min(case when stage_event = 'opportunity_engaged' then event_ts end) as engaged_at,
        min(case when stage_event = 'opportunity_closed' then event_ts end) as closed_at,
        max(case
            when stage_event = 'opportunity_engaged' and prev_stage_event = 'lead_created'
                then days_since_prev_event
            else null
        end) as lead_to_engage_days,
        max(case
            when stage_event = 'opportunity_closed' and prev_stage_event = 'opportunity_engaged'
                then days_since_prev_event
            else null
        end) as engage_to_close_days
    from stage_events
    group by
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
        match_confidence_band
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
    current_deal_stage,
    close_value,
    is_open,
    lead_created_at,
    engaged_at,
    closed_at,
    lead_to_engage_days,
    engage_to_close_days,
    case
        when lead_to_engage_days is null or engage_to_close_days is null then null
        else lead_to_engage_days + engage_to_close_days
    end as total_cycle_days,
    case
        when is_open then datediff('day', engaged_at, current_date)
        else null
    end as current_stage_age_days,
    case
        when is_open and datediff('day', engaged_at, current_date) > 10 then true
        else false
    end as is_mid_funnel_stalled,
    case
        when not is_open and engage_to_close_days > 30 then true
        else false
    end as was_slow_closed
from aggregated
