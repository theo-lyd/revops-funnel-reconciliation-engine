{% macro normalize_text(column_name) -%}
    lower(trim(regexp_replace({{ column_name }}, '[^a-zA-Z0-9 ]', '', 'g')))
{%- endmacro %}
