"""Production health checks and liveness monitoring for data freshness and transformation status."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

OBSERVABILITY_CONTRACT_VERSION = "2.0"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class HealthThresholds:
    max_freshness_hours: float
    max_job_duration_minutes: float


@dataclass(frozen=True)
class ErrorBudgetPolicy:
    monthly_budget_minutes: float
    burn_rate_warning: float
    burn_rate_critical: float


@dataclass(frozen=True)
class ErrorBudgetStatus:
    monthly_budget_minutes: float
    consumed_minutes: float
    remaining_minutes: float
    burn_rate_24h: float
    burn_rate_7d: float
    status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "monthly_budget_minutes": round(self.monthly_budget_minutes, 3),
            "consumed_minutes": round(self.consumed_minutes, 3),
            "remaining_minutes": round(self.remaining_minutes, 3),
            "burn_rate_24h": round(self.burn_rate_24h, 3),
            "burn_rate_7d": round(self.burn_rate_7d, 3),
            "status": self.status,
        }


@dataclass(frozen=True)
class HealthCheck:
    check_name: str
    status: HealthStatus
    detail: str
    evaluated_at_utc: str
    last_known_value: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "check_name": self.check_name,
            "status": str(self.status.value),
            "detail": self.detail,
            "evaluated_at_utc": self.evaluated_at_utc,
            "last_known_value": self.last_known_value,
        }


def _timestamp_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hours_ago(hours: float) -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=hours)


def check_data_freshness(
    table_name: str,
    last_updated_utc: str | None,
    thresholds: HealthThresholds,
) -> HealthCheck:
    """Check if table has been updated within freshness SLO.

    Args:
        table_name: e.g. 'analytics.int_funnel_stage_events'
        last_updated_utc: ISO format timestamp of last successful update, or None if unknown
        thresholds: HealthThresholds with max_freshness_hours

    Returns:
        HealthCheck with status and detail
    """
    if not last_updated_utc:
        return HealthCheck(
            check_name=f"data_freshness__{table_name}",
            status=HealthStatus.SKIPPED,
            detail="no last_updated timestamp available",
            evaluated_at_utc=_timestamp_iso(),
            last_known_value="unknown",
        )

    try:
        last_updated = datetime.fromisoformat(last_updated_utc.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return HealthCheck(
            check_name=f"data_freshness__{table_name}",
            status=HealthStatus.SKIPPED,
            detail=f"unable to parse timestamp: {last_updated_utc}",
            evaluated_at_utc=_timestamp_iso(),
            last_known_value=last_updated_utc or "none",
        )

    now = datetime.now(timezone.utc)
    age_hours = (now - last_updated).total_seconds() / 3600.0

    if age_hours <= thresholds.max_freshness_hours:
        status = HealthStatus.HEALTHY
        detail = (
            f"{table_name} is fresh: {age_hours:.1f}h old "
            f"(threshold: {thresholds.max_freshness_hours}h)"
        )
    else:
        # If significantly over threshold, mark unhealthy; otherwise degraded
        severity_ratio = age_hours / thresholds.max_freshness_hours
        status = HealthStatus.UNHEALTHY if severity_ratio > 1.5 else HealthStatus.DEGRADED
        detail = (
            f"{table_name} is stale: {age_hours:.1f}h old "
            f"(threshold: {thresholds.max_freshness_hours}h)"
        )

    return HealthCheck(
        check_name=f"data_freshness__{table_name}",
        status=status,
        detail=detail,
        evaluated_at_utc=_timestamp_iso(),
        last_known_value=last_updated_utc,
    )


def check_job_duration(
    job_name: str,
    job_duration_minutes: float | None,
    thresholds: HealthThresholds,
) -> HealthCheck:
    """Check if transformation job completed within SLO duration.

    Args:
        job_name: e.g. 'dbt-build-prod'
        job_duration_minutes: duration of last completed job, or None if no job run recorded
        thresholds: HealthThresholds with max_job_duration_minutes

    Returns:
        HealthCheck with status and detail
    """
    if job_duration_minutes is None:
        return HealthCheck(
            check_name=f"job_duration__{job_name}",
            status=HealthStatus.SKIPPED,
            detail="no recent job execution recorded",
            evaluated_at_utc=_timestamp_iso(),
            last_known_value="unknown",
        )

    if job_duration_minutes <= 0:
        return HealthCheck(
            check_name=f"job_duration__{job_name}",
            status=HealthStatus.SKIPPED,
            detail=f"invalid job duration: {job_duration_minutes}",
            evaluated_at_utc=_timestamp_iso(),
            last_known_value=str(job_duration_minutes),
        )

    if job_duration_minutes <= thresholds.max_job_duration_minutes:
        status = HealthStatus.HEALTHY
        detail = (
            f"{job_name} duration is healthy: {job_duration_minutes:.0f}m "
            f"(threshold: {thresholds.max_job_duration_minutes:.0f}m)"
        )
    else:
        severity_ratio = job_duration_minutes / thresholds.max_job_duration_minutes
        status = HealthStatus.UNHEALTHY if severity_ratio > 1.5 else HealthStatus.DEGRADED
        detail = (
            f"{job_name} duration exceeded: {job_duration_minutes:.0f}m "
            f"(threshold: {thresholds.max_job_duration_minutes:.0f}m)"
        )

    return HealthCheck(
        check_name=f"job_duration__{job_name}",
        status=status,
        detail=detail,
        evaluated_at_utc=_timestamp_iso(),
        last_known_value=f"{job_duration_minutes:.0f}m",
    )


def evaluate_liveness(checks: list[HealthCheck]) -> HealthStatus:
    """Aggregate multiple health checks into liveness status.

    Priority: UNHEALTHY > DEGRADED > HEALTHY > SKIPPED

    If any check is UNHEALTHY, overall is UNHEALTHY.
    If any check is DEGRADED (and no UNHEALTHY), overall is DEGRADED.
    If all are HEALTHY or SKIPPED, overall is HEALTHY.
    """
    if not checks:
        return HealthStatus.HEALTHY

    statuses = {check.status for check in checks}

    if HealthStatus.UNHEALTHY in statuses:
        return HealthStatus.UNHEALTHY
    if HealthStatus.DEGRADED in statuses:
        return HealthStatus.DEGRADED
    if HealthStatus.HEALTHY in statuses:
        return HealthStatus.HEALTHY
    return HealthStatus.SKIPPED


def generate_health_report(
    checks: list[HealthCheck],
    error_budget: ErrorBudgetStatus | None = None,
) -> dict[str, object]:
    """Generate machine-readable health report from checks."""
    overall_status = evaluate_liveness(checks)

    unhealthy_count = sum(1 for c in checks if c.status == HealthStatus.UNHEALTHY)
    degraded_count = sum(1 for c in checks if c.status == HealthStatus.DEGRADED)
    healthy_count = sum(1 for c in checks if c.status == HealthStatus.HEALTHY)
    skipped_count = sum(1 for c in checks if c.status == HealthStatus.SKIPPED)

    report: dict[str, object] = {
        "contract_version": OBSERVABILITY_CONTRACT_VERSION,
        "generated_at_utc": _timestamp_iso(),
        "overall_status": str(overall_status.value),
        "summary": {
            "total_checks": len(checks),
            "healthy": healthy_count,
            "degraded": degraded_count,
            "unhealthy": unhealthy_count,
            "skipped": skipped_count,
        },
        "checks": [check.to_dict() for check in checks],
    }

    if error_budget is not None:
        report["error_budget"] = error_budget.to_dict()

    return report


def compute_error_budget_status(
    checks: list[HealthCheck],
    policy: ErrorBudgetPolicy,
) -> ErrorBudgetStatus:
    """Estimate error budget consumption from degraded/unhealthy check windows.

    The model is intentionally conservative and deterministic for CI/release usage.
    """
    degraded = sum(1 for c in checks if c.status == HealthStatus.DEGRADED)
    unhealthy = sum(1 for c in checks if c.status == HealthStatus.UNHEALTHY)

    consumed_minutes = (degraded * 15.0) + (unhealthy * 45.0)
    remaining_minutes = max(policy.monthly_budget_minutes - consumed_minutes, 0.0)

    # Window approximations: degraded contributes less burn pressure than unhealthy.
    burn_24h = 0.0
    if policy.monthly_budget_minutes > 0:
        burn_24h = ((degraded * 0.5) + (unhealthy * 1.5)) / (
            policy.monthly_budget_minutes / (30 * 24)
        )
    burn_7d = burn_24h / 2.0

    if burn_24h >= policy.burn_rate_critical:
        status = "critical"
    elif burn_24h >= policy.burn_rate_warning:
        status = "warning"
    else:
        status = "healthy"

    return ErrorBudgetStatus(
        monthly_budget_minutes=policy.monthly_budget_minutes,
        consumed_minutes=consumed_minutes,
        remaining_minutes=remaining_minutes,
        burn_rate_24h=burn_24h,
        burn_rate_7d=burn_7d,
        status=status,
    )


def build_incident_timeline_events(checks: list[HealthCheck]) -> list[dict[str, str]]:
    """Build timeline events from health checks for incident reconstruction."""
    events: list[dict[str, str]] = []
    for check in checks:
        if check.status in {HealthStatus.DEGRADED, HealthStatus.UNHEALTHY}:
            events.append(
                {
                    "timestamp_utc": check.evaluated_at_utc,
                    "source": "health_report",
                    "event_type": "health_signal",
                    "severity": str(check.status.value),
                    "summary": check.detail,
                }
            )
    return events
