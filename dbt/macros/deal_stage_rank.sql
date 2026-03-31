{% macro deal_stage_rank(stage_col) -%}
    case
        when {{ stage_col }} = 'Prospecting' then 1
        when {{ stage_col }} = 'Engaging' then 2
        when {{ stage_col }} = 'Won' then 3
        when {{ stage_col }} = 'Lost' then 3
        else 0
    end
{%- endmacro %}
