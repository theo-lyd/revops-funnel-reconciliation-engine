from __future__ import annotations

from revops_funnel.incident_operations import (
    IncidentOperationsPolicy,
    IncidentPriority,
    compute_alert_fatigue_score,
    derive_incident_priority,
    determine_response_readiness,
    generate_incident_operations_report,
    incident_is_open,
)


def test_derive_incident_priority_from_runbook() -> None:
    priority = derive_incident_priority(
        health_report={"overall_status": "healthy"},
        dashboard_report={"operational_status": "healthy"},
        runbook_report={"highest_severity": "p1"},
    )
    assert priority == IncidentPriority.P1


def test_incident_is_open_when_dashboard_degraded() -> None:
    result = incident_is_open(
        health_report={"overall_status": "healthy"},
        dashboard_report={"operational_status": "degraded"},
        runbook_report=None,
    )
    assert result is True


def test_compute_alert_fatigue_score() -> None:
    score = compute_alert_fatigue_score(
        runbook_report={
            "failure_patterns": [
                {"pattern_id": "health_degraded"},
                {"pattern_id": "dashboard_degraded"},
            ]
        },
        recent_pattern_ids=["health_degraded", "health_degraded", "health_degraded"],
        repeat_threshold=3,
    )
    assert score == 0.5


def test_determine_response_readiness_ready() -> None:
    status = determine_response_readiness("sent", "sent")
    assert status == "ready"


def test_generate_incident_operations_report_with_blockers() -> None:
    policy = IncidentOperationsPolicy(
        require_dispatch_sent=True,
        require_escalation_sent=True,
        fatigue_pattern_repeat_threshold=2,
    )
    report = generate_incident_operations_report(
        health_report={"overall_status": "unhealthy"},
        dashboard_report={"operational_status": "critical"},
        runbook_report={
            "incident_required": True,
            "highest_severity": "p1",
            "quality_gate_passed": False,
            "failure_patterns": [{"pattern_id": "health_unhealthy"}],
        },
        dispatch_report={"dispatch_status": "failed"},
        escalation_report={"escalation_status": "failed"},
        recent_pattern_ids=["health_unhealthy", "health_unhealthy"],
        policy=policy,
    )
    payload = report.to_dict()
    assert payload["incident_open"] is True
    assert payload["incident_priority"] == "p1"
    assert "dispatch_status=failed" in payload["strict_blockers"]
    assert "runbook_quality_failed" in payload["strict_blockers"]


def test_generate_incident_operations_report_closed_incident() -> None:
    policy = IncidentOperationsPolicy(
        require_dispatch_sent=True,
        require_escalation_sent=True,
        fatigue_pattern_repeat_threshold=2,
    )
    report = generate_incident_operations_report(
        health_report={"overall_status": "healthy"},
        dashboard_report={"operational_status": "healthy"},
        runbook_report={"incident_required": False, "quality_gate_passed": True},
        dispatch_report={"dispatch_status": "skipped"},
        escalation_report={"escalation_status": "skipped-no-dead-letter"},
        recent_pattern_ids=[],
        policy=policy,
    )
    payload = report.to_dict()
    assert payload["incident_open"] is False
    assert payload["strict_blockers"] == []
