select
    opportunity_id,
    close_value
from {{ ref('int_opportunity_enriched') }}
where close_value is not null
  and (close_value < 0 or close_value > 1000000)
