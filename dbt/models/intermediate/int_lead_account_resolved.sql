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
combined as (
    select * from exact_matches
    union all
    select * from fuzzy_matches
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
