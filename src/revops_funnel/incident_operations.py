"""Reliability engineering and incident operations orchestration helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

CONTRACT_VERSION = "phase10.v1"


class IncidentPriority(str, Enum):
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"
    NONE = "none"


@dataclass(frozen=True)
class IncidentOperationsPolicy:
    require_dispatch_sent: bool
    require_escalation_sent: bool
    fatigue_pattern_repeat_threshold: int


@dataclass(frozen=True)
class IncidentOperationsReport:
    contract_version: str
    generated_at_utc: str
    incident_open: bool
    incident_priority: IncidentPriority
    response_readiness: str
    dispatch_status: str
    escalation_status: str
    runbook_quality_passed: bool
    alert_fatigue_score: float
    strict_blockers: list[str]
    command_center_actions: list[str]
    evidence_paths: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["incident_priority"] = self.incident_priority.value
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


def determine_response_readiness(dispatch_status: str, escalation_status: str) -> str:
    if dispatch_status == "sent" and escalation_status in {"sent", "skipped-no-dead-letter"}:
        return "ready"
    if dispatch_status == "skipped" and escalation_status == "skipped-no-dead-letter":
        return "degraded"
    return "at-risk"


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
    policy: IncidentOperationsPolicy,
) -> IncidentOperationsReport:
    incident_open = incident_is_open(health_report, dashboard_report, runbook_report)
    priority = derive_incident_priority(health_report, dashboard_report, runbook_report)

    dispatch_status = _safe_str(dispatch_report, "dispatch_status", "missing")
    escalation_status = _safe_str(escalation_report, "escalation_status", "missing")
    runbook_quality_passed = _safe_bool(runbook_report, "quality_gate_passed", True)
    game_day_due = _safe_bool(runbook_report, "game_day_due", False)

    fatigue_score = compute_alert_fatigue_score(
        runbook_report,
        recent_pattern_ids,
        policy.fatigue_pattern_repeat_threshold,
    )
    readiness = determine_response_readiness(dispatch_status, escalation_status)
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

    return IncidentOperationsReport(
        contract_version=CONTRACT_VERSION,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        incident_open=incident_open,
        incident_priority=priority,
        response_readiness=readiness,
        dispatch_status=dispatch_status,
        escalation_status=escalation_status,
        runbook_quality_passed=runbook_quality_passed,
        alert_fatigue_score=fatigue_score,
        strict_blockers=strict_blockers,
        command_center_actions=actions,
        evidence_paths={
            "health_report": "artifacts/monitoring/health_report.json",
            "dashboard_report": "artifacts/monitoring/operational_dashboard.json",
            "runbook_report": "artifacts/runbooks/oncall_runbook_report.json",
            "dispatch_report": "artifacts/promotions/rollback_incident_dispatch.json",
            "escalation_report": "artifacts/promotions/rollback_dead_letter_escalation.json",
        },
    )
