select
    cast(account as varchar) as account,
    lower(trim(cast(sector as varchar))) as sector,
    cast(year_established as integer) as year_established,
    cast(revenue as double) as revenue_musd,
    cast(employees as integer) as employees,
    cast(office_location as varchar) as office_location,
    nullif(trim(cast(subsidiary_of as varchar)), '') as subsidiary_of
from {{ source('bronze_raw', 'accounts') }}
