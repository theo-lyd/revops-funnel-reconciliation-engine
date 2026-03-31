select
    opportunity_id,
    engage_date,
    close_date
from {{ ref('int_opportunity_enriched') }}
where close_date is not null
  and engage_date is not null
  and close_date < engage_date
