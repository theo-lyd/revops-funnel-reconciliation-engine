{% snapshot snp_lead_account_resolution %}

{{
    config(
      target_schema='silver_history',
      unique_key='lead_id',
      strategy='check',
      check_cols=['account', 'match_type', 'match_strategy', 'match_confidence', 'match_confidence_band'],
      invalidate_hard_deletes=True
    )
}}

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
    match_confidence_band
from {{ ref('int_lead_account_resolved') }}

{% endsnapshot %}
