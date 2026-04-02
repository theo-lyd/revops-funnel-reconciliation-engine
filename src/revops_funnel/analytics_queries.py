"""Shared analytics query helpers for Phase 5."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass(frozen=True)
class QueryTemplate:
    name: str
    description: str
    base_sql: str
    date_column: str
    office_column: str
    chart_x: str
    chart_y: str
    chart_type: str


@dataclass(frozen=True)
class LlmResolution:
    template_key: str
    offices: list[str]
    explanation: str
    mode: str


REQUIRED_MONITORING_COLUMNS = {
    "metric_month",
    "regional_office",
    "total_opportunities",
    "won_opportunities",
    "lost_opportunities",
    "leakage_points",
    "avg_cycle_days",
    "avg_stage_age_days",
    "win_rate",
    "leakage_ratio",
}


def build_template_catalog(bi_schema: str) -> dict[str, QueryTemplate]:
    return {
        "Executive Monthly Overview": QueryTemplate(
            name="Executive Monthly Overview",
            description="Monthly opportunity volume, win rate, leakage ratio, and cycle time.",
            base_sql=(
                f"""
                select
                    metric_month,
                    regional_office,
                    total_opportunities,
                    won_opportunities,
                    lost_opportunities,
                    win_rate,
                    leakage_ratio,
                    avg_cycle_days,
                    avg_stage_age_days
                from {bi_schema}.bi_executive_funnel_overview
                """
            ),
            date_column="metric_month",
            office_column="regional_office",
            chart_x="metric_month",
            chart_y="win_rate",
            chart_type="line",
        ),
        "Public Sector Monthly Overview": QueryTemplate(
            name="Public Sector Monthly Overview",
            description="Public-sector monthly KPI overview for executive governance reporting.",
            base_sql=(
                f"""
                select
                    metric_month,
                    regional_office,
                    total_opportunities,
                    won_opportunities,
                    lost_opportunities,
                    win_rate,
                    leakage_ratio,
                    avg_cycle_days,
                    avg_stage_age_days
                from {bi_schema}.bi_public_sector_executive_overview
                """
            ),
            date_column="metric_month",
            office_column="regional_office",
            chart_x="metric_month",
            chart_y="win_rate",
            chart_type="line",
        ),
        "Sales Team Performance": QueryTemplate(
            name="Sales Team Performance",
            description="Sales team outcomes and value metrics by regional office.",
            base_sql=(
                f"""
                select
                    sales_agent,
                    manager,
                    regional_office,
                    opportunities_total,
                    opportunities_won,
                    opportunities_lost,
                    opportunities_open,
                    win_rate,
                    avg_close_value,
                    max_close_value
                from {bi_schema}.dim_sales_teams
                """
            ),
            date_column="",
            office_column="regional_office",
            chart_x="sales_agent",
            chart_y="win_rate",
            chart_type="bar",
        ),
        "Leakage Reason Analysis": QueryTemplate(
            name="Leakage Reason Analysis",
            description="Leakage by reason and office to identify friction points.",
            base_sql=(
                f"""
                select
                    leakage_reason,
                    regional_office,
                    count(*) as leakage_events,
                    avg(current_stage_age_days) as avg_stage_age_days
                from {bi_schema}.fct_revenue_funnel
                where is_leakage_point = true
                group by 1, 2
                """
            ),
            date_column="",
            office_column="regional_office",
            chart_x="leakage_reason",
            chart_y="leakage_events",
            chart_type="bar",
        ),
        "Pipeline Velocity": QueryTemplate(
            name="Pipeline Velocity",
            description="Stage aging buckets and cycle-time health across offices.",
            base_sql=(
                f"""
                select
                    stage_age_bucket,
                    regional_office,
                    count(*) as opportunities,
                    avg(total_cycle_days) as avg_total_cycle_days
                from {bi_schema}.fct_revenue_funnel
                group by 1, 2
                """
            ),
            date_column="",
            office_column="regional_office",
            chart_x="stage_age_bucket",
            chart_y="opportunities",
            chart_type="bar",
        ),
    }


def validate_columns(frame: pd.DataFrame, required_columns: set[str]) -> list[str]:
    return sorted(required_columns.difference(frame.columns))


def build_query_sql(
    template: QueryTemplate,
    office_filter: list[str],
    start: date,
    end: date,
    source: str,
    max_query_rows: int,
) -> str:
    sql = template.base_sql.strip()
    if office_filter and template.office_column:
        office_values = ", ".join("'" + value.replace("'", "''") + "'" for value in office_filter)
        if " where " in sql.lower():
            sql = f"{sql}\n and {template.office_column} in ({office_values})"
        else:
            sql = f"{sql}\n where {template.office_column} in ({office_values})"

    if template.date_column:
        if source == "DuckDB":
            predicate = f"{template.date_column}::date between date '{start}' and date '{end}'"
        else:
            predicate = (
                f"to_date({template.date_column}) between to_date('{start}') and to_date('{end}')"
            )

        if " where " in sql.lower():
            sql = f"{sql}\n and {predicate}"
        else:
            sql = f"{sql}\n where {predicate}"

    if "order by" not in sql.lower() and "group by" not in sql.lower():
        sql = f"{sql}\n order by 1"
    return f"{sql}\n limit {max_query_rows}"


def heuristic_resolution(prompt: str, offices: list[str]) -> LlmResolution:
    lowered = prompt.lower()
    if (
        "public sector" in lowered
        or "government" in lowered
        or "federal" in lowered
        or "municipal" in lowered
    ):
        template_key = "Public Sector Monthly Overview"
    elif "velocity" in lowered or "stage" in lowered:
        template_key = "Pipeline Velocity"
    elif "team" in lowered or "agent" in lowered or "manager" in lowered:
        template_key = "Sales Team Performance"
    elif "leak" in lowered or "loss" in lowered or "stalled" in lowered:
        template_key = "Leakage Reason Analysis"
    else:
        template_key = "Executive Monthly Overview"

    selected_offices = [office for office in offices if office.lower() in lowered]
    return LlmResolution(
        template_key=template_key,
        offices=selected_offices,
        explanation="Resolved using deterministic fallback keyword routing.",
        mode="heuristic",
    )


def resolve_prompt_to_template(
    prompt: str,
    templates: list[str],
    offices: list[str],
    api_key: str,
    model: str,
    max_tokens: int,
) -> LlmResolution:
    if not api_key:
        return heuristic_resolution(prompt, offices)

    try:
        from openai import OpenAI
    except Exception:
        return heuristic_resolution(prompt, offices)

    client = OpenAI(api_key=api_key)
    system_msg = (
        "You map analytics requests to a governed template list. "
        "Return JSON only with keys: template_key, offices, explanation. "
        "template_key must be one of the provided templates. "
        "offices must only contain items from provided offices."
    )
    user_msg = {"request": prompt, "templates": templates, "offices": offices}

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": json.dumps(user_msg)},
            ],
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
    except Exception:
        return heuristic_resolution(prompt, offices)

    raw_template = str(parsed.get("template_key", "")).strip()
    template_key = raw_template if raw_template in templates else "Executive Monthly Overview"
    raw_offices = parsed.get("offices", [])
    selected_offices = []
    if isinstance(raw_offices, list):
        selected_offices = [str(office) for office in raw_offices if str(office) in offices]

    explanation = str(parsed.get("explanation", "LLM intent routing completed.")).strip()
    if not explanation:
        explanation = "LLM intent routing completed."

    return LlmResolution(
        template_key=template_key,
        offices=selected_offices,
        explanation=explanation,
        mode="llm",
    )
