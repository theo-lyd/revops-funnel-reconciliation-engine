"""Query-cost observability and warehouse spend-attribution helpers."""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum


class TransformationLayer(str, Enum):
    """dbt transformation layer classification."""

    STAGING = "staging"
    INTERMEDIATE = "intermediate"
    MARTS = "marts"
    UTILS = "utils"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class QueryCostEntry:
    query_id: str
    query_tag: str
    warehouse_name: str
    user_name: str
    elapsed_seconds: float
    bytes_scanned: int
    credits_used: float
    started_at_utc: str
    dbt_model_path: str = ""
    transformation_layer: str = ""


def normalize_query_tag(raw_tag: str) -> str:
    normalized = raw_tag.strip()
    return normalized if normalized else "un-tagged"


def _classify_transformation_layer(dbt_model_path: str, query_tag: str) -> str:
    """Classify query into transformation layer (staging, intermediate, marts, utils, unknown)."""
    path = (dbt_model_path or "").strip().lower()
    tag = (query_tag or "").strip().lower()

    # Try to extract layer from dbt_model_path (e.g., "models/staging/crm/..." -> "staging")
    if "staging" in path or "stg_" in tag:
        return TransformationLayer.STAGING.value
    if "intermediate" in path or "int_" in tag:
        return TransformationLayer.INTERMEDIATE.value
    if "marts" in path or "fct_" in tag or "dim_" in tag:
        return TransformationLayer.MARTS.value
    if "utils" in path or "macro" in path:
        return TransformationLayer.UTILS.value

    return TransformationLayer.UNKNOWN.value


def aggregate_query_cost_attribution(entries: list[QueryCostEntry]) -> dict[str, object]:
    total_queries = len(entries)
    total_elapsed_seconds = sum(max(0.0, entry.elapsed_seconds) for entry in entries)
    total_bytes_scanned = sum(max(0, int(entry.bytes_scanned)) for entry in entries)
    total_credits_used = sum(max(0.0, float(entry.credits_used)) for entry in entries)

    by_tag: dict[str, dict[str, float | int | str]] = {}
    by_warehouse: dict[str, dict[str, float | int | str]] = {}
    by_layer: dict[str, dict[str, float | int | str]] = {}

    for entry in entries:
        tag_key = normalize_query_tag(entry.query_tag)
        warehouse_key = entry.warehouse_name.strip() or "unknown"
        layer_key = _classify_transformation_layer(entry.dbt_model_path, entry.query_tag)

        tag_record = by_tag.setdefault(
            tag_key,
            {
                "query_tag": tag_key,
                "query_count": 0,
                "elapsed_seconds": 0.0,
                "bytes_scanned": 0,
                "credits_used": 0.0,
            },
        )
        tag_record["query_count"] = int(tag_record["query_count"]) + 1
        tag_record["elapsed_seconds"] = float(tag_record["elapsed_seconds"]) + max(
            0.0, entry.elapsed_seconds
        )
        tag_record["bytes_scanned"] = int(tag_record["bytes_scanned"]) + max(
            0, int(entry.bytes_scanned)
        )
        tag_record["credits_used"] = float(tag_record["credits_used"]) + max(
            0.0, float(entry.credits_used)
        )

        warehouse_record = by_warehouse.setdefault(
            warehouse_key,
            {
                "warehouse_name": warehouse_key,
                "query_count": 0,
                "elapsed_seconds": 0.0,
                "bytes_scanned": 0,
                "credits_used": 0.0,
            },
        )
        warehouse_record["query_count"] = int(warehouse_record["query_count"]) + 1
        warehouse_record["elapsed_seconds"] = float(warehouse_record["elapsed_seconds"]) + max(
            0.0, entry.elapsed_seconds
        )
        warehouse_record["bytes_scanned"] = int(warehouse_record["bytes_scanned"]) + max(
            0, int(entry.bytes_scanned)
        )
        warehouse_record["credits_used"] = float(warehouse_record["credits_used"]) + max(
            0.0, float(entry.credits_used)
        )

        layer_record = by_layer.setdefault(
            layer_key,
            {
                "layer": layer_key,
                "query_count": 0,
                "elapsed_seconds": 0.0,
                "bytes_scanned": 0,
                "credits_used": 0.0,
            },
        )
        layer_record["query_count"] = int(layer_record["query_count"]) + 1
        layer_record["elapsed_seconds"] = float(layer_record["elapsed_seconds"]) + max(
            0.0, entry.elapsed_seconds
        )
        layer_record["bytes_scanned"] = int(layer_record["bytes_scanned"]) + max(
            0, int(entry.bytes_scanned)
        )
        layer_record["credits_used"] = float(layer_record["credits_used"]) + max(
            0.0, float(entry.credits_used)
        )

    tag_rows = sorted(
        by_tag.values(),
        key=lambda row: float(row["credits_used"]),
        reverse=True,
    )
    warehouse_rows = sorted(
        by_warehouse.values(),
        key=lambda row: float(row["credits_used"]),
        reverse=True,
    )
    layer_rows = sorted(
        by_layer.values(),
        key=lambda row: float(row["credits_used"]),
        reverse=True,
    )

    for row in tag_rows:
        credits = float(row["credits_used"])
        query_count = int(row["query_count"])
        row["credits_share"] = (credits / total_credits_used) if total_credits_used > 0 else 0.0
        row["avg_credits_per_query"] = (credits / query_count) if query_count > 0 else 0.0

    for row in warehouse_rows:
        credits = float(row["credits_used"])
        query_count = int(row["query_count"])
        row["credits_share"] = (credits / total_credits_used) if total_credits_used > 0 else 0.0
        row["avg_credits_per_query"] = (credits / query_count) if query_count > 0 else 0.0

    for row in layer_rows:
        credits = float(row["credits_used"])
        query_count = int(row["query_count"])
        row["credits_share"] = (credits / total_credits_used) if total_credits_used > 0 else 0.0
        row["avg_credits_per_query"] = (credits / query_count) if query_count > 0 else 0.0

    top_queries = sorted(
        entries,
        key=lambda entry: (float(entry.credits_used), float(entry.elapsed_seconds)),
        reverse=True,
    )[:20]

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "query_count": total_queries,
            "elapsed_seconds": total_elapsed_seconds,
            "bytes_scanned": total_bytes_scanned,
            "credits_used": total_credits_used,
        },
        "attribution_by_query_tag": tag_rows,
        "attribution_by_warehouse": warehouse_rows,
        "attribution_by_transformation_layer": layer_rows,
        "top_expensive_queries": [asdict(item) for item in top_queries],
    }


