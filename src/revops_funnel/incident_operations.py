"""Reliability engineering and incident operations orchestration helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import NAMESPACE_DNS, uuid5

CONTRACT_VERSION = "phase10.v2"
POLICY_CONTRACT_VERSION = "phase10.policy.v1"


class IncidentPriority(str, Enum):
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"
    NONE = "none"


class IncidentState(str, Enum):
    DETECTED = "detected"
    ACKNOWLEDGED = "acknowledged"
    MITIGATED = "mitigated"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    POSTMORTEM_DUE = "postmortem_due"


@dataclass(frozen=True)
class IncidentOperationsPolicy:
    require_dispatch_sent: bool
    require_escalation_sent: bool
    fatigue_pattern_repeat_threshold: int
    fatigue_decay_half_life_hours: float = 24.0
    min_evidence_completeness: float = 0.8
    policy_contract_version: str = POLICY_CONTRACT_VERSION


@dataclass(frozen=True)
class IncidentOperationsReport:
    contract_version: str
    generated_at_utc: str
    incident_open: bool
    incident_priority: IncidentPriority
    incident_state: IncidentState
    incident_priority_confidence: float
    incident_priority_rationale: list[str]
    response_readiness: str
    dispatch_status: str
    escalation_status: str
    runbook_quality_passed: bool
    alert_fatigue_score: float
    alert_fatigue_score_v2: float
    evidence_completeness_score: float
    missing_evidence_artifacts: list[str]
    strict_blockers: list[str]
    strict_enforcement_suppressed: bool
    command_center_actions: list[str]
    role_action_templates: list[dict[str, Any]]
    remediation_latency_kpis: dict[str, float | None]
    correlation_id: str
    correlation_source: str
    evidence_paths: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["incident_priority"] = self.incident_priority.value
        payload["incident_state"] = self.incident_state.value
        return payload


def _safe_str(payload: dict[str, Any] | None, key: str, default: str = "") -> str:
    if not payload:
        return default
    value = payload.get(key, default)
    return str(value) if value is not None else default


def _safe_bool(payload: dict[str, Any] | None, key: str, default: bool = False) -> bool:
    if not payload:
        return default
    value = payload.get(key, default)
    return bool(value)


def derive_incident_priority(
    health_report: dict[str, Any] | None,
    dashboard_report: dict[str, Any] | None,
    runbook_report: dict[str, Any] | None,
) -> IncidentPriority:
    runbook_priority = _safe_str(runbook_report, "highest_severity", "")
    if runbook_priority in {"p1", "p2", "p3"}:
        return IncidentPriority(runbook_priority)

    health_status = _safe_str(health_report, "overall_status", "")
    dashboard_status = _safe_str(dashboard_report, "operational_status", "")
    if health_status == "unhealthy" or dashboard_status == "critical":
        return IncidentPriority.P1
    if health_status == "degraded" or dashboard_status == "degraded":
        return IncidentPriority.P2
    return IncidentPriority.NONE


def derive_incident_priority_with_confidence(
    health_report: dict[str, Any] | None,
    dashboard_report: dict[str, Any] | None,
    runbook_report: dict[str, Any] | None,
) -> tuple[IncidentPriority, float, list[str]]:
    rationale: list[str] = []

    runbook_priority = _safe_str(runbook_report, "highest_severity", "")
    if runbook_priority in {"p1", "p2", "p3"}:
        rationale.append(f"runbook_highest_severity={runbook_priority}")
        return IncidentPriority(runbook_priority), 0.95, rationale

    health_status = _safe_str(health_report, "overall_status", "unknown")
    dashboard_status = _safe_str(dashboard_report, "operational_status", "unknown")

    if health_status == "unhealthy":
        rationale.append("health_unhealthy")
    elif health_status == "degraded":
        rationale.append("health_degraded")

    if dashboard_status == "critical":
        rationale.append("dashboard_critical")
    elif dashboard_status == "degraded":
        rationale.append("dashboard_degraded")

    priority = derive_incident_priority(health_report, dashboard_report, runbook_report)
    if priority == IncidentPriority.P1:
        confidence = 0.85 if len(rationale) > 1 else 0.72
    elif priority == IncidentPriority.P2:
        confidence = 0.7 if len(rationale) > 1 else 0.58
    else:
        confidence = 0.9
        rationale.append("no_severity_signals")

    return priority, round(confidence, 3), rationale


def incident_is_open(
    health_report: dict[str, Any] | None,
    dashboard_report: dict[str, Any] | None,
    runbook_report: dict[str, Any] | None,
) -> bool:
    if _safe_bool(runbook_report, "incident_required", False):
        return True

    health_status = _safe_str(health_report, "overall_status", "")
    dashboard_status = _safe_str(dashboard_report, "operational_status", "")
    return health_status in {"degraded", "unhealthy"} or dashboard_status in {
        "degraded",
        "critical",
    }


def compute_alert_fatigue_score(
    runbook_report: dict[str, Any] | None,
    recent_pattern_ids: list[str],
    repeat_threshold: int,
) -> float:
    patterns = []
    if runbook_report and isinstance(runbook_report.get("failure_patterns"), list):
        for item in runbook_report["failure_patterns"]:
            if isinstance(item, dict):
                pattern_id = item.get("pattern_id")
                if pattern_id:
                    patterns.append(str(pattern_id))

    if not patterns:
        return 0.0

    threshold = max(1, repeat_threshold)
    repeated = 0
    for pattern_id in patterns:
        occurrences = sum(1 for value in recent_pattern_ids if value == pattern_id)
        if occurrences >= threshold:
            repeated += 1

    return round(repeated / len(patterns), 3)


def compute_alert_fatigue_score_v2(
    runbook_report: dict[str, Any] | None,
    recent_pattern_events: list[dict[str, Any]],
    repeat_threshold: int,
    decay_half_life_hours: float,
) -> float:
    patterns: list[str] = []
    if runbook_report and isinstance(runbook_report.get("failure_patterns"), list):
        for item in runbook_report["failure_patterns"]:
            if isinstance(item, dict):
                pattern_id = item.get("pattern_id")
                if pattern_id:
                    patterns.append(str(pattern_id))

    if not patterns:
        return 0.0

    half_life = max(decay_half_life_hours, 1.0)
    now = datetime.now(timezone.utc)
    threshold = max(1, repeat_threshold)

    weighted_repeated = 0.0
    for pattern_id in patterns:
        weighted_occurrences = 0.0
        for event in recent_pattern_events:
            if not isinstance(event, dict):
                continue
            if str(event.get("pattern_id", "")) != pattern_id:
                continue

            timestamp_raw = str(event.get("timestamp_utc", ""))
            try:
                ts = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))
                age_hours = max((now - ts).total_seconds() / 3600.0, 0.0)
                weight = 0.5 ** (age_hours / half_life)
            except ValueError:
                weight = 1.0
            weighted_occurrences += weight

        if weighted_occurrences >= threshold:
            weighted_repeated += 1.0

    return round(weighted_repeated / len(patterns), 3)


def evaluate_evidence_completeness(
    health_report: dict[str, Any] | None,
    dashboard_report: dict[str, Any] | None,
    runbook_report: dict[str, Any] | None,
    dispatch_report: dict[str, Any] | None,
    escalation_report: dict[str, Any] | None,
) -> tuple[float, list[str]]:
    checks: list[tuple[str, bool]] = [
        ("health_report", health_report is not None),
        ("dashboard_report", dashboard_report is not None),
        ("runbook_report", runbook_report is not None),
        ("dispatch_report", dispatch_report is not None),
        ("escalation_report", escalation_report is not None),
    ]
    present = sum(1 for _, ok in checks if ok)
    missing = [name for name, ok in checks if not ok]
    score = present / len(checks)
    return round(score, 3), missing


def determine_response_readiness(dispatch_status: str, escalation_status: str) -> str:
    if dispatch_status == "sent" and escalation_status in {"sent", "skipped-no-dead-letter"}:
        return "ready"
    if dispatch_status == "skipped" and escalation_status == "skipped-no-dead-letter":
        return "degraded"
    return "at-risk"


def derive_incident_state(
    incident_open: bool,
    response_readiness: str,
    health_report: dict[str, Any] | None,
    dashboard_report: dict[str, Any] | None,
    runbook_report: dict[str, Any] | None,
    dispatch_status: str,
) -> IncidentState:
    if not incident_open:
        had_patterns = bool((runbook_report or {}).get("failure_patterns"))
        if had_patterns:
            return IncidentState.POSTMORTEM_DUE
        return IncidentState.RESOLVED

    health_status = _safe_str(health_report, "overall_status", "unknown")
    dashboard_status = _safe_str(dashboard_report, "operational_status", "unknown")

    if response_readiness == "at-risk":
        return IncidentState.DETECTED
    if health_status == "unhealthy" or dashboard_status == "critical":
        if dispatch_status == "sent":
            return IncidentState.ACKNOWLEDGED
        return IncidentState.DETECTED
    if health_status == "degraded" or dashboard_status == "degraded":
        return IncidentState.MITIGATED
    return IncidentState.MONITORING


def _parse_timeline_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def compute_remediation_latency_kpis(
    runbook_report: dict[str, Any] | None,
) -> dict[str, float | None]:
    timeline = runbook_report.get("incident_timeline", []) if runbook_report else []
    if not isinstance(timeline, list):
        timeline = []

    detected_at: datetime | None = None
    acknowledged_at: datetime | None = None
    mitigated_at: datetime | None = None

    for event in timeline:
        if not isinstance(event, dict):
            continue

        event_type = str(event.get("event_type", "")).lower()
        summary = str(event.get("summary", "")).lower()
        ts = _parse_timeline_time(str(event.get("timestamp_utc", "")))
        if ts is None:
            continue

        if detected_at is None and event_type in {"pattern_detected", "health_signal"}:
            detected_at = ts

        if acknowledged_at is None and "acknowledge incident" in summary:
            acknowledged_at = ts

        if mitigated_at is None and (
            "validate rollback stabilization" in summary
            or "regenerate strict operational dashboard" in summary
            or "run targeted production health checks" in summary
            or "retry" in summary
        ):
            mitigated_at = ts

    detection_to_ack = None
    detection_to_mitigation = None
    if detected_at and acknowledged_at and acknowledged_at >= detected_at:
        detection_to_ack = round((acknowledged_at - detected_at).total_seconds() / 60.0, 3)
    if detected_at and mitigated_at and mitigated_at >= detected_at:
        detection_to_mitigation = round((mitigated_at - detected_at).total_seconds() / 60.0, 3)

    return {
        "detection_to_ack_minutes": detection_to_ack,
        "detection_to_mitigation_minutes": detection_to_mitigation,
    }


def resolve_correlation(
    runbook_report: dict[str, Any] | None,
    explicit_correlation_id: str | None,
    incident_priority: IncidentPriority,
    incident_state: IncidentState,
    dispatch_status: str,
    escalation_status: str,
) -> tuple[str, str]:
    if explicit_correlation_id:
        return explicit_correlation_id, "explicit"

    runbook_correlation = _safe_str(runbook_report, "correlation_id", "")
    if runbook_correlation:
        return runbook_correlation, "runbook"

    fingerprint = (
        f"{incident_priority.value}:{incident_state.value}:{dispatch_status}:{escalation_status}:"
        f"{_safe_str(runbook_report, 'generated_at_utc', '')}"
    )
    return str(uuid5(NAMESPACE_DNS, fingerprint)), "generated"


def build_role_action_templates(
    incident_priority: IncidentPriority,
    response_readiness: str,
) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = [
        {
            "role": "incident_commander",
            "sla_minutes": 5,
            "action": "Acknowledge incident and publish status cadence.",
            "when": "incident_open",
        },
        {
            "role": "platform_oncall",
            "sla_minutes": 10,
            "action": "Verify dispatch/escalation delivery and webhook health.",
            "when": "incident_open",
        },
        {
            "role": "analytics_engineering",
            "sla_minutes": 15,
            "action": "Re-run strict health checks and dashboard regeneration.",
            "when": "incident_open",
        },
    ]

    if incident_priority == IncidentPriority.P1:
        templates.append(
            {
                "role": "release_manager",
                "sla_minutes": 10,
                "action": "Prepare rollback stabilization validation and decision log.",
                "when": "priority_p1",
            }
        )

    if response_readiness == "at-risk":
        templates.append(
            {
                "role": "platform_oncall",
                "sla_minutes": 5,
                "action": "Activate manual paging fallback and incident ticket creation.",
                "when": "readiness_at_risk",
            }
        )

    return templates


def build_command_center_actions(
    incident_open: bool,
    incident_priority: IncidentPriority,
    response_readiness: str,
    fatigue_score: float,
    game_day_due: bool,
) -> list[str]:
    if not incident_open:
        actions = ["No incident currently open; continue routine observability review."]
        if game_day_due:
            actions.append("Schedule next reliability game-day exercise.")
        return actions

    actions = [
        "Open incident bridge and assign incident commander.",
        "Pin latest health, dashboard, runbook, and rollback artifacts in incident channel.",
    ]

    if incident_priority == IncidentPriority.P1:
        actions.append("Page primary and secondary responders and start 15-minute status cadence.")

    if response_readiness == "at-risk":
        actions.append("Trigger manual escalation path because automation delivery is at risk.")

    if fatigue_score >= 0.5:
        actions.append(
            "Apply alert-noise suppression and rotate triage ownership to reduce fatigue."
        )

    if game_day_due:
        actions.append("Book a post-incident game-day follow-up within current sprint.")

    actions.append("Capture timeline checkpoints for postmortem and reliability scorecard.")
    return actions


def evaluate_strict_blockers(
    policy: IncidentOperationsPolicy,
    incident_open: bool,
    dispatch_status: str,
    escalation_status: str,
    runbook_quality_passed: bool,
) -> list[str]:
    blockers: list[str] = []
    if not incident_open:
        return blockers

    if policy.require_dispatch_sent and dispatch_status != "sent":
        blockers.append(f"dispatch_status={dispatch_status}")

    if policy.require_escalation_sent and escalation_status not in {
        "sent",
        "skipped-no-dead-letter",
    }:
        blockers.append(f"escalation_status={escalation_status}")

    if not runbook_quality_passed:
        blockers.append("runbook_quality_failed")

    return blockers


def generate_incident_operations_report(
    health_report: dict[str, Any] | None,
    dashboard_report: dict[str, Any] | None,
    runbook_report: dict[str, Any] | None,
    dispatch_report: dict[str, Any] | None,
    escalation_report: dict[str, Any] | None,
    recent_pattern_ids: list[str],
    recent_pattern_events: list[dict[str, Any]] | None,
    policy: IncidentOperationsPolicy,
    explicit_correlation_id: str | None = None,
    strict_enforcement_suppressed: bool = False,
) -> IncidentOperationsReport:
    incident_open = incident_is_open(health_report, dashboard_report, runbook_report)
    priority, confidence, rationale = derive_incident_priority_with_confidence(
        health_report,
        dashboard_report,
        runbook_report,
    )

    evidence_score, missing_artifacts = evaluate_evidence_completeness(
        health_report,
        dashboard_report,
        runbook_report,
        dispatch_report,
        escalation_report,
    )
    dispatch_status = _safe_str(dispatch_report, "dispatch_status", "missing")
    escalation_status = _safe_str(escalation_report, "escalation_status", "missing")
    runbook_quality_passed = _safe_bool(runbook_report, "quality_gate_passed", True)
    game_day_due = _safe_bool(runbook_report, "game_day_due", False)

    fatigue_score = compute_alert_fatigue_score(
        runbook_report,
        recent_pattern_ids,
        policy.fatigue_pattern_repeat_threshold,
    )
    fatigue_score_v2 = compute_alert_fatigue_score_v2(
        runbook_report,
        recent_pattern_events or [],
        policy.fatigue_pattern_repeat_threshold,
        policy.fatigue_decay_half_life_hours,
    )
    readiness = determine_response_readiness(dispatch_status, escalation_status)

    state = derive_incident_state(
        incident_open=incident_open,
        response_readiness=readiness,
        health_report=health_report,
        dashboard_report=dashboard_report,
        runbook_report=runbook_report,
        dispatch_status=dispatch_status,
    )

    correlation_id, correlation_source = resolve_correlation(
        runbook_report=runbook_report,
        explicit_correlation_id=explicit_correlation_id,
        incident_priority=priority,
        incident_state=state,
        dispatch_status=dispatch_status,
        escalation_status=escalation_status,
    )

    strict_blockers = evaluate_strict_blockers(
        policy=policy,
        incident_open=incident_open,
        dispatch_status=dispatch_status,
        escalation_status=escalation_status,
        runbook_quality_passed=runbook_quality_passed,
    )

    actions = build_command_center_actions(
        incident_open=incident_open,
        incident_priority=priority,
        response_readiness=readiness,
        fatigue_score=fatigue_score,
        game_day_due=game_day_due,
    )
    role_action_templates = build_role_action_templates(priority, readiness)
    remediation_kpis = compute_remediation_latency_kpis(runbook_report)

    return IncidentOperationsReport(
        contract_version=CONTRACT_VERSION,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        incident_open=incident_open,
        incident_priority=priority,
        incident_state=state,
        incident_priority_confidence=confidence,
        incident_priority_rationale=rationale,
        response_readiness=readiness,
        dispatch_status=dispatch_status,
        escalation_status=escalation_status,
        runbook_quality_passed=runbook_quality_passed,
        alert_fatigue_score=fatigue_score,
        alert_fatigue_score_v2=fatigue_score_v2,
        evidence_completeness_score=evidence_score,
        missing_evidence_artifacts=missing_artifacts,
        strict_blockers=strict_blockers,
        strict_enforcement_suppressed=strict_enforcement_suppressed,
        command_center_actions=actions,
        role_action_templates=role_action_templates,
        remediation_latency_kpis=remediation_kpis,
        correlation_id=correlation_id,
        correlation_source=correlation_source,
        evidence_paths={
            "health_report": "artifacts/monitoring/health_report.json",
            "dashboard_report": "artifacts/monitoring/operational_dashboard.json",
            "runbook_report": "artifacts/runbooks/oncall_runbook_report.json",
            "dispatch_report": "artifacts/promotions/rollback_incident_dispatch.json",
            "escalation_report": "artifacts/promotions/rollback_dead_letter_escalation.json",
        },
    )
