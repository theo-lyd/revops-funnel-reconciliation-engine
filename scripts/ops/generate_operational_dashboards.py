#!/usr/bin/env python3
"""Generate operational dashboards with SLO/SLI tracking and scaling recommendations."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from revops_funnel.artifacts import write_json_artifact
from revops_funnel.operational_dashboards import (
    MetricTrend,
    PerformanceMetric,
    SLIMetric,
    TrendAnalysis,
    analyze_metric_trend,
    evaluate_sli_status,
    generate_operational_dashboard,
)

DEFAULT_DASHBOARD_OUTPUT = os.getenv(
    "DASHBOARD_OUTPUT_PATH",
    "artifacts/monitoring/operational_dashboard.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--health-report",
        default="artifacts/monitoring/health_report.json",
        help="Path to health report artifact.",
    )
    parser.add_argument(
        "--cost-report",
        default="artifacts/monitoring/query_cost_attribution.json",
        help="Path to cost attribution artifact.",
    )
    parser.add_argument(
        "--performance-report",
        default="artifacts/performance/dbt_build_prod_report.json",
        help="Path to performance metrics artifact.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_DASHBOARD_OUTPUT,
        help="Output path for operational dashboard artifact.",
    )
    parser.add_argument(
        "--deployment-version",
        default=None,
        help="Current deployment version (e.g., git commit hash).",
    )
    parser.add_argument(
        "--strict-metrics",
        action="store_true",
        help="Fail when telemetry data is unavailable.",
    )
    return parser.parse_args()


def fetch_health_status() -> dict[str, Any] | None:
    """Fetch health report to extract freshness and job status."""
    health_path = Path("artifacts/monitoring/health_report.json")
    if not health_path.exists():
        return None

    try:
        data = json.loads(health_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        return None
    except (OSError, json.JSONDecodeError):
        return None


def fetch_cost_metrics() -> list[dict[str, Any]] | None:
    """Fetch cost attribution to extract cost-per-record metrics."""
    cost_path = Path("artifacts/monitoring/query_cost_attribution.json")
    if not cost_path.exists():
        return None

    try:
        data = json.loads(cost_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            attributions = data.get("attributions", [])
            if isinstance(attributions, list):
                return attributions
            return None
        if isinstance(data, list):
            return data
        return None
    except (json.JSONDecodeError, OSError):
        return None


def fetch_performance_metrics() -> dict[str, Any] | None:
    """Fetch performance metrics (latency, throughput)."""
    perf_path = Path("artifacts/performance/dbt_build_prod_report.json")
    if not perf_path.exists():
        return None

    try:
        data = json.loads(perf_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        return None
    except (json.JSONDecodeError, OSError):
        return None


def extract_latency_metrics(
    performance_data: dict | None,
) -> list[PerformanceMetric]:
    """Extract latency metrics from performance report."""
    if not performance_data:
        return []

    metrics: list[PerformanceMetric] = []
    now = datetime.utcnow().isoformat()

    # Extract from dbt execution stats if available
    if "stats" in performance_data:
        execution_time = performance_data["stats"].get("execution_time")
        if execution_time:
            metrics.append(
                PerformanceMetric(
                    timestamp=now,
                    value=float(execution_time),
                    unit="seconds",
                    metric_type="latency",
                )
            )

    # Historical metrics if available
    if "timestamped_latency" in performance_data:
        for entry in performance_data["timestamped_latency"]:
            metrics.append(
                PerformanceMetric(
                    timestamp=entry.get("timestamp", now),
                    value=float(entry.get("value", 0)),
                    unit="seconds",
                    metric_type="latency",
                )
            )

    return metrics


def extract_cost_metrics(cost_data: list[dict] | None) -> list[PerformanceMetric]:
    """Extract cost-per-record metrics."""
    if not cost_data:
        return []

    metrics: list[PerformanceMetric] = []
    now = datetime.utcnow().isoformat()

    for entry in cost_data:
        cost_per_record = entry.get("cost_per_record")
        if cost_per_record:
            metrics.append(
                PerformanceMetric(
                    timestamp=entry.get("timestamp", now),
                    value=float(cost_per_record),
                    unit="USD/record",
                    metric_type="cost_per_record",
                )
            )

    return metrics


def generate_sli_metrics(
    health_status: dict | None,
    latency_metrics: list[PerformanceMetric],
    cost_metrics: list[PerformanceMetric],
) -> list[SLIMetric]:
    """Generate SLI metrics from telemetry."""
    sli_metrics: list[SLIMetric] = []

    # Data Freshness SLI
    freshness_slo = 24.0  # hours
    if health_status and "sli_metrics" in health_status:
        for metric in health_status.get("sli_metrics", []):
            if metric.get("name") == "freshness":
                freshness_hours = float(metric.get("current_value", 0))
                sli_metrics.append(
                    SLIMetric(
                        name="data_freshness",
                        current_value=freshness_hours,
                        slo_threshold=freshness_slo,
                        unit="hours",
                        status=evaluate_sli_status(freshness_hours, freshness_slo),
                        trend=MetricTrend.STABLE,
                        last_updated=datetime.utcnow().isoformat(),
                    )
                )

    # Transformation Latency SLI
    latency_slo = 120.0  # minutes
    if latency_metrics:
        latest_latency = latency_metrics[-1]
        sli_metrics.append(
            SLIMetric(
                name="transformation_latency",
                current_value=latest_latency.value / 60,  # Convert to minutes
                slo_threshold=latency_slo,
                unit="minutes",
                status=evaluate_sli_status(latest_latency.value / 60, latency_slo),
                trend=MetricTrend.STABLE,
                last_updated=latest_latency.timestamp,
            )
        )

    # Cost per Record SLI
    cost_per_record_slo = 0.001  # $0.001 per record
    if cost_metrics:
        latest_cost = cost_metrics[-1]
        sli_metrics.append(
            SLIMetric(
                name="cost_per_record",
                current_value=latest_cost.value,
                slo_threshold=cost_per_record_slo,
                unit="USD/record",
                status=evaluate_sli_status(latest_cost.value, cost_per_record_slo),
                trend=MetricTrend.STABLE,
                last_updated=latest_cost.timestamp,
            )
        )

    return sli_metrics


def main() -> int:
    """Generate operational dashboard."""
    args = parse_args()

    # Fetch telemetry artifacts
    health_status = fetch_health_status()
    cost_data = fetch_cost_metrics()
    performance_data = fetch_performance_metrics()

    # Check if we have any data
    has_data = any([health_status, cost_data, performance_data])

    if not has_data:
        if args.strict_metrics:
            print("Error: No telemetry data available (--strict-metrics enabled)")
            return 1

        # Local-safe mode: emit skipped dashboard
        skipped_dashboard = {
            "status": "skipped",
            "reason": "No telemetry artifacts found",
            "timestamp": datetime.utcnow().isoformat(),
        }
        write_json_artifact(args.output, skipped_dashboard)
        print("Dashboard skipped (no telemetry data)")
        return 0

    # Extract metrics
    latency_metrics = extract_latency_metrics(performance_data)
    cost_metrics = extract_cost_metrics(cost_data)

    # Generate SLI metrics
    sli_metrics = generate_sli_metrics(health_status, latency_metrics, cost_metrics)

    # Analyze trends
    trend_analyses: dict[str, TrendAnalysis] = {}
    if latency_metrics:
        trend_analyses["latency"] = analyze_metric_trend("latency", latency_metrics)
    if cost_metrics:
        trend_analyses["cost_per_record"] = analyze_metric_trend("cost_per_record", cost_metrics)

    # Extract cost and performance values for correlation
    cost_values = [m.value for m in cost_metrics] if cost_metrics else None
    perf_values = [m.value / 60 for m in latency_metrics] if latency_metrics else None

    # Generate dashboard
    dashboard = generate_operational_dashboard(
        sli_metrics=sli_metrics,
        trend_analyses=trend_analyses,
        cost_values=cost_values,
        performance_values=perf_values,
        deployment_version=args.deployment_version,
    )

    # Write artifact
    artifact_path = write_json_artifact(args.output, dashboard.to_dict())
    print(f"✓ Dashboard generated: {artifact_path}")
    print(f"  Status: {dashboard.operational_status}")
    print(f"  SLI Metrics: {len(dashboard.sli_metrics)}")
    print(f"  Trends: {len(dashboard.trend_analyses)}")
    print(f"  Scaling Recommendations: {len(dashboard.scaling_recommendations)}")

    return 0


if __name__ == "__main__":
    exit(main())
