select
    'leakage_ratio' as metric_name,
    'Leakage points divided by total funnel records.' as business_definition,
    'sum(case when is_leakage_point then 1 else 0 end) / count(*)' as calculation_sql,
    'lead_opportunity' as grain,
    'daily' as time_grain,
    'fct_revenue_funnel' as source_model,
    'revops_analytics_owner' as owner_role,
    'metabase,streamlit' as consumer_tools,
    'Exclude null lifecycle rows if business requests strict active-funnel view.' as caveats

union all

select
    'win_rate' as metric_name,
    'Won opportunities divided by total opportunities.' as business_definition,
    'sum(case when deal_stage = ''Won'' then 1 else 0 end) / count(*)' as calculation_sql,
    'lead_opportunity' as grain,
    'daily' as time_grain,
    'fct_revenue_funnel' as source_model,
    'revops_analytics_owner' as owner_role,
    'metabase,streamlit' as consumer_tools,
    'Use same denominator policy across all dashboards.' as caveats

union all

select
    'conversion_ratio_lead_to_engaged' as metric_name,
    'Share of leads that reached engagement stage.' as business_definition,
    'sum(case when engaged_at is not null then 1 else 0 end) / count(*)' as calculation_sql,
    'lead' as grain,
    'daily' as time_grain,
    'fct_revenue_funnel' as source_model,
    'revops_analytics_owner' as owner_role,
    'metabase,streamlit' as consumer_tools,
    'Requires lead-level de-duplication if source grain changes.' as caveats

union all

select
    'avg_cycle_days' as metric_name,
    'Average total cycle duration from lead creation to close when available.' as business_definition,
    'avg(total_cycle_days)' as calculation_sql,
    'lead_opportunity' as grain,
    'monthly' as time_grain,
    'fct_revenue_funnel' as source_model,
    'revops_analytics_owner' as owner_role,
    'metabase,streamlit' as consumer_tools,
    'Null cycle rows should be excluded from aggregate averages.' as caveats

union all

select
    'cac_proxy' as metric_name,
    'Proxy CAC equal to campaign spend divided by engaged leads.' as business_definition,
    'sum(marketing_spend) / nullif(sum(case when engaged_at is not null then 1 else 0 end), 0)' as calculation_sql,
    'campaign_period' as grain,
    'monthly' as time_grain,
    'semantic_join_marketing_spend_to_funnel' as source_model,
    'revops_finance_owner' as owner_role,
    'metabase,streamlit' as consumer_tools,
    'Requires external spend source; use only after spend model is integrated.' as caveats

union all

select
    'ltv_proxy' as metric_name,
    'Proxy LTV equal to average won deal value multiplied by expected repeat factor.' as business_definition,
    'avg(case when deal_stage = ''Won'' then close_value end) * expected_repeat_factor' as calculation_sql,
    'customer_segment' as grain,
    'quarterly' as time_grain,
    'fct_revenue_funnel_plus_repeat_assumption' as source_model,
    'revops_finance_owner' as owner_role,
    'metabase,streamlit' as consumer_tools,
    'Requires explicit repeat-factor governance and periodic recalibration.' as caveats
