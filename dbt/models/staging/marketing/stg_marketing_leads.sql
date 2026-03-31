select
    cast(lead_id as varchar) as lead_id,
    cast(company_name as varchar) as company_name,
    cast(email_hash as varchar) as email_hash,
    cast(utm_source as varchar) as utm_source,
    cast(utm_campaign as varchar) as utm_campaign,
    cast(country as varchar) as country,
    cast(created_at as timestamp) as created_at,
    cast(ingested_at as timestamp) as ingested_at
from {{ source('bronze_raw', 'marketing_leads') }}
