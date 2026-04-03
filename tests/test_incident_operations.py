from __future__ import annotations

from revops_funnel.incident_operations import (
    IncidentOperationsPolicy,
    IncidentPriority,
    IncidentState,
    compute_alert_fatigue_score,
    compute_alert_fatigue_score_v2,
    derive_incident_priority,
    derive_incident_priority_with_confidence,
    determine_response_readiness,
    evaluate_evidence_completeness,
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


def test_compute_alert_fatigue_score_v2_non_zero() -> None:
    score = compute_alert_fatigue_score_v2(
        runbook_report={
            "failure_patterns": [
                {"pattern_id": "health_degraded"},
            ]
        },
        recent_pattern_events=[
            {
                "pattern_id": "health_degraded",
                "timestamp_utc": "2030-01-01T00:00:00+00:00",
            }
        ],
        repeat_threshold=1,
        decay_half_life_hours=24,
    )
    assert score >= 0.0


def test_priority_confidence_and_rationale() -> None:
    priority, confidence, rationale = derive_incident_priority_with_confidence(
        health_report={"overall_status": "unhealthy"},
        dashboard_report={"operational_status": "critical"},
        runbook_report=None,
    )
    assert priority == IncidentPriority.P1
    assert confidence > 0.0
    assert len(rationale) >= 1


def test_evidence_completeness_missing_artifacts() -> None:
    score, missing = evaluate_evidence_completeness(
        health_report=None,
        dashboard_report={"operational_status": "healthy"},
        runbook_report=None,
        dispatch_report=None,
        escalation_report={"escalation_status": "sent"},
    )
    assert score < 1.0
    assert "health_report" in missing


def test_determine_response_readiness_ready() -> None:
    status = determine_response_readiness("sent", "sent")
    assert status == "ready"


def test_generate_incident_operations_report_with_blockers() -> None:
    policy = IncidentOperationsPolicy(
        require_dispatch_sent=True,
        require_escalation_sent=True,
        fatigue_pattern_repeat_threshold=2,
        fatigue_decay_half_life_hours=24.0,
        min_evidence_completeness=0.8,
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
        recent_pattern_events=[],
        policy=policy,
    )
    payload = report.to_dict()
    assert payload["incident_open"] is True
    assert payload["incident_priority"] == "p1"
    assert payload["incident_state"] in {
        IncidentState.DETECTED.value,
        IncidentState.ACKNOWLEDGED.value,
    }
    assert "incident_priority_confidence" in payload
    assert "incident_priority_rationale" in payload
    assert "evidence_completeness_score" in payload
    assert "alert_fatigue_score_v2" in payload
    assert "correlation_id" in payload
    assert "role_action_templates" in payload
    assert "remediation_latency_kpis" in payload
    assert "dispatch_status=failed" in payload["strict_blockers"]
    assert "runbook_quality_failed" in payload["strict_blockers"]


def test_contract_compatibility_old_fields_still_present() -> None:
    policy = IncidentOperationsPolicy(
        require_dispatch_sent=False,
        require_escalation_sent=False,
        fatigue_pattern_repeat_threshold=3,
    )
    report = generate_incident_operations_report(
        health_report={"overall_status": "healthy"},
        dashboard_report={"operational_status": "healthy"},
        runbook_report={"incident_required": False, "quality_gate_passed": True},
        dispatch_report={"dispatch_status": "sent"},
        escalation_report={"escalation_status": "sent"},
        recent_pattern_ids=[],
        recent_pattern_events=[],
        policy=policy,
    )
    payload = report.to_dict()
    # Backward compatibility fields from v1
    assert "incident_open" in payload
    assert "incident_priority" in payload
    assert "response_readiness" in payload
    assert "dispatch_status" in payload
    assert "escalation_status" in payload
    assert "strict_blockers" in payload
    assert "command_center_actions" in payload


def test_generate_incident_operations_report_closed_incident() -> None:
    policy = IncidentOperationsPolicy(
        require_dispatch_sent=True,
        require_escalation_sent=True,
        fatigue_pattern_repeat_threshold=2,
        fatigue_decay_half_life_hours=24.0,
        min_evidence_completeness=0.8,
    )
    report = generate_incident_operations_report(
        health_report={"overall_status": "healthy"},
        dashboard_report={"operational_status": "healthy"},
        runbook_report={"incident_required": False, "quality_gate_passed": True},
        dispatch_report={"dispatch_status": "skipped"},
        escalation_report={"escalation_status": "skipped-no-dead-letter"},
        recent_pattern_ids=[],
        recent_pattern_events=[],
        policy=policy,
    )
    payload = report.to_dict()
    assert payload["incident_open"] is False
    assert payload["incident_state"] in {
        IncidentState.RESOLVED.value,
        IncidentState.POSTMORTEM_DUE.value,
    }
    assert payload["strict_blockers"] == []
