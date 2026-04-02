from __future__ import annotations

from datetime import datetime, timedelta, timezone

from revops_funnel.health_monitoring import (
    HealthCheck,
    HealthStatus,
    HealthThresholds,
    check_data_freshness,
    check_job_duration,
    evaluate_liveness,
    generate_health_report,
)


def test_check_data_freshness_healthy() -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    thresholds = HealthThresholds(max_freshness_hours=24.0, max_job_duration_minutes=120.0)

    check = check_data_freshness("test_table", now_iso, thresholds)

    assert check.status == HealthStatus.HEALTHY
    assert "fresh" in check.detail.lower()


def test_check_data_freshness_degraded() -> None:
    old_time = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
    thresholds = HealthThresholds(max_freshness_hours=24.0, max_job_duration_minutes=120.0)

    check = check_data_freshness("test_table", old_time, thresholds)

    assert check.status == HealthStatus.DEGRADED
    assert "stale" in check.detail.lower()


def test_check_data_freshness_unhealthy() -> None:
    old_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    thresholds = HealthThresholds(max_freshness_hours=24.0, max_job_duration_minutes=120.0)

    check = check_data_freshness("test_table", old_time, thresholds)

    assert check.status == HealthStatus.UNHEALTHY
    assert "stale" in check.detail.lower()


def test_check_data_freshness_skipped_no_timestamp() -> None:
    thresholds = HealthThresholds(max_freshness_hours=24.0, max_job_duration_minutes=120.0)

    check = check_data_freshness("test_table", None, thresholds)

    assert check.status == HealthStatus.SKIPPED
    assert check.detail == "no last_updated timestamp available"


def test_check_job_duration_healthy() -> None:
    thresholds = HealthThresholds(max_freshness_hours=24.0, max_job_duration_minutes=120.0)

    check = check_job_duration("dbt-build", 90.0, thresholds)

    assert check.status == HealthStatus.HEALTHY
    assert "healthy" in check.detail.lower()


def test_check_job_duration_degraded() -> None:
    thresholds = HealthThresholds(max_freshness_hours=24.0, max_job_duration_minutes=120.0)

    check = check_job_duration("dbt-build", 150.0, thresholds)

    assert check.status == HealthStatus.DEGRADED
    assert "exceeded" in check.detail.lower()


def test_check_job_duration_unhealthy() -> None:
    thresholds = HealthThresholds(max_freshness_hours=24.0, max_job_duration_minutes=120.0)

    check = check_job_duration("dbt-build", 250.0, thresholds)

    assert check.status == HealthStatus.UNHEALTHY
    assert "exceeded" in check.detail.lower()


def test_evaluate_liveness_all_healthy() -> None:
    checks = [
        HealthCheck("c1", HealthStatus.HEALTHY, "ok", "2026-04-02T00:00:00+00:00"),
        HealthCheck("c2", HealthStatus.HEALTHY, "ok", "2026-04-02T00:00:00+00:00"),
    ]

    status = evaluate_liveness(checks)
    assert status == HealthStatus.HEALTHY


def test_evaluate_liveness_with_degraded() -> None:
    checks = [
        HealthCheck("c1", HealthStatus.HEALTHY, "ok", "2026-04-02T00:00:00+00:00"),
        HealthCheck("c2", HealthStatus.DEGRADED, "degraded", "2026-04-02T00:00:00+00:00"),
    ]

    status = evaluate_liveness(checks)
    assert status == HealthStatus.DEGRADED


def test_evaluate_liveness_with_unhealthy() -> None:
    checks = [
        HealthCheck("c1", HealthStatus.HEALTHY, "ok", "2026-04-02T00:00:00+00:00"),
        HealthCheck("c2", HealthStatus.DEGRADED, "degraded", "2026-04-02T00:00:00+00:00"),
        HealthCheck("c3", HealthStatus.UNHEALTHY, "bad", "2026-04-02T00:00:00+00:00"),
    ]

    status = evaluate_liveness(checks)
    assert status == HealthStatus.UNHEALTHY


def test_generate_health_report() -> None:
    checks = [
        HealthCheck("c1", HealthStatus.HEALTHY, "ok", "2026-04-02T00:00:00+00:00"),
        HealthCheck("c2", HealthStatus.DEGRADED, "degraded", "2026-04-02T00:00:00+00:00"),
    ]

    report = generate_health_report(checks)

    assert report["overall_status"] == "degraded"
    assert report["summary"]["healthy"] == 1
    assert report["summary"]["degraded"] == 1
    assert len(report["checks"]) == 2
    assert report["checks"][0]["status"] == "healthy"
    assert report["checks"][1]["status"] == "degraded"
