select
    cast(product as varchar) as product,
    cast(series as varchar) as series,
    cast(sales_price as double) as sales_price
from {{ source('bronze_raw', 'products') }}
