"""Operational dashboards, SLO/SLI tracking, and scaling recommendations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from statistics import mean, stdev
from typing import Any


class MetricTrend(str, Enum):
    """Trend direction for metrics."""

    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    INSUFFICIENT_DATA = "insufficient_data"


class ScalingRecommendation(str, Enum):
    """Scaling recommendation types."""

    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    MONITOR = "monitor"
    NO_ACTION = "no_action"


@dataclass
class PerformanceMetric:
    """Single performance data point."""

    timestamp: str
    value: float
    unit: str
    metric_type: str  # e.g., 'latency', 'cost_per_record', 'throughput'


@dataclass
class TrendAnalysis:
    """Trend analysis for a metric over time."""

    metric_type: str
    current_value: float | None
    average_value: float | None
    peak_value: float | None
    min_value: float | None
    trend_direction: MetricTrend
    change_percent: float | None  # percentage change recent vs historical
    unit: str
    data_points: int


@dataclass
class SLOThresholds:
    """Service-level objective thresholds."""

    healthy_threshold: float
    degraded_threshold: float  # 1.5x threshold = start being concerned
    unhealthy_threshold: float  # 2x threshold = alert


@dataclass
class SLIMetric:
    """Service-level indicator measurement."""

    name: str
    current_value: float
    slo_threshold: float
    unit: str
    status: str  # healthy, degraded, unhealthy
    trend: MetricTrend
    last_updated: str


@dataclass
class ScalingRecommendationDetail:
    """Detailed scaling recommendation."""

    recommendation: ScalingRecommendation
    reason: str
    confidence: float  # 0.0-1.0
    estimated_impact: str
    priority: str  # high, medium, low


@dataclass
class OperationalDashboard:
    """Complete operational dashboard."""

    dashboard_id: str
    generated_at: str
    deployment_version: str | None
    sli_metrics: list[SLIMetric]
    trend_analyses: dict[str, TrendAnalysis]
    scaling_recommendations: list[ScalingRecommendationDetail]
    cost_performance_correlation: float | None  # -1.0 to 1.0
    operational_status: str  # healthy, degraded, critical

    def to_dict(self) -> dict[str, Any]:
        """Convert to machine-readable dictionary."""
        return {
            "dashboard_id": self.dashboard_id,
            "generated_at": self.generated_at,
            "deployment_version": self.deployment_version,
            "sli_metrics": [asdict(m) for m in self.sli_metrics],
            "trend_analyses": {
                k: {
                    **asdict(v),
                    "trend_direction": v.trend_direction.value,
                }
                for k, v in self.trend_analyses.items()
            },
            "scaling_recommendations": [
                {
                    **asdict(r),
                    "recommendation": r.recommendation.value,
                }
                for r in self.scaling_recommendations
            ],
            "cost_performance_correlation": self.cost_performance_correlation,
            "operational_status": self.operational_status,
        }


def calculate_trend(
    recent_values: list[float], historical_values: list[float]
) -> tuple[MetricTrend, float | None]:
    """Calculate trend direction and percent change."""
    if not recent_values or not historical_values:
        return MetricTrend.INSUFFICIENT_DATA, None

    recent_avg = mean(recent_values)
    historical_avg = mean(historical_values)

    if historical_avg == 0:
        return MetricTrend.STABLE, 0.0

    change_percent = ((recent_avg - historical_avg) / historical_avg) * 100

    # Determine trend based on percentage change threshold
    if abs(change_percent) < 2.0:  # Less than 2% is stable
        return MetricTrend.STABLE, change_percent
    elif change_percent > 0:  # cost/latency getting worse is degrading
        return MetricTrend.DEGRADING, change_percent
    else:  # cost/latency getting better is improving
        return MetricTrend.IMPROVING, change_percent


def analyze_metric_trend(
    metric_type: str,
    performance_history: list[PerformanceMetric],
    lookback_hours: int = 168,  # 1 week default
) -> TrendAnalysis:
    """Analyze trend for a given metric type."""
    if not performance_history:
        return TrendAnalysis(
            metric_type=metric_type,
            current_value=None,
            average_value=None,
            peak_value=None,
            min_value=None,
            trend_direction=MetricTrend.INSUFFICIENT_DATA,
            change_percent=None,
            unit="",
            data_points=0,
        )

    values = [m.value for m in performance_history]
    unit = performance_history[0].unit if performance_history else ""

    cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
    cutoff_timestamp = cutoff_time.isoformat()

    recent_metrics = [m for m in performance_history if m.timestamp >= cutoff_timestamp]
    historical_metrics = [m for m in performance_history if m.timestamp < cutoff_timestamp]

    recent_values = [m.value for m in recent_metrics]
    historical_values = [m.value for m in historical_metrics]

    trend_direction, change_percent = calculate_trend(recent_values, historical_values)

    return TrendAnalysis(
        metric_type=metric_type,
        current_value=values[-1] if values else None,
        average_value=mean(values) if values else None,
        peak_value=max(values) if values else None,
        min_value=min(values) if values else None,
        trend_direction=trend_direction,
        change_percent=change_percent,
        unit=unit,
        data_points=len(values),
    )


def evaluate_sli_status(metric_value: float, slo_threshold: float) -> str:
    """Determine SLI health status."""
    if metric_value <= slo_threshold:
        return "healthy"
    elif metric_value <= slo_threshold * 1.5:
        return "degraded"
    else:
        return "unhealthy"


def calculate_cost_performance_correlation(
    cost_values: list[float], performance_values: list[float]
) -> float | None:
    """Calculate correlation between cost and performance metrics.

    Negative correlation (cost down, performance up) is ideal.
    Positive correlation (cost up, performance down) is concerning.
    Returns correlation coefficient -1.0 to 1.0, or None if insufficient data.
    """
    if len(cost_values) < 2 or len(performance_values) < 2:
        return None

    if len(cost_values) != len(performance_values):
        return None

    try:
        cost_mean = mean(cost_values)
        perf_mean = mean(performance_values)

        if len(cost_values) < 2:
            return None

        cost_stdev_val = stdev(cost_values)
        perf_stdev_val = stdev(performance_values)

        if cost_stdev_val == 0 or perf_stdev_val == 0:
            return None

        covariance = sum(
            (cost_values[i] - cost_mean) * (performance_values[i] - perf_mean)
            for i in range(len(cost_values))
        ) / len(cost_values)

        correlation = covariance / (cost_stdev_val * perf_stdev_val)
        return round(correlation, 3)
    except (ValueError, ZeroDivisionError):
        return None


def generate_scaling_recommendations(
    latency_trend: TrendAnalysis, throughput_trend: TrendAnalysis
) -> list[ScalingRecommendationDetail]:
    """Generate scaling recommendations based on performance trends."""
    recommendations: list[ScalingRecommendationDetail] = []

    # Latency degrading + throughput adequate = scale up
    if (
        latency_trend.trend_direction == MetricTrend.DEGRADING
        and latency_trend.change_percent is not None
        and abs(latency_trend.change_percent) > 5
    ):
        recommendations.append(
            ScalingRecommendationDetail(
                recommendation=ScalingRecommendation.SCALE_UP,
                reason=(
                    f"Transformation latency degrading by "
                    f"{abs(latency_trend.change_percent):.1f}% over past week"
                ),
                confidence=0.8,
                estimated_impact="Reduce latency by 30-40%",
                priority="high",
            )
        )

    # Cost improving without latency degradation = opportunity
    if latency_trend.trend_direction in (
        MetricTrend.STABLE,
        MetricTrend.IMPROVING,
    ):
        recommendations.append(
            ScalingRecommendationDetail(
                recommendation=ScalingRecommendation.MONITOR,
                reason="Performance stable; continue monitoring cost trends",
                confidence=0.7,
                estimated_impact="Baseline for future scaling decisions",
                priority="medium",
            )
        )

    if not recommendations:
        recommendations.append(
            ScalingRecommendationDetail(
                recommendation=ScalingRecommendation.NO_ACTION,
                reason="Current performance metrics within SLO targets",
                confidence=0.9,
                estimated_impact="No immediate scaling needed",
                priority="low",
            )
        )

    return recommendations


def determine_dashboard_status(
    sli_metrics: list[SLIMetric],
) -> str:
    """Determine overall operational dashboard status."""
    unhealthy_count = sum(1 for m in sli_metrics if m.status == "unhealthy")
    degraded_count = sum(1 for m in sli_metrics if m.status == "degraded")

    if unhealthy_count > 0:
        return "critical"
    elif degraded_count > len(sli_metrics) * 0.3:  # More than 30% degraded
        return "degraded"
    else:
        return "healthy"


def generate_operational_dashboard(
    sli_metrics: list[SLIMetric],
    trend_analyses: dict[str, TrendAnalysis],
    cost_values: list[float] | None = None,
    performance_values: list[float] | None = None,
    deployment_version: str | None = None,
) -> OperationalDashboard:
    """Generate complete operational dashboard."""
    # Calculate correlation if data available
    correlation = None
    if cost_values and performance_values:
        correlation = calculate_cost_performance_correlation(cost_values, performance_values)

    # Get latency and throughput trends for scaling recommendations
    latency_trend = trend_analyses.get("latency", None)
    throughput_trend = trend_analyses.get("throughput", None)

    recommendations: list[ScalingRecommendationDetail] = []
    if latency_trend and throughput_trend:
        recommendations = generate_scaling_recommendations(latency_trend, throughput_trend)

    dashboard_status = determine_dashboard_status(sli_metrics)

    return OperationalDashboard(
        dashboard_id=f"dashboard_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        generated_at=datetime.utcnow().isoformat(),
        deployment_version=deployment_version,
        sli_metrics=sli_metrics,
        trend_analyses=trend_analyses,
        scaling_recommendations=recommendations,
        cost_performance_correlation=correlation,
        operational_status=dashboard_status,
    )
