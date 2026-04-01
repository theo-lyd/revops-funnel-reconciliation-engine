-- Streamlit + LLM safe SQL templates
-- Purpose: Provide approved query skeletons for NL-to-SQL workflows.

-- TEMPLATE 1: Identify regions with prolonged stage age
select
    regional_office,
    metric_month,
    avg_stage_age_days,
    leakage_ratio
from analytics_gold.bi_executive_funnel_overview
where avg_stage_age_days > 10
  and metric_month >= date_trunc('month', current_date) - interval '6 months'
order by avg_stage_age_days desc;

-- TEMPLATE 2: Top leakage regions by month
select
    metric_month,
    regional_office,
    leakage_points,
    total_opportunities,
    leakage_ratio
from analytics_gold.bi_executive_funnel_overview
where metric_month >= date_trunc('month', current_date) - interval '6 months'
order by metric_month desc, leakage_ratio desc;

-- TEMPLATE 3: Win-rate performance by region
select
    metric_month,
    regional_office,
    won_opportunities,
    total_opportunities,
    win_rate
from analytics_gold.bi_executive_funnel_overview
where metric_month >= date_trunc('month', current_date) - interval '6 months'
order by metric_month desc, win_rate desc;
