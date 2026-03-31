with opportunities as (
    select *
    from {{ ref('stg_crm_sales_pipeline') }}
),
accounts as (
    select *
    from {{ ref('stg_crm_accounts') }}
),
products as (
    select *
    from {{ ref('stg_crm_products') }}
),
sales_teams as (
    select *
    from {{ ref('stg_crm_sales_teams') }}
)

select
    o.opportunity_id,
    o.sales_agent,
    st.manager,
    st.regional_office,
    o.product,
    p.series as product_series,
    p.sales_price,
    o.account,
    a.sector,
    a.office_location,
    a.employees,
    o.deal_stage,
    {{ deal_stage_rank('o.deal_stage') }} as deal_stage_rank,
    o.engage_date,
    o.close_date,
    o.close_value,
    case when o.deal_stage in ('Won', 'Lost') then false else true end as is_open,
    case
        when o.close_date is null then null
        else datediff('day', o.engage_date, o.close_date)
    end as cycle_days
from opportunities o
left join accounts a on o.account = a.account
left join products p on o.product = p.product
left join sales_teams st on o.sales_agent = st.sales_agent
