with leads as (
    select
        lead_id,
        company_name,
        utm_source,
        utm_campaign,
        created_at,
        {{ normalize_text('coalesce(company_name, '''')') }} as company_name_normalized
    from {{ ref('stg_marketing_leads') }}
),
accounts as (
    select
        account,
        sector,
        office_location,
        {{ normalize_text('coalesce(account, '''')') }} as account_name_normalized
    from {{ ref('stg_crm_accounts') }}
),
candidates as (
    select
        l.lead_id,
        l.company_name,
        l.utm_source,
        l.utm_campaign,
        l.created_at,
        a.account,
        a.sector,
        a.office_location,
        l.company_name_normalized,
        a.account_name_normalized,
        case
            when l.company_name_normalized = '' then 0.0
            when l.company_name_normalized = a.account_name_normalized then 1.0
            when l.company_name_normalized like a.account_name_normalized || '%' then 0.92
            when a.account_name_normalized like l.company_name_normalized || '%' then 0.90
            when strpos(l.company_name_normalized, a.account_name_normalized) > 0 then 0.82
            when strpos(a.account_name_normalized, l.company_name_normalized) > 0 then 0.80
            else 0.0
        end as match_confidence,
        case
            when l.company_name_normalized = '' then 'unmatched'
            when l.company_name_normalized = a.account_name_normalized then 'exact_name_match'
            when l.company_name_normalized like a.account_name_normalized || '%' then 'lead_prefix_account_match'
            when a.account_name_normalized like l.company_name_normalized || '%' then 'account_prefix_lead_match'
            when strpos(l.company_name_normalized, a.account_name_normalized) > 0 then 'lead_contains_account_match'
            when strpos(a.account_name_normalized, l.company_name_normalized) > 0 then 'account_contains_lead_match'
            else 'unmatched'
        end as match_type
    from leads l
    cross join accounts a
    where l.company_name_normalized <> ''
),
ranked as (
    select
        *,
        row_number() over (
            partition by lead_id
            order by match_confidence desc, length(account_name_normalized) desc, account
        ) as match_rank
    from candidates
    where match_confidence >= 0.80
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
    match_confidence
from ranked
where match_rank = 1