@dataclass(frozen=True)
class CostRegressionThresholds:
    max_credits_regression_pct: float
    max_elapsed_regression_pct: float


@dataclass(frozen=True)
class CostForecastConfig:
    team_owner: str | None = None
    budget_allocated: float | None = None
    window_days: int = 30
    trend_threshold_pct: float = 20.0


def _safe_float(value: object) -> float:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def _percent_change(current: float, baseline: float) -> float | None:
    if baseline <= 0:
        return None
    return ((current - baseline) / baseline) * 100.0


def _compute_z_score(value: float, mean: float, stddev: float) -> float:
    """Compute z-score: (value - mean) / stddev."""
    if stddev <= 0:
        return 0.0
    return (value - mean) / stddev


def _compute_iqr_bounds(values: list[float], k: float = 1.5) -> tuple[float, float]:
    """Compute IQR bounds (Q1 - k*IQR, Q3 + k*IQR)."""
    if len(values) < 4:
        return (min(values) if values else 0.0, max(values) if values else 0.0)

    sorted_vals = sorted(values)
    q1 = statistics.quantiles(sorted_vals, n=4)[0]
    q3 = statistics.quantiles(sorted_vals, n=4)[2]
    iqr = q3 - q1

    lower_bound = q1 - k * iqr
    upper_bound = q3 + k * iqr
    return (lower_bound, upper_bound)


