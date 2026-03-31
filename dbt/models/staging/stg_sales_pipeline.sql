select
    cast(opportunity_id as varchar) as opportunity_id,
    cast(sales_agent as varchar) as sales_agent,
    cast(product as varchar) as product,
    cast(account as varchar) as account,
    cast(deal_stage as varchar) as deal_stage,
    cast(engage_date as date) as engage_date,
    cast(close_date as date) as close_date,
    cast(close_value as double) as close_value
from {{ source('bronze_raw', 'sales_pipeline') }}
