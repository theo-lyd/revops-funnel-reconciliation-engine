with lead_account as (
    select *
    from {{ ref('int_lead_account_matches') }}
    where match_type = 'exact_name_match'
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
        o.opportunity_id,
        o.engage_date,
        o.close_date,
        o.deal_stage,
        o.close_value,
        datediff('day', la.created_at, o.engage_date) as days_to_engage,
        row_number() over (
            partition by la.lead_id
            order by abs(datediff('day', la.created_at, o.engage_date)), o.engage_date
        ) as candidate_rank
    from lead_account la
    inner join opportunities o
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
    opportunity_id,
    engage_date,
    close_date,
    deal_stage,
    close_value,
    days_to_engage
from candidates
where candidate_rank = 1
