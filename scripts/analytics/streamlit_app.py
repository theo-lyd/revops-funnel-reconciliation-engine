#!/usr/bin/env python3
"""Streamlit app for Phase 5 AI-driven analytics.

This app exposes a governed set of query templates over Gold-layer models.
It defaults to DuckDB for local use and supports Snowflake when optional
connector dependencies and credentials are available.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
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
from revops_funnel.snowflake_auth import (
    build_snowflake_connector_auth_kwargs,
    snowflake_auth_from_env,
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
METABASE_HOST = os.getenv("METABASE_HOST", "http://localhost")
METABASE_PORT = os.getenv("METABASE_PORT", "3000")


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
    config = snowflake_auth_from_env()
    return bool(config.account and config.user and config.is_auth_configured)


def _metabase_status() -> tuple[bool, str]:
    base = f"{METABASE_HOST}:{METABASE_PORT}".rstrip("/")
    health_url = f"{base}/api/health"
    try:
        with urllib.request.urlopen(health_url, timeout=1.5) as response:
            if response.status == 200:
                return True, base
    except (urllib.error.URLError, TimeoutError, ValueError):
        pass
    return False, base


@st.cache_resource
def _duckdb_conn() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(DUCKDB_PATH, read_only=True)


@st.cache_resource
def _snowflake_conn(cache_key: str) -> Any | None:
    config = snowflake_auth_from_env()
    if not (config.account and config.user and config.is_auth_configured):
        return None

    try:
        import snowflake.connector  # type: ignore[import-not-found]
    except Exception:
        return None

    connector_kwargs = build_snowflake_connector_auth_kwargs(config)
    return snowflake.connector.connect(
        account=config.account,
        user=config.user,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        warehouse=SNOWFLAKE_WAREHOUSE,
        role=SNOWFLAKE_ROLE,
        **connector_kwargs,
    )


def _snowflake_cache_key() -> str:
    config = snowflake_auth_from_env()
    key_material = [
        config.account,
        config.user,
        config.password,
        config.private_key_path,
        config.private_key_passphrase,
        SNOWFLAKE_DATABASE,
        SNOWFLAKE_SCHEMA,
        SNOWFLAKE_WAREHOUSE,
        SNOWFLAKE_ROLE,
    ]

    if config.private_key_path:
        try:
            stat = Path(config.private_key_path).stat()
            key_material.extend([str(stat.st_mtime_ns), str(stat.st_size)])
        except FileNotFoundError:
            key_material.append("missing-key-file")

    return "|".join(key_material)


@st.cache_data(ttl=DASHBOARD_CACHE_SECONDS)
def _run_duckdb_query(sql: str) -> pd.DataFrame:
    conn = _duckdb_conn()
    return conn.execute(sql).df()


@st.cache_data(ttl=DASHBOARD_CACHE_SECONDS)
def _run_snowflake_query(sql: str) -> pd.DataFrame:
    conn = _snowflake_conn(_snowflake_cache_key())
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


def _prepare_executive_frame(source: str) -> pd.DataFrame:
    frame = _load_monitoring_frame(source).copy()
    if frame.empty:
        return frame

    frame["metric_month"] = pd.to_datetime(frame["metric_month"], errors="coerce")
    frame = frame.dropna(subset=["metric_month"]).sort_values(["metric_month", "regional_office"])
    frame["regional_office"] = frame["regional_office"].fillna("Unknown")
    return frame


def _safe_mean(frame: pd.DataFrame, column: str) -> float:
    if column not in frame.columns or frame.empty:
        return 0.0
    series = pd.to_numeric(frame[column], errors="coerce")
    return float(series.mean()) if not series.isna().all() else 0.0


def _safe_sum(frame: pd.DataFrame, column: str) -> int:
    if column not in frame.columns or frame.empty:
        return 0
    series = pd.to_numeric(frame[column], errors="coerce")
    return int(series.sum()) if not series.isna().all() else 0


def _safe_mean_optional(frame: pd.DataFrame, column: str) -> float | None:
    if column not in frame.columns or frame.empty:
        return None
    series = pd.to_numeric(frame[column], errors="coerce")
    if series.isna().all():
        return None
    return float(series.mean())


def _render_executive_brief(source: str) -> None:
    st.subheader("Executive Brief")
    st.caption(
        "Answers core stakeholder questions: pipeline health, where leakage is rising, "
        "whether velocity is improving, and where intervention is needed now."
    )

    try:
        frame = _prepare_executive_frame(source)
    except Exception as exc:
        st.error(f"Unable to load executive metrics: {exc}")
        return

    if frame.empty:
        st.warning("No executive funnel data is available.")
        return

    month_count = int(frame["metric_month"].nunique())
    if month_count < 2:
        st.warning(
            "Limited trend history: only one metric month is available. "
            "KPI snapshots are shown, but month-over-month trend interpretation is limited."
        )

    latest_month = cast(pd.Timestamp, frame["metric_month"].max())
    previous_candidates = frame.loc[frame["metric_month"] < latest_month, "metric_month"]
    previous_month = cast(
        pd.Timestamp | None,
        previous_candidates.max() if not previous_candidates.empty else None,
    )

    latest = frame[frame["metric_month"] == latest_month]
    previous = (
        frame[frame["metric_month"] == previous_month]
        if previous_month is not None
        else pd.DataFrame()
    )

    current_total = _safe_sum(latest, "total_opportunities")
    previous_total = _safe_sum(previous, "total_opportunities")
    current_win = _safe_mean(latest, "win_rate")
    previous_win = _safe_mean(previous, "win_rate")
    current_leak = _safe_mean(latest, "leakage_ratio")
    previous_leak = _safe_mean(previous, "leakage_ratio")
    current_cycle = _safe_mean_optional(latest, "avg_cycle_days")
    previous_cycle = _safe_mean_optional(previous, "avg_cycle_days")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Total Opportunities",
        f"{current_total:,}",
        delta=f"{current_total - previous_total:+,}" if previous_month is not None else None,
    )
    col2.metric(
        "Win Rate",
        f"{current_win:.1%}",
        delta=(
            f"{(current_win - previous_win) * 100:+.1f} pp" if previous_month is not None else None
        ),
    )
    col3.metric(
        "Leakage Ratio",
        f"{current_leak:.1%}",
        delta=(
            f"{(current_leak - previous_leak) * 100:+.1f} pp"
            if previous_month is not None
            else None
        ),
        delta_color="inverse",
    )
    col4.metric(
        "Avg Cycle Days",
        f"{current_cycle:.1f}" if current_cycle is not None else "N/A",
        delta=(
            (
                f"{current_cycle - previous_cycle:+.1f} days"
                if current_cycle is not None and previous_cycle is not None
                else None
            )
            if previous_month is not None
            else None
        ),
        delta_color="inverse",
    )

    insight_lines = [
        f"Latest month: {latest_month.date()}",
        f"Pipeline volume is {current_total:,} opportunities.",
        f"Win rate is {current_win:.1%} and leakage is {current_leak:.1%}.",
    ]
    if month_count < 2:
        insight_lines.append(
            "Action: load at least 3 months of funnel history for directional trend insights."
        )
    st.info("\n".join(insight_lines))

    monthly_office = (
        frame.groupby(["metric_month", "regional_office"], as_index=False)
        .agg(
            total_opportunities=("total_opportunities", "sum"),
            won_opportunities=("won_opportunities", "sum"),
            lost_opportunities=("lost_opportunities", "sum"),
            win_rate=("win_rate", "mean"),
            leakage_ratio=("leakage_ratio", "mean"),
            avg_cycle_days=("avg_cycle_days", "mean"),
        )
        .sort_values(["metric_month", "regional_office"])
    )
    monthly_office["prior_leakage_ratio"] = monthly_office.groupby("regional_office")[
        "leakage_ratio"
    ].shift(1)
    monthly_office["leakage_delta_pp"] = (
        monthly_office["leakage_ratio"] - monthly_office["prior_leakage_ratio"]
    ) * 100

    latest_office = monthly_office[monthly_office["metric_month"] == latest_month].copy()
    latest_office["closed_outcomes"] = latest_office["won_opportunities"].fillna(0) + latest_office[
        "lost_opportunities"
    ].fillna(0)
    latest_office["action_status"] = "Monitor"
    latest_office.loc[
        (latest_office["closed_outcomes"] < 3),
        "action_status",
    ] = "Insufficient Data"
    intervention_condition = (latest_office["closed_outcomes"] >= 3) & (
        (latest_office["leakage_ratio"] >= 0.5)
        | (latest_office["win_rate"] <= 0.25)
        | (latest_office["avg_cycle_days"] >= 60)
    )
    latest_office.loc[intervention_condition, "action_status"] = "Intervene"

    if (latest_office["closed_outcomes"] < 3).all():
        st.info(
            "Intervention scoring is limited because there are not enough closed outcomes "
            "in the latest month. Load more historical wins/losses for reliable action flags."
        )

    q1, q2 = st.columns(2)
    with q1:
        st.markdown("**Where are we leaking pipeline most this month?**")
        leakage_view = latest_office[
            [
                "regional_office",
                "total_opportunities",
                "leakage_ratio",
                "leakage_delta_pp",
                "action_status",
            ]
        ].sort_values("leakage_ratio", ascending=False)
        st.dataframe(leakage_view.head(8), use_container_width=True, hide_index=True)

    with q2:
        st.markdown("**Which offices need immediate action?**")
        intervene = latest_office[latest_office["action_status"] == "Intervene"].copy()
        if intervene.empty:
            st.success("No office breaches intervention thresholds in the latest month.")
        else:
            st.error(
                "Intervention candidates: "
                + ", ".join(
                    intervene.sort_values("leakage_ratio", ascending=False)[
                        "regional_office"
                    ].tolist()
                )
            )
            st.dataframe(
                intervene[
                    [
                        "regional_office",
                        "win_rate",
                        "leakage_ratio",
                        "avg_cycle_days",
                        "total_opportunities",
                    ]
                ].sort_values("leakage_ratio", ascending=False),
                use_container_width=True,
                hide_index=True,
            )

    trend = (
        frame.groupby("metric_month", as_index=False)
        .agg(
            win_rate=("win_rate", "mean"),
            leakage_ratio=("leakage_ratio", "mean"),
            avg_cycle_days=("avg_cycle_days", "mean"),
            total_opportunities=("total_opportunities", "sum"),
        )
        .sort_values("metric_month")
    )

    if month_count >= 2:
        trend_fig = px.line(
            trend,
            x="metric_month",
            y=["win_rate", "leakage_ratio"],
            markers=True,
            title="Conversion vs Leakage Trend",
        )
        trend_fig.update_layout(
            height=360,
            margin=dict(l=20, r=20, t=45, b=20),
            legend_title_text="Metric",
        )
        trend_fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(trend_fig, use_container_width=True)

        cycle_fig = px.bar(
            trend,
            x="metric_month",
            y="avg_cycle_days",
            title="Sales Cycle Duration Trend",
        )
        cycle_fig.update_layout(height=320, margin=dict(l=20, r=20, t=45, b=20))
        st.plotly_chart(cycle_fig, use_container_width=True)
    else:
        st.dataframe(
            trend,
            use_container_width=True,
            hide_index=True,
        )


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
        metabase_up, metabase_url = _metabase_status()
        if metabase_up:
            st.success(f"Metabase online: {metabase_url}")
        else:
            st.warning("Metabase offline on configured host/port")

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

    executive_tab, analytics_tab, monitoring_tab = st.tabs(
        ["Executive Brief", "Analytics Explorer", "Monitoring Dashboard"]
    )

    with executive_tab:
        _render_executive_brief(source)

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
