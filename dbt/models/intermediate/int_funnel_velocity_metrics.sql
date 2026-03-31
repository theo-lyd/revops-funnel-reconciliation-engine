with stage_events as (
    select *
    from {{ ref('int_funnel_stage_events') }}
),
latest_state as (
    select
        lead_id,
        opportunity_id,
        deal_stage,
        row_number() over (
            partition by lead_id, opportunity_id
            order by event_ts desc, stage_order desc
        ) as state_rank
    from stage_events
),
aggregated as (
    select
        se.lead_id,
        se.opportunity_id,
        se.account,
        se.sales_agent,
        se.manager,
        se.regional_office,
        se.sector,
        se.office_location,
        se.product,
        se.product_series,
        se.utm_source,
        se.utm_campaign,
        se.match_strategy,
        se.match_confidence,
        se.match_confidence_band,
        max(case when ls.state_rank = 1 then ls.deal_stage end) as current_deal_stage,
        max(se.close_value) as close_value,
        coalesce(bool_or(se.is_open), false) as is_open,
        min(case when se.stage_event = 'lead_created' then se.event_ts end) as lead_created_at,
        min(case when se.stage_event = 'opportunity_engaged' then se.event_ts end) as engaged_at,
        min(case when se.stage_event = 'opportunity_closed' then se.event_ts end) as closed_at,
        max(case
            when se.stage_event = 'opportunity_engaged' and se.prev_stage_event = 'lead_created'
                then se.days_since_prev_event
            else null
        end) as lead_to_engage_days,
        max(case
            when se.stage_event = 'opportunity_closed' and se.prev_stage_event = 'opportunity_engaged'
                then se.days_since_prev_event
            else null
        end) as engage_to_close_days
    from stage_events se
    left join latest_state ls
        on se.lead_id = ls.lead_id
        and se.opportunity_id is not distinct from ls.opportunity_id
    group by
        se.lead_id,
        se.opportunity_id,
        se.account,
        se.sales_agent,
        se.manager,
        se.regional_office,
        se.sector,
        se.office_location,
        se.product,
        se.product_series,
        se.utm_source,
        se.utm_campaign,
        se.match_strategy,
        se.match_confidence,
        se.match_confidence_band
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
        when is_open and engaged_at is not null then datediff('day', engaged_at, current_date)
        else null
    end as current_stage_age_days,
    case
        when is_open and engaged_at is not null and datediff('day', engaged_at, current_date) > 10 then true
        else false
    end as is_mid_funnel_stalled,
    case
        when not is_open and engage_to_close_days > 30 then true
        else false
    end as was_slow_closed
from aggregated
