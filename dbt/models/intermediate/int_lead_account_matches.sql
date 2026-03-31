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
)

select
    l.lead_id,
    l.company_name,
    l.utm_source,
    l.utm_campaign,
    l.created_at,
    a.account,
    a.sector,
    a.office_location,
    case
        when l.company_name_normalized = '' then 'unmatched'
        when l.company_name_normalized = a.account_name_normalized then 'exact_name_match'
        else 'unmatched'
    end as match_type,
    case
        when l.company_name_normalized = a.account_name_normalized then 1.0
        else 0.0
    end as match_confidence
from leads l
left join accounts a
    on l.company_name_normalized = a.account_name_normalized
