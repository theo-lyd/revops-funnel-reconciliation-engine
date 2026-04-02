"""Tests for Phase 8 enhancements (Batches 1-10)."""

from __future__ import annotations

import pytest

from revops_funnel.cost_observability import (
    QueryCostEntry,
    TransformationLayer,
    _bytes_per_result_row,
    _classify_transformation_layer,
    _compute_seasonal_factor,
    _compute_trend_line,
    _compute_z_score,
    _detect_statistical_anomaly,
    _estimate_prod_cost_from_staging,
    _forecast_end_of_period_cost,
    aggregate_query_cost_attribution,
)


class TestTransformationLayerClassification:
    """Test Batch 1: Transformation layer attribution."""

    def test_classify_staging_layer_from_path(self) -> None:
        """Test staging layer classification from dbt model path."""
        layer = _classify_transformation_layer("models/staging/crm/stg_accounts.sql", "")
        assert layer == TransformationLayer.STAGING.value

    def test_classify_intermediate_layer_from_tag(self) -> None:
        """Test intermediate layer classification from query tag."""
        layer = _classify_transformation_layer("", "dbt_int_funnel_velocity")
        assert layer == TransformationLayer.INTERMEDIATE.value

    def test_classify_marts_layer_from_path(self) -> None:
        """Test marts layer classification from dbt model path."""
        layer = _classify_transformation_layer("models/marts/fct_revenue.sql", "")
        assert layer == TransformationLayer.MARTS.value

    def test_classify_unknown_layer_fallback(self) -> None:
        """Test unknown layer for unrecognized paths."""
        layer = _classify_transformation_layer("models/other/custom_model.sql", "random_tag")
        assert layer == TransformationLayer.UNKNOWN.value

    def test_aggregate_includes_layer_attribution(self) -> None:
        """Test that aggregation includes attribution_by_transformation_layer."""
        entries = [
            QueryCostEntry(
                query_id="q1",
                query_tag="dbt_stg_accounts",
                warehouse_name="WH",
                user_name="user1",
                elapsed_seconds=10.0,
                bytes_scanned=1_000_000,
                credits_used=5.0,
                started_at_utc="2026-04-02T00:00:00Z",
                dbt_model_path="models/staging/crm/stg_accounts.sql",
            ),
            QueryCostEntry(
                query_id="q2",
                query_tag="dbt_int_opportunities",
                warehouse_name="WH",
                user_name="user1",
                elapsed_seconds=50.0,
                bytes_scanned=10_000_000,
                credits_used=25.0,
                started_at_utc="2026-04-02T00:05:00Z",
                dbt_model_path="models/intermediate/pipeline/int_opportunities.sql",
            ),
        ]

        result = aggregate_query_cost_attribution(entries)

        assert "attribution_by_transformation_layer" in result
        layer_attr = result["attribution_by_transformation_layer"]
        assert len(layer_attr) >= 1
        assert any(row.get("layer") == TransformationLayer.STAGING.value for row in layer_attr)
        assert any(row.get("layer") == TransformationLayer.INTERMEDIATE.value for row in layer_attr)


class TestStatisticalAnomalyDetection:
    """Test Batch 2: Statistical anomaly detection."""

    def test_z_score_computation(self) -> None:
        """Test z-score calculation."""
        z = _compute_z_score(100.0, 50.0, 10.0)
        assert abs(z - 5.0) < 0.01

    def test_anomaly_detection_high_z_score(self) -> None:
        """Test anomaly detection with high z-score."""
        historical = [45.0, 47.0, 46.0, 48.0, 45.0]
        current = 100.0

        result = _detect_statistical_anomaly(current, historical, z_threshold=3.0)

        assert result["status"] == "anomaly"
        assert result["z_anomaly"] is True
        assert result["z_score"] > 3.0

    def test_anomaly_detection_normal_values(self) -> None:
        """Test anomaly detection with normal values."""
        historical = [45.0, 47.0, 46.0, 48.0, 45.0]
        current = 46.0

        result = _detect_statistical_anomaly(current, historical, z_threshold=3.0)

        assert result["status"] == "ok"
        assert result["z_anomaly"] is False


class TestCostForecasting:
    """Test Batch 3: Cost forecasting."""

    def test_trend_line_positive_slope(self) -> None:
        """Test trend line computation with increasing costs."""
        daily_costs = [10.0, 15.0, 20.0, 25.0, 30.0]
        slope, intercept = _compute_trend_line(daily_costs)

        assert slope > 0  # Increasing trend
        assert intercept >= 0  # Starting value

    def test_forecast_end_of_period(self) -> None:
        """Test end-of-period cost forecasting."""
        current_burn = 45.0
        daily_costs = [1.5, 1.6, 1.4, 1.7, 1.5, 1.6]

        forecast, confidence = _forecast_end_of_period_cost(
            current_burn, daily_costs, days_elapsed=6, days_in_period=30
        )

        assert forecast >= current_burn  # Should project higher or equal
        assert 0.7 <= confidence <= 0.95  # Confidence in reasonable range


class TestCrossEnvironmentCosts:
    """Test Batch 7: Cross-environment visibility."""

    def test_estimate_prod_cost_from_staging(self) -> None:
        """Test production cost extrapolation from staging."""
        staging_monthly = 10.0
        staging_trend = 0.5

        prod_today, prod_steady, confidence = _estimate_prod_cost_from_staging(
            staging_monthly, staging_trend, staging_to_prod_multiplier=5.0
        )

        assert prod_today == 50.0  # 10 * 5
        assert prod_steady > prod_today  # Steady state higher due to trend
        assert 0.7 <= confidence <= 0.95


class TestPatternAnalysis:
    """Test Batch 4: Query pattern analysis."""

    def test_bytes_per_result_row(self) -> None:
        """Test bytes-per-result-row efficiency metric."""
        bytes_per_row = _bytes_per_result_row(100_000_000, 50_000)
        assert bytes_per_row == 2000.0


class TestSeasonalityAdjustment:
    """Test Batch 9: Seasonality in costs."""

    def test_seasonal_factor_q4_peak(self) -> None:
        """Test Q4 peak seasonal multiplier."""
        factor = _compute_seasonal_factor(50)  # Mid-Q4
        assert factor > 1.0  # Should be elevated in Q4

    def test_seasonal_factor_jan_trough(self) -> None:
        """Test January trough seasonal multiplier."""
        factor = _compute_seasonal_factor(2)  # Early January
        assert factor < 1.0  # Should be reduced in January

    def test_seasonal_factor_normal_quarter(self) -> None:
        """Test normal quarter seasonal factor."""
        factor = _compute_seasonal_factor(20)  # May (Q2)
        assert 0.95 <= factor <= 1.05  # Close to baseline


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
