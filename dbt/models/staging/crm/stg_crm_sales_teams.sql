select
    cast(sales_agent as varchar) as sales_agent,
    cast(manager as varchar) as manager,
    cast(regional_office as varchar) as regional_office
from {{ source('bronze_raw', 'sales_teams') }}