def _detect_statistical_anomaly(
    current_value: float,
    historical_values: list[float],
    z_threshold: float = 3.0,
) -> dict[str, object]:
    """Detect anomalies using z-score and IQR methods."""
    if not historical_values:
        return {
            "status": "insufficient-history",
            "z_score": 0.0,
            "z_threshold": z_threshold,
            "percentile_rank": 0.0,
        }

    mean_val = statistics.mean(historical_values)
    try:
        stddev_val = statistics.stdev(historical_values) if len(historical_values) > 1 else 0.0
    except statistics.StatisticsError:
        stddev_val = 0.0

    z_score = _compute_z_score(current_value, mean_val, stddev_val)

    lower_bound, upper_bound = _compute_iqr_bounds(historical_values)
    iqr_anomaly = current_value < lower_bound or current_value > upper_bound

    z_anomaly = abs(z_score) > z_threshold

    all_values = sorted(historical_values + [current_value])
    percentile_rank = (all_values.index(current_value) / len(all_values)) * 100.0

    status = "ok"
    if z_anomaly or iqr_anomaly:
        status = "anomaly"

    return {
        "status": status,
        "z_score": round(z_score, 2),
        "z_threshold": z_threshold,
        "z_anomaly": z_anomaly,
        "iqr_anomaly": iqr_anomaly,
        "historical_mean": round(mean_val, 2),
        "historical_stddev": round(stddev_val, 2),
        "iqr_lower_bound": round(lower_bound, 2),
        "iqr_upper_bound": round(upper_bound, 2),
        "percentile_rank": round(percentile_rank, 1),
    }


def _compute_trend_line(
    daily_costs: list[float],
) -> tuple[float, float]:
    """Compute linear trend (slope, intercept) for daily costs using least squares."""
    if len(daily_costs) < 2:
        return (0.0, daily_costs[0] if daily_costs else 0.0)

    n = len(daily_costs)
    x_values = list(range(n))
    x_mean = statistics.mean(x_values)
    y_mean = statistics.mean(daily_costs)

    numerator = sum((x_values[i] - x_mean) * (daily_costs[i] - y_mean) for i in range(n))
    denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return (0.0, y_mean)

    slope = numerator / denominator
    intercept = y_mean - slope * x_mean

    return (slope, intercept)


def _forecast_end_of_period_cost(
    current_monthly_burn: float,
    daily_costs: list[float],
    days_elapsed: int,
    days_in_period: int = 30,
) -> tuple[float, float]:
    """Forecast end-of-period cost using trend line."""
    if days_elapsed < 1 or len(daily_costs) < 2:
        # Simple extrapolation
        daily_rate = current_monthly_burn / days_elapsed if days_elapsed > 0 else 0.0
        remaining_days = days_in_period - days_elapsed
        forecast = current_monthly_burn + (daily_rate * remaining_days)
        return (forecast, current_monthly_burn)

    slope, intercept = _compute_trend_line(daily_costs)
    remaining_days = days_in_period - days_elapsed
    daily_rate = slope if slope > 0 else (current_monthly_burn / days_elapsed)

    forecast = current_monthly_burn + (daily_rate * remaining_days)
    confidence = min(0.95, 0.7 + (days_elapsed / days_in_period) * 0.25)

    return (forecast, confidence)


def _bytes_per_result_row(bytes_scanned: int, estimated_result_rows: int = 1) -> float:
    """Compute bytes-scanned-per-result-row efficiency metric."""
    if estimated_result_rows <= 0:
        return float(bytes_scanned)
    return bytes_scanned / estimated_result_rows


def _extract_join_count(query_text: str) -> int:
    """Estimate join count from query text (simple heuristic)."""
    query_lower = query_text.lower()
    join_keywords = ["inner join", "left join", "right join", "full join", "cross join"]
    return sum(query_lower.count(kw) for kw in join_keywords)


def _emit_optimization_hints(
    query_id: str,
    bytes_scanned: int,
    result_rows: int,
    peer_median_bytes_per_row: float,
) -> list[dict[str, object]]:
    """Generate optimization hints based on query metrics vs. peer statistics."""
    hints: list[dict[str, object]] = []

    if result_rows <= 0:
        return hints

    bytes_per_row = bytes_scanned / result_rows
    deviation_sigma = (bytes_per_row - peer_median_bytes_per_row) / max(
        peer_median_bytes_per_row * 0.2, 1.0
    )

    if deviation_sigma > 3.0:
        hints.append(
            {
                "hint": "Full table scan detected; apply early filters to reduce scanned bytes",
                "confidence": "high",
                "estimated_savings_pct": min(70, (deviation_sigma - 2.0) * 10),
                "effort_hours": 1,
            }
        )

    return hints


def _compute_seasonal_factor(week_of_year: int) -> float:
    """Compute seasonal adjustment factor (placeholder for now)."""
    # Simplified seasonal model (peak in Q4, trough in Jan)
    if 42 <= week_of_year <= 52:  # Q4 (Oct-Dec)
        return 1.25
    if 1 <= week_of_year <= 4:  # Early Jan
        return 0.85
    return 1.0


