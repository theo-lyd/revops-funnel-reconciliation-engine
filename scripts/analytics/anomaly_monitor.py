#!/usr/bin/env python3
"""Batch 5.4 anomaly monitoring CLI.

Runs anomaly detection against the executive funnel overview and writes a JSON
report suitable for scheduling or alerting workflows.
"""

from __future__ import annotations

import argparse
import os

import duckdb
import pandas as pd

from revops_funnel.analytics_monitoring import (
    build_alert_message,
    detect_anomalies,
    summarize_findings,
    write_monitoring_report,
)
from revops_funnel.artifacts import write_text_artifact

BI_SCHEMA = os.getenv("BI_CONSUMPTION_SCHEMA", "analytics_gold")
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "./data/warehouse/revops.duckdb")
ANOMALY_DETECTION_SENSITIVITY = float(os.getenv("ANOMALY_DETECTION_SENSITIVITY", "2.0"))
ANOMALY_CHECK_CADENCE_HOURS = int(os.getenv("ANOMALY_CHECK_CADENCE_HOURS", "24"))
ALERT_EMAIL_RECIPIENTS = [
    recipient.strip()
    for recipient in os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(",")
    if recipient.strip()
]
ANOMALY_REPORT_PATH = os.getenv("ANOMALY_REPORT_PATH", "artifacts/monitoring/anomaly_report.json")
ANOMALY_MARKDOWN_PATH = os.getenv("ANOMALY_MARKDOWN_PATH", "artifacts/monitoring/anomaly_report.md")

SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER", "")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD", "")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "REVOPS")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_GOLD_SCHEMA", "analytics_gold")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "TRANSFORMING")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "TRANSFORMER")


def _snowflake_available() -> bool:
    return bool(SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER and SNOWFLAKE_PASSWORD)


def _duckdb_conn() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(DUCKDB_PATH, read_only=True)


def _snowflake_query(sql: str) -> pd.DataFrame:
    if not _snowflake_available():
        raise RuntimeError("Snowflake credentials are not configured.")

    try:
        import snowflake.connector  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("snowflake-connector-python is not available") from exc

    conn = snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        warehouse=SNOWFLAKE_WAREHOUSE,
        role=SNOWFLAKE_ROLE,
    )
    cur = conn.cursor()
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        return pd.DataFrame(rows, columns=columns)
    finally:
        cur.close()
        conn.close()


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
    if source == "snowflake":
        return _snowflake_query(sql)
    return _duckdb_conn().execute(sql).df()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Phase 5.4 anomaly report")
    parser.add_argument("--source", choices=["duckdb", "snowflake"], default="duckdb")
    parser.add_argument("--output-json", default=ANOMALY_REPORT_PATH)
    parser.add_argument("--output-markdown", default=ANOMALY_MARKDOWN_PATH)
    args = parser.parse_args()

    frame = _load_monitoring_frame(args.source)
    findings = detect_anomalies(frame, ANOMALY_DETECTION_SENSITIVITY)
    report = write_monitoring_report(
        findings=findings,
        output_path=args.output_json,
        sensitivity=ANOMALY_DETECTION_SENSITIVITY,
        cadence_hours=ANOMALY_CHECK_CADENCE_HOURS,
        source=args.source,
        recipients=ALERT_EMAIL_RECIPIENTS,
    )

    write_text_artifact(
        args.output_markdown,
        "# Phase 5.4 Monitoring Summary\n\n"
        f"- Generated: {report.generated_at_utc}\n"
        f"- Source: {args.source}\n"
        f"- Recipients: {', '.join(ALERT_EMAIL_RECIPIENTS) if ALERT_EMAIL_RECIPIENTS else 'none'}\n"
        f"- Anomaly count: {report.anomaly_count}\n"
        f"- Severe count: {report.severe_count}\n\n"
        f"{summarize_findings(findings)}\n\n"
        f"```text\n{build_alert_message(findings)}\n```\n",
    )

    print(summarize_findings(findings))
    print(f"Report written to {args.output_json}")
    print(f"Markdown summary written to {args.output_markdown}")

    if report.severe_count > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
