#!/usr/bin/env python3
"""Streamlit app for Phase 5.2 self-service analytics.

This app exposes a governed set of query templates over Gold-layer models.
It defaults to DuckDB for local use and supports Snowflake when optional
connector dependencies and credentials are available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BI_SCHEMA = os.getenv("BI_CONSUMPTION_SCHEMA", "analytics_gold")
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "./data/warehouse/revops.duckdb")
DASHBOARD_CACHE_SECONDS = int(os.getenv("DASHBOARD_CACHE_SECONDS", "300"))
MAX_QUERY_ROWS = int(os.getenv("STREAMLIT_MAX_QUERY_ROWS", "5000"))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "600"))
LLM_RATE_LIMIT_PER_MINUTE = int(os.getenv("LLM_RATE_LIMIT_PER_MINUTE", "10"))
LLM_AUDIT_LOG_PATH = os.getenv("LLM_AUDIT_LOG_PATH", "artifacts/ai/llm_query_audit.jsonl")

SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER", "")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD", "")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "REVOPS")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_GOLD_SCHEMA", "analytics_gold")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "TRANSFORMING")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "TRANSFORMER")


@dataclass(frozen=True)
class LlmResolution:
    template_key: str
    offices: list[str]
    explanation: str
    mode: str


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


def _template_catalog() -> dict[str, QueryTemplate]:
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
                from {BI_SCHEMA}.bi_executive_funnel_overview
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
                from {BI_SCHEMA}.dim_sales_teams
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
                from {BI_SCHEMA}.fct_revenue_funnel
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
                from {BI_SCHEMA}.fct_revenue_funnel
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


def _check_rate_limit() -> bool:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=1)
    existing = cast(list[str], st.session_state.get("llm_request_times", []))
    in_window = [t for t in existing if datetime.fromisoformat(t) >= window_start]

    if len(in_window) >= LLM_RATE_LIMIT_PER_MINUTE:
        st.warning(
            "LLM rate limit reached for this session. "
            "Wait one minute before submitting another prompt."
        )
        st.session_state["llm_request_times"] = in_window
        return False

    in_window.append(now.isoformat())
    st.session_state["llm_request_times"] = in_window
    return True


def _append_audit_log(
    prompt: str,
    resolution: LlmResolution,
    source: str,
    start: date,
    end: date,
) -> None:
    path = Path(LLM_AUDIT_LOG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "prompt": prompt,
        "template_key": resolution.template_key,
        "offices": resolution.offices,
        "mode": resolution.mode,
        "date_start": str(start),
        "date_end": str(end),
        "explanation": resolution.explanation,
    }

    with path.open("a", encoding="utf-8") as file_obj:
        file_obj.write(json.dumps(event) + "\n")


def _heuristic_resolution(prompt: str, offices: list[str]) -> LlmResolution:
    lowered = prompt.lower()
    if "velocity" in lowered or "stage" in lowered:
        template_key = "Pipeline Velocity"
    elif "team" in lowered or "agent" in lowered or "manager" in lowered:
        template_key = "Sales Team Performance"
    elif "leak" in lowered or "loss" in lowered or "stalled" in lowered:
        template_key = "Leakage Reason Analysis"
    else:
        template_key = "Executive Monthly Overview"

    selected_offices = [o for o in offices if o.lower() in lowered]
    return LlmResolution(
        template_key=template_key,
        offices=selected_offices,
        explanation="Resolved using deterministic fallback keyword routing.",
        mode="heuristic",
    )


def _llm_resolution(prompt: str, templates: list[str], offices: list[str]) -> LlmResolution:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return _heuristic_resolution(prompt, offices)

    try:
        from openai import OpenAI
    except Exception:
        return _heuristic_resolution(prompt, offices)

    client = OpenAI(api_key=api_key)
    system_msg = (
        "You map analytics requests to a governed template list. "
        "Return JSON only with keys: template_key, offices, explanation. "
        "template_key must be one of the provided templates. "
        "offices must only contain items from provided offices."
    )
    user_msg = {
        "request": prompt,
        "templates": templates,
        "offices": offices,
    }

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0,
            max_tokens=LLM_MAX_TOKENS,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": json.dumps(user_msg)},
            ],
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
    except Exception:
        return _heuristic_resolution(prompt, offices)

    raw_template = str(parsed.get("template_key", "")).strip()
    template_key = raw_template if raw_template in templates else "Executive Monthly Overview"
    raw_offices = parsed.get("offices", [])
    selected_offices = []
    if isinstance(raw_offices, list):
        selected_offices = [str(o) for o in raw_offices if str(o) in offices]

    explanation = str(parsed.get("explanation", "LLM intent routing completed.")).strip()
    if not explanation:
        explanation = "LLM intent routing completed."

    return LlmResolution(
        template_key=template_key,
        offices=selected_offices,
        explanation=explanation,
        mode="llm",
    )


def _snowflake_available() -> bool:
    return bool(SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER and SNOWFLAKE_PASSWORD)


@st.cache_resource
def _duckdb_conn() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(DUCKDB_PATH, read_only=True)


@st.cache_resource
def _snowflake_conn() -> Any | None:
    if not _snowflake_available():
        return None

    try:
        import snowflake.connector  # type: ignore[import-not-found]
    except Exception:
        return None

    return snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        warehouse=SNOWFLAKE_WAREHOUSE,
        role=SNOWFLAKE_ROLE,
    )


def _apply_filters(template: QueryTemplate, office_filter: list[str]) -> str:
    sql = template.base_sql.strip()
    if office_filter and template.office_column:
        office_values = ", ".join("'" + x.replace("'", "''") + "'" for x in office_filter)
        if " where " in sql.lower():
            sql = f"{sql}\n and {template.office_column} in ({office_values})"
        else:
            sql = f"{sql}\n where {template.office_column} in ({office_values})"
    return sql


def _apply_date_filters(
    sql: str,
    template: QueryTemplate,
    start: date,
    end: date,
    source: str,
) -> str:
    if not template.date_column:
        return sql

    if source == "DuckDB":
        predicate = f"{template.date_column}::date between date '{start}' and date '{end}'"
    else:
        predicate = (
            f"to_date({template.date_column}) between to_date('{start}') and to_date('{end}')"
        )

    if " where " in sql.lower():
        return f"{sql}\n and {predicate}"
    return f"{sql}\n where {predicate}"


def _finalize_query(sql: str) -> str:
    if "order by" not in sql.lower() and "group by" not in sql.lower():
        sql = f"{sql}\n order by 1"
    return f"{sql}\n limit {MAX_QUERY_ROWS}"


@st.cache_data(ttl=DASHBOARD_CACHE_SECONDS)
def _run_duckdb_query(sql: str) -> pd.DataFrame:
    conn = _duckdb_conn()
    return conn.execute(sql).df()


@st.cache_data(ttl=DASHBOARD_CACHE_SECONDS)
def _run_snowflake_query(sql: str) -> pd.DataFrame:
    conn = _snowflake_conn()
    if conn is None:
        raise RuntimeError(
            "Snowflake connector unavailable. Install "
            "snowflake-connector-python and configure SNOWFLAKE_* env vars."
        )

    cur = conn.cursor()
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        return pd.DataFrame(rows, columns=columns)
    finally:
        cur.close()


def _distinct_offices(source: str) -> list[str]:
    sql = (
        "select distinct regional_office "
        f"from {BI_SCHEMA}.bi_executive_funnel_overview "
        "where regional_office is not null order by 1"
    )
    try:
        df = _run_duckdb_query(sql) if source == "DuckDB" else _run_snowflake_query(sql)
    except Exception:
        return []
    if "regional_office" not in df.columns:
        return []
    return [str(v) for v in df["regional_office"].dropna().tolist()]


def _render_chart(df: pd.DataFrame, template: QueryTemplate) -> None:
    if df.empty or template.chart_x not in df.columns or template.chart_y not in df.columns:
        st.info("No chart rendered for this selection.")
        return

    if template.chart_type == "line":
        fig = px.line(df, x=template.chart_x, y=template.chart_y, color="regional_office")
    else:
        fig = px.bar(df, x=template.chart_x, y=template.chart_y, color="regional_office")

    fig.update_layout(height=420, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)


def _render_kpis(df: pd.DataFrame, template_key: str) -> None:
    if df.empty:
        return

    if template_key == "Executive Monthly Overview":
        total = int(df["total_opportunities"].sum()) if "total_opportunities" in df.columns else 0
        avg_win = float(df["win_rate"].mean()) if "win_rate" in df.columns else 0.0
        avg_leak = float(df["leakage_ratio"].mean()) if "leakage_ratio" in df.columns else 0.0
        avg_cycle = float(df["avg_cycle_days"].mean()) if "avg_cycle_days" in df.columns else 0.0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Opportunities", f"{total:,}")
        c2.metric("Avg Win Rate", f"{avg_win:.2%}")
        c3.metric("Avg Leakage Ratio", f"{avg_leak:.2%}")
        c4.metric("Avg Cycle Days", f"{avg_cycle:.1f}")


def main() -> None:
    st.set_page_config(page_title="RevOps AI Analytics", page_icon="📈", layout="wide")
    st.title("RevOps Self-Service Analytics")
    st.caption("Phase 5.2: governed query templates over Gold-layer models")

    templates = _template_catalog()

    with st.sidebar:
        st.header("Query Controls")
        source_options = ["DuckDB"]
        if _snowflake_available():
            source_options.append("Snowflake")
        source = st.selectbox("Data Source", source_options)

        today = date.today()
        default_start = today - timedelta(days=90)
        selected_range = st.date_input(
            "Date Range",
            value=(default_start, today),
            help="Applied only to templates that include a date column.",
        )

        if isinstance(selected_range, tuple) and len(selected_range) == 2:
            start_date, end_date = selected_range
        else:
            start_date, end_date = default_start, today

        offices = _distinct_offices(source)
        selected_offices = st.multiselect("Regional Office", options=offices, default=[])

        selected_template_key = st.selectbox("Template", list(templates.keys()))
        st.markdown("---")
        st.subheader("AI Query Assistant")
        prompt = st.text_area(
            "Describe the question in natural language",
            placeholder="Example: Show leakage issues for London and New York in the last 90 days.",
            height=110,
        )
        use_ai = st.button("Generate with AI", use_container_width=True)
        run_query = st.button("Run Template", type="primary", use_container_width=True)

    if use_ai:
        if not prompt.strip():
            st.warning("Enter a natural-language request before using AI generation.")
        elif _check_rate_limit():
            resolution = _llm_resolution(prompt.strip(), list(templates.keys()), offices)
            selected_template_key = resolution.template_key
            selected_offices = resolution.offices
            st.info(
                f"AI mode: {resolution.mode}. "
                f"Template: {resolution.template_key}. "
                f"{resolution.explanation}"
            )
            _append_audit_log(
                prompt=prompt.strip(),
                resolution=resolution,
                source=source,
                start=start_date,
                end=end_date,
            )
            run_query = True

    selected_template = templates[selected_template_key]
    st.subheader(selected_template.name)
    st.write(selected_template.description)

    if not run_query:
        st.info("Select controls and click Run Template to query the Gold layer.")
        return

    sql = _apply_filters(selected_template, selected_offices)
    sql = _apply_date_filters(sql, selected_template, start_date, end_date, source)
    sql = _finalize_query(sql)

    with st.expander("SQL Preview", expanded=False):
        st.code(sql, language="sql")

    try:
        df = _run_duckdb_query(sql) if source == "DuckDB" else _run_snowflake_query(sql)
    except Exception as exc:
        st.error(f"Query failed: {exc}")
        return

    if df.empty:
        st.warning("Query succeeded but returned no rows for the selected filters.")
        return

    _render_kpis(df, selected_template_key)
    _render_chart(df, selected_template)

    st.dataframe(df, use_container_width=True, hide_index=True)
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Results (CSV)",
        data=csv_data,
        file_name="revops_query_result.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
