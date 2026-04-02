"""On-call runbook generation from operational failure artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

OBSERVABILITY_CONTRACT_VERSION = "2.0"


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
    runbook_quality_score: float
    quality_gate_passed: bool
    incident_timeline: list[dict[str, str]]
    game_day_due: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": OBSERVABILITY_CONTRACT_VERSION,
            "generated_at_utc": self.generated_at_utc,
            "overall_status": self.overall_status,
            "incident_required": self.incident_required,
            "highest_severity": (
                self.highest_severity.value if self.highest_severity is not None else None
            ),
            "failure_patterns": [pattern.to_dict() for pattern in self.failure_patterns],
            "recommended_actions": [asdict(action) for action in self.recommended_actions],
            "escalation_steps": [step.to_dict() for step in self.escalation_steps],
            "runbook_quality_score": self.runbook_quality_score,
            "quality_gate_passed": self.quality_gate_passed,
            "incident_timeline": self.incident_timeline,
            "game_day_due": self.game_day_due,
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


def dedupe_failure_patterns(patterns: list[FailurePattern]) -> list[FailurePattern]:
    """Collapse duplicated pattern ids to reduce alert storms."""
    deduped: dict[str, FailurePattern] = {}
    for pattern in patterns:
        deduped.setdefault(pattern.pattern_id, pattern)
    return list(deduped.values())


def suppress_flapping_patterns(
    patterns: list[FailurePattern],
    recent_pattern_ids: list[str] | None,
    flap_threshold: int,
) -> list[FailurePattern]:
    """Suppress patterns that repeatedly reappear across recent windows."""
    if not recent_pattern_ids or flap_threshold <= 1:
        return patterns

    counts: dict[str, int] = {}
    for pattern_id in recent_pattern_ids:
        counts[pattern_id] = counts.get(pattern_id, 0) + 1

    filtered: list[FailurePattern] = []
    for pattern in patterns:
        if counts.get(pattern.pattern_id, 0) >= flap_threshold:
            continue
        filtered.append(pattern)
    return filtered


def apply_multi_signal_severity(
    patterns: list[FailurePattern],
    health_report: dict[str, Any] | None,
    dashboard_report: dict[str, Any] | None,
) -> list[FailurePattern]:
    """Promote severity when multiple independent signals confirm impact."""
    if not patterns:
        return patterns

    health_status = _safe_str(health_report or {}, "overall_status", "unknown")
    dashboard_status = _safe_str(dashboard_report or {}, "operational_status", "unknown")
    multi_signal = health_status in {"degraded", "unhealthy"} and dashboard_status in {
        "degraded",
        "critical",
    }
    if not multi_signal:
        return patterns

    promoted: list[FailurePattern] = []
    for pattern in patterns:
        if pattern.severity == IncidentSeverity.P2:
            promoted.append(
                FailurePattern(
                    pattern_id=pattern.pattern_id,
                    detected=pattern.detected,
                    severity=IncidentSeverity.P1,
                    summary=f"[multi-signal] {pattern.summary}",
                    source_artifact=pattern.source_artifact,
                    evidence=pattern.evidence,
                )
            )
        else:
            promoted.append(pattern)
    return promoted


def apply_dependency_aware_severity(
    patterns: list[FailurePattern], dependency_impact: dict[str, Any] | None
) -> list[FailurePattern]:
    """Escalate severity when blast radius is high."""
    if not patterns:
        return patterns

    blast_radius = _safe_str(dependency_impact or {}, "blast_radius", "none")
    if blast_radius != "high":
        return patterns

    adjusted: list[FailurePattern] = []
    for pattern in patterns:
        if pattern.severity in {IncidentSeverity.P2, IncidentSeverity.P3}:
            adjusted.append(
                FailurePattern(
                    pattern_id=pattern.pattern_id,
                    detected=pattern.detected,
                    severity=IncidentSeverity.P1,
                    summary=f"[high-blast-radius] {pattern.summary}",
                    source_artifact=pattern.source_artifact,
                    evidence=pattern.evidence,
                )
            )
        else:
            adjusted.append(pattern)
    return adjusted


def score_runbook_quality(
    patterns: list[FailurePattern],
    actions: list[RunbookAction],
    escalation_steps: list[EscalationStep],
) -> float:
    """Score runbook quality for strict release gating."""
    score = 1.0

    if patterns and len(actions) < 3:
        score -= 0.35
    if (
        any(pattern.severity == IncidentSeverity.P1 for pattern in patterns)
        and not escalation_steps
    ):
        score -= 0.4
    if patterns and not any("timeline" in action.step.lower() for action in actions):
        score -= 0.15

    return round(max(score, 0.0), 3)


def build_incident_timeline(
    generated_at_utc: str,
    patterns: list[FailurePattern],
    actions: list[RunbookAction],
) -> list[dict[str, str]]:
    """Construct a deterministic timeline for post-incident reconstruction."""
    timeline: list[dict[str, str]] = []
    for pattern in patterns:
        timeline.append(
            {
                "timestamp_utc": generated_at_utc,
                "source": pattern.source_artifact,
                "event_type": "pattern_detected",
                "severity": pattern.severity.value,
                "summary": pattern.summary,
            }
        )

    for action in actions:
        timeline.append(
            {
                "timestamp_utc": generated_at_utc,
                "source": "runbook",
                "event_type": "action_recommended",
                "severity": "info",
                "summary": action.step,
            }
        )
    return timeline


def is_game_day_due(last_game_day_utc: str | None, cadence_days: int) -> bool:
    """Return whether the next resilience game-day exercise is due."""
    if cadence_days <= 0:
        return False
    if not last_game_day_utc:
        return True
    try:
        last_game_day = datetime.fromisoformat(last_game_day_utc.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return True
    return (datetime.now(timezone.utc) - last_game_day).days >= cadence_days


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
    recent_pattern_ids: list[str] | None = None,
    flap_threshold: int = 3,
    strict_quality_threshold: float = 0.8,
    dependency_impact: dict[str, Any] | None = None,
    last_game_day_utc: str | None = None,
    game_day_cadence_days: int = 30,
) -> OnCallRunbookReport:
    """Generate full runbook report from available telemetry artifacts."""
    patterns = detect_failure_patterns(
        health_report=health_report,
        dashboard_report=dashboard_report,
        rollback_execution_report=rollback_execution_report,
        incident_dispatch_report=incident_dispatch_report,
        dead_letter_escalation_report=dead_letter_escalation_report,
    )
    patterns = dedupe_failure_patterns(patterns)
    patterns = suppress_flapping_patterns(patterns, recent_pattern_ids, flap_threshold)
    patterns = apply_multi_signal_severity(patterns, health_report, dashboard_report)
    patterns = apply_dependency_aware_severity(patterns, dependency_impact)

    severity = highest_severity(patterns)
    actions = build_recommended_actions(patterns)
    escalations = build_escalation_steps(
        patterns=patterns,
        primary_endpoint=primary_endpoint,
        secondary_endpoint=secondary_endpoint,
        ticket_queue=ticket_queue,
    )
    quality_score = score_runbook_quality(patterns, actions, escalations)
    quality_gate_passed = quality_score >= strict_quality_threshold
    now = _timestamp_utc()
    timeline = build_incident_timeline(now, patterns, actions)
    game_day_due = is_game_day_due(last_game_day_utc, game_day_cadence_days)

    status = "healthy" if not patterns else "incident"
    return OnCallRunbookReport(
        generated_at_utc=now,
        overall_status=status,
        incident_required=bool(patterns),
        highest_severity=severity,
        failure_patterns=patterns,
        recommended_actions=actions,
        escalation_steps=escalations,
        runbook_quality_score=quality_score,
        quality_gate_passed=quality_gate_passed,
        incident_timeline=timeline,
        game_day_due=game_day_due,
    )
