"""On-call runbook generation from operational failure artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class IncidentSeverity(str, Enum):
    """Incident severity levels used for runbook routing."""

    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


@dataclass(frozen=True)
class FailurePattern:
    """Detected operational failure pattern."""

    pattern_id: str
    detected: bool
    severity: IncidentSeverity
    summary: str
    source_artifact: str
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["severity"] = self.severity.value
        return payload


@dataclass(frozen=True)
class RunbookAction:
    """Action item for on-call responders."""

    step: str
    owner: str
    sla_minutes: int
    command: str


@dataclass(frozen=True)
class EscalationStep:
    """Escalation procedure step."""

    severity: IncidentSeverity
    target: str
    action: str
    trigger_reason: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["severity"] = self.severity.value
        return payload


@dataclass(frozen=True)
class OnCallRunbookReport:
    """Full on-call runbook report artifact."""

    generated_at_utc: str
    overall_status: str
    incident_required: bool
    highest_severity: IncidentSeverity | None
    failure_patterns: list[FailurePattern]
    recommended_actions: list[RunbookAction]
    escalation_steps: list[EscalationStep]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at_utc": self.generated_at_utc,
            "overall_status": self.overall_status,
            "incident_required": self.incident_required,
            "highest_severity": (
                self.highest_severity.value if self.highest_severity is not None else None
            ),
            "failure_patterns": [pattern.to_dict() for pattern in self.failure_patterns],
            "recommended_actions": [asdict(action) for action in self.recommended_actions],
            "escalation_steps": [step.to_dict() for step in self.escalation_steps],
        }


def _timestamp_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_str(payload: dict[str, Any], key: str, default: str = "") -> str:
    value = payload.get(key, default)
    return str(value) if value is not None else default


def _safe_float(payload: dict[str, Any], key: str) -> float | None:
    value = payload.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def detect_failure_patterns(
    health_report: dict[str, Any] | None,
    dashboard_report: dict[str, Any] | None,
    rollback_execution_report: dict[str, Any] | None,
    incident_dispatch_report: dict[str, Any] | None,
    dead_letter_escalation_report: dict[str, Any] | None,
) -> list[FailurePattern]:
    """Detect standardized failure patterns from artifacts."""
    patterns: list[FailurePattern] = []

    if health_report:
        health_status = _safe_str(health_report, "overall_status", "unknown")
        if health_status == "unhealthy":
            patterns.append(
                FailurePattern(
                    pattern_id="health_unhealthy",
                    detected=True,
                    severity=IncidentSeverity.P1,
                    summary="Health checks reported unhealthy status",
                    source_artifact="health_report",
                    evidence=f"overall_status={health_status}",
                )
            )
        elif health_status == "degraded":
            patterns.append(
                FailurePattern(
                    pattern_id="health_degraded",
                    detected=True,
                    severity=IncidentSeverity.P2,
                    summary="Health checks reported degraded status",
                    source_artifact="health_report",
                    evidence=f"overall_status={health_status}",
                )
            )

    if dashboard_report:
        dashboard_status = _safe_str(dashboard_report, "operational_status", "unknown")
        if dashboard_status == "critical":
            patterns.append(
                FailurePattern(
                    pattern_id="dashboard_critical",
                    detected=True,
                    severity=IncidentSeverity.P1,
                    summary="Operational dashboard reached critical state",
                    source_artifact="operational_dashboard",
                    evidence=f"operational_status={dashboard_status}",
                )
            )
        elif dashboard_status == "degraded":
            patterns.append(
                FailurePattern(
                    pattern_id="dashboard_degraded",
                    detected=True,
                    severity=IncidentSeverity.P2,
                    summary="Operational dashboard indicates degraded state",
                    source_artifact="operational_dashboard",
                    evidence=f"operational_status={dashboard_status}",
                )
            )

        for metric in dashboard_report.get("sli_metrics", []):
            if not isinstance(metric, dict):
                continue
            metric_name = _safe_str(metric, "name", "unknown")
            metric_status = _safe_str(metric, "status", "unknown")
            current_value = _safe_float(metric, "current_value")
            threshold = _safe_float(metric, "slo_threshold")

            if metric_status == "unhealthy":
                patterns.append(
                    FailurePattern(
                        pattern_id=f"sli_unhealthy_{metric_name}",
                        detected=True,
                        severity=IncidentSeverity.P1,
                        summary=f"SLI {metric_name} breached unhealthy threshold",
                        source_artifact="operational_dashboard",
                        evidence=(
                            f"status={metric_status},value={current_value},threshold={threshold}"
                        ),
                    )
                )
            elif metric_status == "degraded":
                patterns.append(
                    FailurePattern(
                        pattern_id=f"sli_degraded_{metric_name}",
                        detected=True,
                        severity=IncidentSeverity.P2,
                        summary=f"SLI {metric_name} breached degraded threshold",
                        source_artifact="operational_dashboard",
                        evidence=(
                            f"status={metric_status},value={current_value},threshold={threshold}"
                        ),
                    )
                )

    if rollback_execution_report:
        execution_mode = _safe_str(rollback_execution_report, "execution_mode", "unknown")
        execution_enabled = bool(rollback_execution_report.get("execution_enabled", False))
        if execution_mode == "controlled" and execution_enabled:
            patterns.append(
                FailurePattern(
                    pattern_id="rollback_executed",
                    detected=True,
                    severity=IncidentSeverity.P1,
                    summary="Controlled rollback playbook executed",
                    source_artifact="deployment_rollback_execution",
                    evidence="execution_mode=controlled",
                )
            )

    if incident_dispatch_report:
        dispatch_status = _safe_str(incident_dispatch_report, "dispatch_status", "unknown")
        webhook_configured = bool(
            incident_dispatch_report.get("incident_webhook_configured", False)
        )
        if webhook_configured and dispatch_status != "sent":
            patterns.append(
                FailurePattern(
                    pattern_id="incident_dispatch_failed",
                    detected=True,
                    severity=IncidentSeverity.P1,
                    summary="Rollback incident notification dispatch failed",
                    source_artifact="rollback_incident_dispatch",
                    evidence=f"dispatch_status={dispatch_status}",
                )
            )

    if dead_letter_escalation_report:
        dead_letter_found = bool(dead_letter_escalation_report.get("dead_letter_found", False))
        escalation_status = _safe_str(dead_letter_escalation_report, "escalation_status", "unknown")
        if dead_letter_found and escalation_status != "sent":
            patterns.append(
                FailurePattern(
                    pattern_id="dead_letter_escalation_failed",
                    detected=True,
                    severity=IncidentSeverity.P1,
                    summary="Dead-letter escalation failed",
                    source_artifact="rollback_dead_letter_escalation",
                    evidence=f"escalation_status={escalation_status}",
                )
            )

    return patterns


def highest_severity(patterns: list[FailurePattern]) -> IncidentSeverity | None:
    """Return highest severity among detected patterns."""
    if not patterns:
        return None

    if any(pattern.severity == IncidentSeverity.P1 for pattern in patterns):
        return IncidentSeverity.P1
    if any(pattern.severity == IncidentSeverity.P2 for pattern in patterns):
        return IncidentSeverity.P2
    return IncidentSeverity.P3


def build_recommended_actions(patterns: list[FailurePattern]) -> list[RunbookAction]:
    """Build deterministic action list from detected patterns."""
    if not patterns:
        return [
            RunbookAction(
                step="No immediate remediation required",
                owner="platform-oncall",
                sla_minutes=120,
                command="echo 'No-op: operational status healthy'",
            )
        ]

    actions: list[RunbookAction] = [
        RunbookAction(
            step="Acknowledge incident and open coordination thread",
            owner="platform-oncall",
            sla_minutes=5,
            command="echo 'Acknowledge incident in on-call channel'",
        ),
        RunbookAction(
            step="Collect latest release and health artifacts",
            owner="data-platform",
            sla_minutes=10,
            command="ls artifacts/monitoring artifacts/promotions artifacts/performance",
        ),
    ]

    if any(pattern.pattern_id.startswith("sli_") for pattern in patterns):
        actions.append(
            RunbookAction(
                step="Run targeted production health checks",
                owner="analytics-engineering",
                sla_minutes=15,
                command="make health-checks-strict",
            )
        )

    if any(pattern.pattern_id.startswith("dashboard_") for pattern in patterns):
        actions.append(
            RunbookAction(
                step="Regenerate strict operational dashboard",
                owner="analytics-engineering",
                sla_minutes=15,
                command="make dashboards-strict",
            )
        )

    if any(pattern.pattern_id == "rollback_executed" for pattern in patterns):
        actions.append(
            RunbookAction(
                step="Validate rollback stabilization state",
                owner="release-manager",
                sla_minutes=10,
                command=(
                    "python scripts/ops/execute_rollback_playbook.py "
                    "--rollback-report artifacts/promotions/deployment_rollback.json"
                ),
            )
        )

    if any(pattern.pattern_id == "incident_dispatch_failed" for pattern in patterns):
        actions.append(
            RunbookAction(
                step="Retry incident dispatch with strict mode",
                owner="platform-oncall",
                sla_minutes=5,
                command="make dispatch-rollback-incident",
            )
        )

    if any(pattern.pattern_id == "dead_letter_escalation_failed" for pattern in patterns):
        actions.append(
            RunbookAction(
                step="Retry dead-letter escalation with strict mode",
                owner="platform-oncall",
                sla_minutes=5,
                command="make escalate-rollback-dead-letter",
            )
        )

    actions.append(
        RunbookAction(
            step="Document incident timeline and root-cause hypothesis",
            owner="incident-commander",
            sla_minutes=30,
            command="echo 'Update incident tracker with timeline and owner assignments'",
        )
    )
    return actions


def build_escalation_steps(
    patterns: list[FailurePattern],
    primary_endpoint: str,
    secondary_endpoint: str,
    ticket_queue: str,
) -> list[EscalationStep]:
    """Create escalation routing plan from severity."""
    severity = highest_severity(patterns)
    if severity is None:
        return []

    steps: list[EscalationStep] = [
        EscalationStep(
            severity=severity,
            target=primary_endpoint,
            action="page-primary-oncall",
            trigger_reason=f"highest_severity={severity.value}",
        )
    ]

    if severity == IncidentSeverity.P1:
        steps.append(
            EscalationStep(
                severity=IncidentSeverity.P1,
                target=secondary_endpoint,
                action="page-secondary-oncall",
                trigger_reason="p1 requires secondary acknowledgement",
            )
        )

    steps.append(
        EscalationStep(
            severity=severity,
            target=ticket_queue,
            action="create-incident-ticket",
            trigger_reason="track remediation and postmortem",
        )
    )
    return steps


def generate_oncall_runbook_report(
    health_report: dict[str, Any] | None,
    dashboard_report: dict[str, Any] | None,
    rollback_execution_report: dict[str, Any] | None,
    incident_dispatch_report: dict[str, Any] | None,
    dead_letter_escalation_report: dict[str, Any] | None,
    primary_endpoint: str,
    secondary_endpoint: str,
    ticket_queue: str,
) -> OnCallRunbookReport:
    """Generate full runbook report from available telemetry artifacts."""
    patterns = detect_failure_patterns(
        health_report=health_report,
        dashboard_report=dashboard_report,
        rollback_execution_report=rollback_execution_report,
        incident_dispatch_report=incident_dispatch_report,
        dead_letter_escalation_report=dead_letter_escalation_report,
    )
    severity = highest_severity(patterns)
    actions = build_recommended_actions(patterns)
    escalations = build_escalation_steps(
        patterns=patterns,
        primary_endpoint=primary_endpoint,
        secondary_endpoint=secondary_endpoint,
        ticket_queue=ticket_queue,
    )

    status = "healthy" if not patterns else "incident"
    return OnCallRunbookReport(
        generated_at_utc=_timestamp_utc(),
        overall_status=status,
        incident_required=bool(patterns),
        highest_severity=severity,
        failure_patterns=patterns,
        recommended_actions=actions,
        escalation_steps=escalations,
    )
