#!/usr/bin/env python3
"""Streamlit app for Phase 5.2 self-service analytics.

This app exposes a governed set of query templates over Gold-layer models.
It defaults to DuckDB for local use and supports Snowflake when optional
connector dependencies and credentials are available.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

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

SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER", "")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD", "")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "REVOPS")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_GOLD_SCHEMA", "analytics_gold")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "TRANSFORMING")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "TRANSFORMER")


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
        run_query = st.button("Run Template", type="primary", use_container_width=True)

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
