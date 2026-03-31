select
    lead_id,
    opportunity_id,
    lead_to_engage_days,
    engage_to_close_days,
    total_cycle_days
from {{ ref('int_funnel_velocity_metrics') }}
where (lead_to_engage_days is not null and lead_to_engage_days < 0)
   or (engage_to_close_days is not null and engage_to_close_days < 0)
   or (total_cycle_days is not null and total_cycle_days < 0)
