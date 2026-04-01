#!/usr/bin/env python3
"""Streamlit app for Phase 5 AI-driven analytics.

This app exposes a governed set of query templates over Gold-layer models.
It defaults to DuckDB for local use and supports Snowflake when optional
connector dependencies and credentials are available.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from revops_funnel.analytics_monitoring import (
    build_alert_message,
    detect_anomalies,
    summarize_findings,
    write_monitoring_report,
)
from revops_funnel.analytics_queries import (
    REQUIRED_MONITORING_COLUMNS,
    LlmResolution,
    QueryTemplate,
    build_query_sql,
    build_template_catalog,
    resolve_prompt_to_template,
    validate_columns,
)

load_dotenv()

BI_SCHEMA = os.getenv("BI_CONSUMPTION_SCHEMA", "analytics_gold")
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "./data/warehouse/revops.duckdb")
DASHBOARD_CACHE_SECONDS = int(os.getenv("DASHBOARD_CACHE_SECONDS", "300"))
MAX_QUERY_ROWS = int(os.getenv("STREAMLIT_MAX_QUERY_ROWS", "5000"))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "600"))
LLM_RATE_LIMIT_PER_MINUTE = int(os.getenv("LLM_RATE_LIMIT_PER_MINUTE", "10"))
LLM_AUDIT_LOG_PATH = os.getenv("LLM_AUDIT_LOG_PATH", "artifacts/ai/llm_query_audit.jsonl")
ANOMALY_DETECTION_SENSITIVITY = float(os.getenv("ANOMALY_DETECTION_SENSITIVITY", "2.0"))
ANOMALY_CHECK_CADENCE_HOURS = int(os.getenv("ANOMALY_CHECK_CADENCE_HOURS", "24"))
ALERT_EMAIL_RECIPIENTS = [
    recipient.strip()
    for recipient in os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(",")
    if recipient.strip()
]
MONITORING_DASHBOARD_REFRESH_INTERVAL = int(
    os.getenv("MONITORING_DASHBOARD_REFRESH_INTERVAL", "300")
)
ANOMALY_REPORT_PATH = os.getenv("ANOMALY_REPORT_PATH", "artifacts/monitoring/anomaly_report.json")

SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER", "")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD", "")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "REVOPS")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_GOLD_SCHEMA", "analytics_gold")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "TRANSFORMING")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "TRANSFORMER")


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


@st.cache_data(ttl=MONITORING_DASHBOARD_REFRESH_INTERVAL)
def _load_monitoring_frame(source: str) -> pd.DataFrame:
    sql = f"""
        select
            metric_month,
            regional_office,
            total_opportunities,
            won_opportunities,
            lost_opportunities,
            leakage_points,
            avg_cycle_days,
            avg_stage_age_days,
            win_rate,
            leakage_ratio
        from {BI_SCHEMA}.bi_executive_funnel_overview
        order by 1, 2
        """
    return _run_duckdb_query(sql) if source == "DuckDB" else _run_snowflake_query(sql)


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


def _render_monitoring_dashboard(source: str) -> None:
    st.subheader("Monitoring Dashboard")
    st.caption(
        "Phase 5.4: anomaly detection over the executive funnel overview with "
        "alert-ready summaries."
    )

    try:
        frame = _load_monitoring_frame(source)
    except Exception as exc:
        st.error(f"Unable to load monitoring data: {exc}")
        return

    missing_columns = validate_columns(frame, REQUIRED_MONITORING_COLUMNS)
    if missing_columns:
        st.error("Monitoring data is missing required columns: " + ", ".join(missing_columns))
        return

    findings = detect_anomalies(frame, ANOMALY_DETECTION_SENSITIVITY)
    alert_message = build_alert_message(findings)
    summary = summarize_findings(findings)

    write_monitoring_report(
        findings=findings,
        output_path=ANOMALY_REPORT_PATH,
        sensitivity=ANOMALY_DETECTION_SENSITIVITY,
        cadence_hours=ANOMALY_CHECK_CADENCE_HOURS,
        source=source,
        recipients=ALERT_EMAIL_RECIPIENTS,
    )

    metric_columns = st.columns(4)
    metric_columns[0].metric("Monitoring rows", f"{len(frame):,}")
    metric_columns[1].metric("Anomalies", f"{len(findings):,}")
    metric_columns[2].metric(
        "High priority",
        f"{sum(1 for finding in findings if finding.severity in {'high', 'critical'}):,}",
    )
    metric_columns[3].metric("Recipients", f"{len(ALERT_EMAIL_RECIPIENTS):,}")

    st.info(summary)
    st.code(alert_message, language="text")

    if frame.empty:
        st.warning("No monitoring data available.")
        return

    if not findings:
        st.success("No anomalies detected in the current monitoring window.")
    else:
        finding_frame = pd.DataFrame([finding.__dict__ for finding in findings])
        st.dataframe(finding_frame, use_container_width=True, hide_index=True)
        chart_frame = (
            finding_frame.groupby(["regional_office", "metric_name"])
            .size()
            .reset_index(name="anomaly_count")
        )
        chart = px.bar(
            chart_frame,
            x="regional_office",
            y="anomaly_count",
            color="metric_name",
            barmode="group",
            title="Anomalies by Office and Metric",
        )
        chart.update_layout(height=420, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(chart, use_container_width=True)

    with st.expander("Monitoring Data Preview", expanded=False):
        st.dataframe(frame.tail(12), use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="RevOps AI Analytics", page_icon="📈", layout="wide")
    st.title("RevOps Self-Service Analytics")
    st.caption("Phase 5.2: governed query templates over Gold-layer models")

    templates = build_template_catalog(BI_SCHEMA)

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
            resolution = resolve_prompt_to_template(
                prompt.strip(),
                list(templates.keys()),
                offices,
                os.getenv("OPENAI_API_KEY", ""),
                OPENAI_MODEL,
                LLM_MAX_TOKENS,
            )
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

    analytics_tab, monitoring_tab = st.tabs(["Analytics Explorer", "Monitoring Dashboard"])

    with analytics_tab:
        selected_template = templates[selected_template_key]
        st.subheader(selected_template.name)
        st.write(selected_template.description)

        if not run_query:
            st.info("Select controls and click Run Template to query the Gold layer.")
        else:
            sql = build_query_sql(
                selected_template,
                selected_offices,
                start_date,
                end_date,
                source,
                MAX_QUERY_ROWS,
            )

            with st.expander("SQL Preview", expanded=False):
                st.code(sql, language="sql")

            try:
                df = _run_duckdb_query(sql) if source == "DuckDB" else _run_snowflake_query(sql)
            except Exception as exc:
                st.error(f"Query failed: {exc}")
            else:
                if df.empty:
                    st.warning("Query succeeded but returned no rows for the selected filters.")
                else:
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

    with monitoring_tab:
        _render_monitoring_dashboard(source)


if __name__ == "__main__":
    main()
