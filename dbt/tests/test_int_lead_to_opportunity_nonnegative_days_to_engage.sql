select
    lead_id,
    opportunity_id,
    days_to_engage
from {{ ref('int_lead_to_opportunity_base') }}
where days_to_engage is not null
  and days_to_engage < 0
