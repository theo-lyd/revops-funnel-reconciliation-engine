"""Tests for operational dashboards, SLO/SLI tracking, and scaling recommendations."""

from __future__ import annotations

from datetime import datetime, timedelta

from revops_funnel.operational_dashboards import (
    MetricTrend,
    PerformanceMetric,
    ScalingRecommendation,
    SLIMetric,
    TrendAnalysis,
    analyze_dependency_impact,
    analyze_metric_trend,
    calculate_cost_performance_correlation,
    calculate_trend,
    determine_dashboard_status,
    evaluate_sli_status,
    generate_operational_dashboard,
    generate_scaling_recommendations,
)


class TestPerformanceMetric:
    """Test PerformanceMetric dataclass."""

    def test_create_latency_metric(self) -> None:
        """Test creating a latency metric."""
        metric = PerformanceMetric(
            timestamp=datetime.utcnow().isoformat(),
            value=120.5,
            unit="seconds",
            metric_type="latency",
        )
        assert metric.value == 120.5
        assert metric.unit == "seconds"
        assert metric.metric_type == "latency"


class TestTrendCalculation:
    """Test trend calculation logic."""

    def test_calculate_trend_improving(self) -> None:
        """Test trend calculation when metric is improving."""
        recent = [100.0, 95.0, 90.0]
        historical = [150.0, 140.0, 130.0]
        trend, change = calculate_trend(recent, historical)
        assert trend == MetricTrend.IMPROVING
        assert change is not None
        assert change < 0  # Negative = improving

    def test_calculate_trend_degrading(self) -> None:
        """Test trend calculation when metric is degrading."""
        recent = [150.0, 160.0, 170.0]
        historical = [100.0, 105.0, 110.0]
        trend, change = calculate_trend(recent, historical)
        assert trend == MetricTrend.DEGRADING
        assert change is not None
        assert change > 0  # Positive = degrading

    def test_calculate_trend_stable(self) -> None:
        """Test trend calculation when metric is stable."""
        recent = [100.0, 101.0, 99.0]
        historical = [100.0, 102.0, 98.0]
        trend, change = calculate_trend(recent, historical)
        assert trend == MetricTrend.STABLE
        assert change is not None
        assert abs(change) < 5  # Small change = stable

    def test_calculate_trend_insufficient_data(self) -> None:
        """Test trend calculation with no data."""
        trend, change = calculate_trend([], [])
        assert trend == MetricTrend.INSUFFICIENT_DATA
        assert change is None

    def test_calculate_trend_zero_historical(self) -> None:
        """Test trend calculation with zero historical average."""
        recent = [100.0]
        historical = [0.0]
        trend, change = calculate_trend(recent, historical)
        assert trend == MetricTrend.STABLE
        assert change == 0.0


class TestTrendAnalysis:
    """Test trend analysis for metrics."""

    def test_analyze_metric_trend_with_data(self) -> None:
        """Test trend analysis with available data."""
        now = datetime.utcnow()
        metrics = [
            PerformanceMetric(
                timestamp=(now - timedelta(hours=i)).isoformat(),
                value=100.0 + i * 2,
                unit="seconds",
                metric_type="latency",
            )
            for i in range(10)
        ]

        analysis = analyze_metric_trend("latency", metrics, lookback_hours=24)
        assert analysis.metric_type == "latency"
        assert analysis.current_value is not None
        assert analysis.average_value is not None
        assert analysis.data_points > 0

    def test_analyze_metric_trend_no_data(self) -> None:
        """Test trend analysis with no data."""
        analysis = analyze_metric_trend("latency", [], lookback_hours=24)
        assert analysis.metric_type == "latency"
        assert analysis.current_value is None
        assert analysis.trend_direction == MetricTrend.INSUFFICIENT_DATA


class TestSLIEvaluation:
    """Test SLI status evaluation."""

    def test_evaluate_sli_healthy(self) -> None:
        """Test SLI status when metric is healthy."""
        status = evaluate_sli_status(metric_value=50.0, slo_threshold=100.0)
        assert status == "healthy"

    def test_evaluate_sli_degraded(self) -> None:
        """Test SLI status when metric is degraded."""
        status = evaluate_sli_status(metric_value=125.0, slo_threshold=100.0)
        assert status == "degraded"

    def test_evaluate_sli_unhealthy(self) -> None:
        """Test SLI status when metric is unhealthy."""
        status = evaluate_sli_status(metric_value=200.0, slo_threshold=100.0)
        assert status == "unhealthy"