def _normalize_environment_cost(
    staging_cost: float,
    environment: str,
    staging_to_prod_multiplier: float = 5.0,
) -> float:
    """Normalize cost across environments using multiplier (e.g., staging→prod)."""
    if environment in ("staging", "ci", "dev"):
        return staging_cost * staging_to_prod_multiplier
    return staging_cost


def _estimate_prod_cost_from_staging(
    staging_monthly_cost: float,
    staging_trend_7_day: float,
    staging_to_prod_multiplier: float = 5.0,
) -> tuple[float, float, float]:
    """Estimate production cost from staging with confidence."""
    estimated_prod_today = staging_monthly_cost * staging_to_prod_multiplier
    prod_state_cost = staging_monthly_cost + staging_trend_7_day
    estimated_prod_steady_state = prod_state_cost * staging_to_prod_multiplier
    confidence = min(
        0.95,
        0.75 + (abs(staging_trend_7_day) / max(staging_monthly_cost, 1.0)) * 0.1,
    )

    return (estimated_prod_today, estimated_prod_steady_state, confidence)


def _query_tag_totals(report: dict[str, object]) -> dict[str, dict[str, float]]:
    rows = report.get("attribution_by_query_tag")
    if not isinstance(rows, list):
        return {}

    totals: dict[str, dict[str, float]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        raw_tag = str(row.get("query_tag", ""))
        tag = normalize_query_tag(raw_tag)
        totals[tag] = {
            "credits_used": _safe_float(row.get("credits_used")),
            "elapsed_seconds": _safe_float(row.get("elapsed_seconds")),
            "query_count": _safe_float(row.get("query_count")),
        }
    return totals


def detect_query_cost_regressions(
    current_report: dict[str, object],
    baseline_report: dict[str, object],
    thresholds: CostRegressionThresholds,
) -> dict[str, object]:
    current_totals = current_report.get("totals")
    baseline_totals = baseline_report.get("totals")

    if not isinstance(current_totals, dict) or not isinstance(baseline_totals, dict):
        return {
            "status": "error",
            "detail": "current and baseline reports must include totals",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "thresholds": asdict(thresholds),
            "overall_regressions": [],
            "query_tag_regressions": [],
            "new_query_tags": [],
        }

    metrics = [
        ("credits_used", thresholds.max_credits_regression_pct),
        ("elapsed_seconds", thresholds.max_elapsed_regression_pct),
    ]

    overall_regressions: list[dict[str, object]] = []
    for metric, threshold_pct in metrics:
        current_value = _safe_float(current_totals.get(metric))
        baseline_value = _safe_float(baseline_totals.get(metric))
        change_pct = _percent_change(current_value, baseline_value)
        if change_pct is None:
            continue
        if change_pct > threshold_pct:
            overall_regressions.append(
                {
                    "scope": "totals",
                    "metric": metric,
                    "baseline_value": baseline_value,
                    "current_value": current_value,
                    "change_pct": change_pct,
                    "threshold_pct": threshold_pct,
                }
            )

    current_tags = _query_tag_totals(current_report)
    baseline_tags = _query_tag_totals(baseline_report)

    query_tag_regressions: list[dict[str, object]] = []
    new_query_tags: list[str] = []

    for tag, current_values in current_tags.items():
        baseline_values = baseline_tags.get(tag)
        if baseline_values is None:
            new_query_tags.append(tag)
            continue

        for metric, threshold_pct in metrics:
            current_value = _safe_float(current_values.get(metric))
            baseline_value = _safe_float(baseline_values.get(metric))
            change_pct = _percent_change(current_value, baseline_value)
            if change_pct is None:
                continue
            if change_pct > threshold_pct:
                query_tag_regressions.append(
                    {
                        "scope": "query_tag",
                        "query_tag": tag,
                        "metric": metric,
                        "baseline_value": baseline_value,
                        "current_value": current_value,
                        "change_pct": change_pct,
                        "threshold_pct": threshold_pct,
                    }
                )

    status = "ok"
    if overall_regressions or query_tag_regressions:
        status = "regression-detected"

    return {
        "status": status,
        "detail": "",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "thresholds": asdict(thresholds),
        "overall_regressions": overall_regressions,
        "query_tag_regressions": query_tag_regressions,
        "new_query_tags": sorted(new_query_tags),
    }
