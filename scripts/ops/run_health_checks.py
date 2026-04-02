#!/usr/bin/env python3
"""Run production health checks and liveness monitoring."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from revops_funnel.artifacts import write_json_artifact
from revops_funnel.health_monitoring import (
    HealthCheck,
    HealthStatus,
    HealthThresholds,
    check_data_freshness,
    check_job_duration,
    generate_health_report,
)

DEFAULT_FRESHNESS_HOURS = 24.0
DEFAULT_JOB_DURATION_MINUTES = 120.0
DEFAULT_OUTPUT = os.getenv(
    "HEALTH_REPORT_PATH",
    "artifacts/monitoring/health_report.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-freshness-hours",
        type=float,
        default=float(os.getenv("HEALTH_MAX_FRESHNESS_HOURS", str(DEFAULT_FRESHNESS_HOURS))),
        help="Maximum allowed data freshness age in hours.",
    )
    parser.add_argument(
        "--max-job-duration-minutes",
        type=float,
        default=float(
            os.getenv("HEALTH_MAX_JOB_DURATION_MINUTES", str(DEFAULT_JOB_DURATION_MINUTES))
        ),
        help="Maximum allowed transformation job duration in minutes.",
    )
    parser.add_argument(
        "--strict-metrics",
        action="store_true",
        help="Fail when telemetry data is unavailable in strict contexts.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Output path for health report artifact.",
    )
    return parser.parse_args()


def fetch_table_freshness(table_name: str) -> tuple[str, str | None]:
    """Fetch last updated timestamp for a table.

    In local-safe mode, returns skipped status if telemetry unavailable.
    Integrations would fetch from dbt artifacts or telemetry DBs.
    """
    dbt_manifest_path = Path("dbt/target/manifest.json")
    if not dbt_manifest_path.exists():
        return "skipped", None

    try:
        manifest = json.loads(dbt_manifest_path.read_text(encoding="utf-8"))
        for node_id, node in manifest.get("nodes", {}).items():
            if table_name in node_id:
                if "relations" in node:
                    created_at = node.get("created_at")
                    if created_at:
                        return "ok", created_at
    except (json.JSONDecodeError, KeyError, AttributeError):
        pass

    return "skipped", None


def fetch_job_metrics(job_name: str) -> tuple[str, float | None]:
    """Fetch last job duration for a named transformation job.

    Returns (status, duration_minutes) where status is ok/skipped/error.
    Integrations would fetch from Airflow, dbt Cloud, or release artifacts.
    """
    perf_artifact_path = Path("artifacts/performance/dbt_build_prod_report.json")
    if not perf_artifact_path.exists():
        return "skipped", None

    try:
        report = json.loads(perf_artifact_path.read_text(encoding="utf-8"))
        if "duration_seconds" in report:
            duration_minutes = float(report["duration_seconds"]) / 60.0
            return "ok", duration_minutes
    except (json.JSONDecodeError, KeyError, ValueError):
        pass

    return "skipped", None


def main() -> int:
    args = parse_args()

    thresholds = HealthThresholds(
        max_freshness_hours=max(0.5, args.max_freshness_hours),
        max_job_duration_minutes=max(1.0, args.max_job_duration_minutes),
    )

    checks: list[HealthCheck] = []

    freshness_status, freshness_ts = fetch_table_freshness("int_funnel_stage_events")
    if freshness_status == "ok" or not args.strict_metrics:
        check_freshness = check_data_freshness("int_funnel_stage_events", freshness_ts, thresholds)
        checks.append(check_freshness)

    job_status, job_duration = fetch_job_metrics("dbt-build-prod")
    if job_status == "ok" or not args.strict_metrics:
        check_job = check_job_duration("dbt-build-prod", job_duration, thresholds)
        checks.append(check_job)

    if not checks:
        if args.strict_metrics:
            payload = {
                "status": "error",
                "detail": "no health metrics available and strict mode enabled",
                "strict_metrics": True,
            }
            write_json_artifact(args.output, payload)
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 1

        checks = [
            HealthCheck(
                check_name="generic_liveness",
                status=HealthStatus.SKIPPED,
                detail="no health telemetry available",
                evaluated_at_utc="",
            )
        ]

    report = generate_health_report(checks)
    overall = str(report.get("overall_status", ""))

    payload = {
        "status": "ok" if overall != "unhealthy" else "error",
        "strict_metrics": bool(args.strict_metrics),
        "report": report,
    }

    code = 1 if overall == "unhealthy" else 0
    write_json_artifact(args.output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
