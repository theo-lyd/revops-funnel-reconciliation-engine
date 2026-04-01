select *
from {{ ref('bi_executive_funnel_overview') }}
where win_rate is null
   or win_rate < 0
   or win_rate > 1
