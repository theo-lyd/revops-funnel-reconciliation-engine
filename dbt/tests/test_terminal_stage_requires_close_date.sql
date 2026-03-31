select
    opportunity_id,
    deal_stage,
    close_date
from {{ ref('int_opportunity_enriched') }}
where deal_stage in ('Won', 'Lost')
  and close_date is null
