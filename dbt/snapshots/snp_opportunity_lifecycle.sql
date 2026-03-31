{% snapshot snp_opportunity_lifecycle %}

{{
    config(
      target_schema='silver_history',
      unique_key='opportunity_id',
      strategy='check',
      check_cols=['deal_stage', 'close_date', 'close_value', 'is_open', 'sales_agent', 'account'],
      invalidate_hard_deletes=True
    )
}}

select
    opportunity_id,
    sales_agent,
    manager,
    regional_office,
    product,
    product_series,
    account,
    sector,
    office_location,
    deal_stage,
    deal_stage_rank,
    engage_date,
    close_date,
    close_value,
    is_open,
    cycle_days
from {{ ref('int_opportunity_enriched') }}

{% endsnapshot %}
