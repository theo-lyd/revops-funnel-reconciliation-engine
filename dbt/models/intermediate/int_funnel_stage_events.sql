with stitched as (
    select
        lto.lead_id,
        lto.opportunity_id,
        lto.account,
        lto.utm_source,
        lto.utm_campaign,
        lto.match_strategy,
        lto.match_confidence,
        lto.match_confidence_band,
        cast(lto.lead_created_at as timestamp) as lead_created_at,
        cast(lto.engage_date as timestamp) as engage_date,
        cast(lto.close_date as timestamp) as close_date,
        lto.deal_stage,
        lto.close_value,
        opp.sales_agent,
        opp.manager,
        opp.regional_office,
        opp.sector,
        opp.office_location,
        opp.product,
        opp.product_series,
        opp.is_open
    from {{ ref('int_lead_to_opportunity_base') }} lto
    inner join {{ ref('int_opportunity_enriched') }} opp
        on lto.opportunity_id = opp.opportunity_id
),
events as (
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
        deal_stage,
        close_value,
        is_open,
        1 as stage_order,
        'lead_created' as stage_event,
        lead_created_at as event_ts
    from stitched

    union all

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
        deal_stage,
        close_value,
        is_open,
        2 as stage_order,
        'opportunity_engaged' as stage_event,
        engage_date as event_ts
    from stitched

    union all

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
        deal_stage,
        close_value,
        is_open,
        3 as stage_order,
        'opportunity_closed' as stage_event,
        close_date as event_ts
    from stitched
    where close_date is not null
),
windowed as (
    select
        *,
        lag(event_ts) over (
            partition by lead_id, opportunity_id
            order by stage_order, event_ts
        ) as prev_event_ts,
        lag(stage_event) over (
            partition by lead_id, opportunity_id
            order by stage_order, event_ts
        ) as prev_stage_event,
        lead(event_ts) over (
            partition by lead_id, opportunity_id
            order by stage_order, event_ts
        ) as next_event_ts,
        lead(stage_event) over (
            partition by lead_id, opportunity_id
            order by stage_order, event_ts
        ) as next_stage_event
    from events
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
    deal_stage,
    close_value,
    is_open,
    stage_order,
    stage_event,
    event_ts,
    prev_stage_event,
    prev_event_ts,
    next_stage_event,
    next_event_ts,
    case
        when prev_event_ts is null then null
        else datediff('day', prev_event_ts, event_ts)
    end as days_since_prev_event,
    case
        when next_event_ts is null then null
        else datediff('day', event_ts, next_event_ts)
    end as days_to_next_event
from windowed