class TestCostPerformanceCorrelation:
    """Test cost-performance correlation calculation."""

    def test_negative_correlation(self) -> None:
        """Test negative correlation (cost down, performance down)."""
        # Cost decreasing, performance (latency) improving simultaneously
        # Both trending in same direction = positive correlation
        # But we want to detect "cost efficiency improvements"
        cost_values = [10.0, 8.0, 6.0, 4.0]
        perf_values = [100.0, 80.0, 60.0, 40.0]
        corr = calculate_cost_performance_correlation(cost_values, perf_values)
        assert corr is not None
        assert corr > 0  # Positive correlation (both improving)

    def test_positive_correlation(self) -> None:
        """Test positive correlation (cost up, performance down)."""
        # Cost increasing, performance (latency) getting worse
        cost_values = [10.0, 12.0, 14.0, 16.0]
        perf_values = [100.0, 120.0, 140.0, 160.0]
        corr = calculate_cost_performance_correlation(cost_values, perf_values)
        assert corr is not None
        assert corr > 0  # Positive correlation

    def test_no_correlation_insufficient_data(self) -> None:
        """Test correlation with insufficient data."""
        corr = calculate_cost_performance_correlation([], [])
        assert corr is None

    def test_no_correlation_mismatched_lengths(self) -> None:
        """Test correlation with mismatched data lengths."""
        cost_values = [10.0, 15.0]
        perf_values = [100.0, 120.0, 140.0]
        corr = calculate_cost_performance_correlation(cost_values, perf_values)
        assert corr is None


class TestScalingRecommendations:
    """Test scaling recommendation generation."""

    def test_scale_up_recommendation_latency_degrading(self) -> None:
        """Test scale-up recommendation when latency is degrading."""
        latency_trend = TrendAnalysis(
            metric_type="latency",
            current_value=150.0,
            average_value=140.0,
            peak_value=160.0,
            min_value=130.0,
            trend_direction=MetricTrend.DEGRADING,
            change_percent=10.0,
            unit="seconds",
            data_points=10,
        )
        throughput_trend = TrendAnalysis(
            metric_type="throughput",
            current_value=1000.0,
            average_value=950.0,
            peak_value=1100.0,
            min_value=900.0,
            trend_direction=MetricTrend.STABLE,
            change_percent=0.0,
            unit="records/sec",
            data_points=10,
        )

        recommendations = generate_scaling_recommendations(latency_trend, throughput_trend)
        assert any(r.recommendation == ScalingRecommendation.SCALE_UP for r in recommendations)

    def test_monitor_recommendation_latency_stable(self) -> None:
        """Test monitor recommendation when latency is stable."""
        latency_trend = TrendAnalysis(
            metric_type="latency",
            current_value=100.0,
            average_value=100.0,
            peak_value=105.0,
            min_value=95.0,
            trend_direction=MetricTrend.STABLE,
            change_percent=0.5,
            unit="seconds",
            data_points=10,
        )
        throughput_trend = TrendAnalysis(
            metric_type="throughput",
            current_value=1000.0,
            average_value=1000.0,
            peak_value=1050.0,
            min_value=950.0,
            trend_direction=MetricTrend.STABLE,
            change_percent=0.0,
            unit="records/sec",
            data_points=10,
        )

        recommendations = generate_scaling_recommendations(latency_trend, throughput_trend)
        assert any(r.recommendation == ScalingRecommendation.MONITOR for r in recommendations)


class TestDashboardStatus:
    """Test overall dashboard status determination."""

    def test_dashboard_all_healthy(self) -> None:
        """Test dashboard status with all healthy metrics."""
        metrics = [
            SLIMetric(
                name="latency",
                current_value=60.0,
                slo_threshold=120.0,
                unit="minutes",
                status="healthy",
                trend=MetricTrend.STABLE,
                last_updated=datetime.utcnow().isoformat(),
            ),
            SLIMetric(
                name="cost",
                current_value=0.0005,
                slo_threshold=0.001,
                unit="USD/record",
                status="healthy",
                trend=MetricTrend.IMPROVING,
                last_updated=datetime.utcnow().isoformat(),
            ),
        ]
        status = determine_dashboard_status(metrics)
        assert status == "healthy"

    def test_dashboard_with_degraded(self) -> None:
        """Test dashboard status with degraded metrics."""
        metrics = [
            SLIMetric(
                name="latency",
                current_value=120.0,
                slo_threshold=100.0,
                unit="minutes",
                status="degraded",
                trend=MetricTrend.STABLE,
                last_updated=datetime.utcnow().isoformat(),
            ),
            SLIMetric(
                name="cost",
                current_value=0.0005,
                slo_threshold=0.001,
                unit="USD/record",
                status="healthy",
                trend=MetricTrend.IMPROVING,
                last_updated=datetime.utcnow().isoformat(),
            ),
        ]
        status = determine_dashboard_status(metrics)
        assert status == "degraded"


