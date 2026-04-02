from __future__ import annotations

from revops_funnel.oncall_runbooks import (
    IncidentSeverity,
    build_escalation_steps,
    build_recommended_actions,
    detect_failure_patterns,
    generate_oncall_runbook_report,
    highest_severity,
)


def test_detect_failure_patterns_from_health_and_dashboard() -> None:
    health_report = {"overall_status": "degraded"}
    dashboard_report = {
        "operational_status": "critical",
        "sli_metrics": [
            {
                "name": "transformation_latency",
                "status": "unhealthy",
                "current_value": 220,
                "slo_threshold": 120,
            }
        ],
    }

    patterns = detect_failure_patterns(
        health_report=health_report,
        dashboard_report=dashboard_report,
        rollback_execution_report=None,
        incident_dispatch_report=None,
        dead_letter_escalation_report=None,
    )

    pattern_ids = {pattern.pattern_id for pattern in patterns}
    assert "health_degraded" in pattern_ids
    assert "dashboard_critical" in pattern_ids
    assert "sli_unhealthy_transformation_latency" in pattern_ids


def test_detect_failure_patterns_for_failed_dispatch_and_escalation() -> None:
    patterns = detect_failure_patterns(
        health_report=None,
        dashboard_report=None,
        rollback_execution_report=None,
        incident_dispatch_report={
            "incident_webhook_configured": True,
            "dispatch_status": "failed",
        },
        dead_letter_escalation_report={
            "dead_letter_found": True,
            "escalation_status": "failed",
        },
    )

    pattern_ids = {pattern.pattern_id for pattern in patterns}
    assert "incident_dispatch_failed" in pattern_ids
    assert "dead_letter_escalation_failed" in pattern_ids


def test_highest_severity_returns_p1_when_present() -> None:
    patterns = detect_failure_patterns(
        health_report={"overall_status": "degraded"},
        dashboard_report={"operational_status": "critical", "sli_metrics": []},
        rollback_execution_report=None,
        incident_dispatch_report=None,
        dead_letter_escalation_report=None,
    )
    assert highest_severity(patterns) == IncidentSeverity.P1


def test_build_recommended_actions_includes_health_commands() -> None:
    patterns = detect_failure_patterns(
        health_report={"overall_status": "unhealthy"},
        dashboard_report={
            "operational_status": "degraded",
            "sli_metrics": [
                {
                    "name": "cost_per_record",
                    "status": "degraded",
                    "current_value": 0.002,
                    "slo_threshold": 0.001,
                }
            ],
        },
        rollback_execution_report=None,
        incident_dispatch_report=None,
        dead_letter_escalation_report=None,
    )

    actions = build_recommended_actions(patterns)
    commands = {action.command for action in actions}
    assert "make health-checks-strict" in commands
    assert "make dashboards-strict" in commands


def test_build_escalation_steps_includes_secondary_for_p1() -> None:
    patterns = detect_failure_patterns(
        health_report={"overall_status": "unhealthy"},
        dashboard_report=None,
        rollback_execution_report=None,
        incident_dispatch_report=None,
        dead_letter_escalation_report=None,
    )

    steps = build_escalation_steps(
        patterns=patterns,
        primary_endpoint="oncall-primary",
        secondary_endpoint="oncall-secondary",
        ticket_queue="revops-queue",
    )

    assert len(steps) == 3
    assert steps[0].target == "oncall-primary"
    assert steps[1].target == "oncall-secondary"


def test_generate_oncall_runbook_report_healthy_defaults() -> None:
    report = generate_oncall_runbook_report(
        health_report={"overall_status": "healthy"},
        dashboard_report={"operational_status": "healthy", "sli_metrics": []},
        rollback_execution_report=None,
        incident_dispatch_report=None,
        dead_letter_escalation_report=None,
        primary_endpoint="oncall-primary",
        secondary_endpoint="oncall-secondary",
        ticket_queue="revops-queue",
    )

    assert report.overall_status == "healthy"
    assert report.incident_required is False
    assert report.highest_severity is None
    assert len(report.failure_patterns) == 0


def test_generate_oncall_runbook_report_incident() -> None:
    report = generate_oncall_runbook_report(
        health_report={"overall_status": "unhealthy"},
        dashboard_report={"operational_status": "critical", "sli_metrics": []},
        rollback_execution_report={"execution_mode": "controlled", "execution_enabled": True},
        incident_dispatch_report={"incident_webhook_configured": True, "dispatch_status": "failed"},
        dead_letter_escalation_report={"dead_letter_found": True, "escalation_status": "failed"},
        primary_endpoint="oncall-primary",
        secondary_endpoint="oncall-secondary",
        ticket_queue="revops-queue",
    )

    assert report.overall_status == "incident"
    assert report.incident_required is True
    assert report.highest_severity == IncidentSeverity.P1
    assert len(report.failure_patterns) >= 4
    assert len(report.escalation_steps) >= 2


def test_report_serialization_converts_enum_values() -> None:
    report = generate_oncall_runbook_report(
        health_report={"overall_status": "unhealthy"},
        dashboard_report=None,
        rollback_execution_report=None,
        incident_dispatch_report=None,
        dead_letter_escalation_report=None,
        primary_endpoint="oncall-primary",
        secondary_endpoint="oncall-secondary",
        ticket_queue="revops-queue",
    )

    payload = report.to_dict()
    assert payload["highest_severity"] == "p1"
    assert payload["failure_patterns"][0]["severity"] == "p1"
