with exact_matches as (
    select
        lead_id,
        company_name,
        utm_source,
        utm_campaign,
        created_at,
        account,
        sector,
        office_location,
        match_type,
        match_confidence,
        'deterministic' as match_strategy
    from {{ ref('int_lead_account_matches') }}
    where match_type = 'exact_name_match'
),
fuzzy_matches as (
    select
        lead_id,
        company_name,
        utm_source,
        utm_campaign,
        created_at,
        account,
        sector,
        office_location,
        match_type,
        match_confidence,
        'fuzzy' as match_strategy
    from {{ ref('int_lead_account_fuzzy_candidates') }}
),
unmatched_leads as (
    select
        l.lead_id,
        l.company_name,
        l.utm_source,
        l.utm_campaign,
        l.created_at,
        cast(null as varchar) as account,
        cast(null as varchar) as sector,
        cast(null as varchar) as office_location,
        'unmatched' as match_type,
        0.0 as match_confidence,
        'unmatched' as match_strategy
    from {{ ref('stg_marketing_leads') }} l
    left join (
        select lead_id from exact_matches
        union all
        select lead_id from fuzzy_matches
    ) m on l.lead_id = m.lead_id
    where m.lead_id is null
),
combined as (
    select * from exact_matches
    union all
    select * from fuzzy_matches
    union all
    select * from unmatched_leads
),
ranked as (
    select
        *,
        row_number() over (
            partition by lead_id
            order by
                case when match_strategy = 'deterministic' then 1 else 2 end,
                match_confidence desc,
                account
        ) as selection_rank
    from combined
)

select
    lead_id,
    company_name,
    utm_source,
    utm_campaign,
    created_at,
    account,
    sector,
    office_location,
    match_type,
    match_strategy,
    match_confidence,
    case
        when match_confidence >= 0.95 then 'high'
        when match_confidence >= 0.85 then 'medium'
        else 'low'
    end as match_confidence_band
from ranked
where selection_rank = 1