def test_analyze_dependency_impact_high_blast_radius() -> None:
    sli_metrics = [
        SLIMetric(
            name="transformation_latency",
            current_value=160.0,
            slo_threshold=120.0,
            unit="minutes",
            status="unhealthy",
            trend=MetricTrend.DEGRADING,
            last_updated=datetime.utcnow().isoformat(),
        )
    ]
    dependency_graph = {
        "transformation_latency": ["dbt-runner", "warehouse", "bi-api", "alerts", "scheduler"]
    }

    impact = analyze_dependency_impact(sli_metrics, dependency_graph)
    assert impact["blast_radius"] == "high"
    assert impact["impacted_services"] == 5


def test_generate_dashboard_includes_contract_fields() -> None:
    sli_metrics = [
        SLIMetric(
            name="latency",
            current_value=150.0,
            slo_threshold=120.0,
            unit="minutes",
            status="unhealthy",
            trend=MetricTrend.DEGRADING,
            last_updated=datetime.utcnow().isoformat(),
        )
    ]
    dashboard = generate_operational_dashboard(
        sli_metrics=sli_metrics,
        trend_analyses={},
        dependency_graph={"latency": ["warehouse"]},
        error_budget={"status": "healthy"},
        cost_of_reliability={"cost_per_latency_minute": 0.001},
    )
    payload = dashboard.to_dict()
    assert payload["contract_version"] == "2.0"
    assert payload["dependency_impact"]["impacted_services"] == 1

    def test_dashboard_with_unhealthy(self) -> None:
        """Test dashboard status with unhealthy metrics."""
        metrics = [
            SLIMetric(
                name="latency",
                current_value=250.0,
                slo_threshold=100.0,
                unit="minutes",
                status="unhealthy",
                trend=MetricTrend.DEGRADING,
                last_updated=datetime.utcnow().isoformat(),
            ),
            SLIMetric(
                name="cost",
                current_value=0.005,
                slo_threshold=0.001,
                unit="USD/record",
                status="healthy",
                trend=MetricTrend.IMPROVING,
                last_updated=datetime.utcnow().isoformat(),
            ),
        ]
        status = determine_dashboard_status(metrics)
        assert status == "critical"


class TestDashboardGeneration:
    """Test complete dashboard generation."""

    def test_generate_operational_dashboard_with_data(self) -> None:
        """Test generating a complete operational dashboard."""
        sli_metrics = [
            SLIMetric(
                name="latency",
                current_value=90.0,
                slo_threshold=120.0,
                unit="minutes",
                status="healthy",
                trend=MetricTrend.STABLE,
                last_updated=datetime.utcnow().isoformat(),
            ),
        ]

        trend_analyses = {
            "latency": TrendAnalysis(
                metric_type="latency",
                current_value=90.0,
                average_value=95.0,
                peak_value=100.0,
                min_value=85.0,
                trend_direction=MetricTrend.STABLE,
                change_percent=1.0,
                unit="minutes",
                data_points=10,
            ),
        }

        dashboard = generate_operational_dashboard(
            sli_metrics=sli_metrics,
            trend_analyses=trend_analyses,
            deployment_version="abc123",
        )

        assert dashboard.dashboard_id.startswith("dashboard_")
        assert dashboard.deployment_version == "abc123"
        assert len(dashboard.sli_metrics) == 1
        assert dashboard.operational_status == "healthy"

    def test_dashboard_serialization_to_dict(self) -> None:
        """Test dashboard serialization to dict."""
        sli_metrics = [
            SLIMetric(
                name="latency",
                current_value=90.0,
                slo_threshold=120.0,
                unit="minutes",
                status="healthy",
                trend=MetricTrend.STABLE,
                last_updated=datetime.utcnow().isoformat(),
            ),
        ]

        trend_analyses = {
            "latency": TrendAnalysis(
                metric_type="latency",
                current_value=90.0,
                average_value=95.0,
                peak_value=100.0,
                min_value=85.0,
                trend_direction=MetricTrend.STABLE,
                change_percent=1.0,
                unit="minutes",
                data_points=10,
            ),
        }

        dashboard = generate_operational_dashboard(
            sli_metrics=sli_metrics,
            trend_analyses=trend_analyses,
        )

        dashboard_dict = dashboard.to_dict()
        assert "dashboard_id" in dashboard_dict
        assert "sli_metrics" in dashboard_dict
        assert "trend_analyses" in dashboard_dict
        assert dashboard_dict["trend_analyses"]["latency"]["trend_direction"] == "stable"
