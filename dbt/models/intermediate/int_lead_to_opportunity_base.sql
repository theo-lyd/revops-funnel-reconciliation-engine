with lead_account as (
    select *
    from {{ ref('int_lead_account_resolved') }}
),
opportunities as (
    select *
    from {{ ref('int_opportunity_enriched') }}
),
candidates as (
    select
        la.lead_id,
        la.created_at as lead_created_at,
        la.utm_source,
        la.utm_campaign,
        la.account,
        la.match_type,
        la.match_strategy,
        la.match_confidence,
        la.match_confidence_band,
        o.opportunity_id,
        o.engage_date,
        o.close_date,
        o.deal_stage,
        o.close_value,
        datediff('day', la.created_at, o.engage_date) as days_to_engage,
        row_number() over (
            partition by la.lead_id
            order by
                case when o.opportunity_id is null then 1 else 0 end,
                abs(datediff('day', la.created_at, o.engage_date)),
                o.engage_date
        ) as candidate_rank
    from lead_account la
    left join opportunities o
        on la.account = o.account
        and o.engage_date >= cast(la.created_at as date)
        and o.engage_date <= cast(la.created_at as date) + interval 120 day
)

select
    lead_id,
    lead_created_at,
    utm_source,
    utm_campaign,
    account,
    match_type,
    match_strategy,
    match_confidence,
    match_confidence_band,
    opportunity_id,
    engage_date,
    close_date,
    deal_stage,
    close_value,
    days_to_engage
from candidates
where candidate_rank = 1
