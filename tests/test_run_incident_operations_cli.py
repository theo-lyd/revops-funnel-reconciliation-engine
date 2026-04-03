from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_run_incident_operations_cli_safe_mode(tmp_path: Path) -> None:
    output_path = tmp_path / "incident_operations.json"
    runbook_path = tmp_path / "runbook.json"
    runbook_path.write_text(
        json.dumps(
            {
                "incident_required": True,
                "highest_severity": "p1",
                "quality_gate_passed": True,
                "failure_patterns": [{"pattern_id": "health_unhealthy"}],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ops/run_incident_operations.py",
            f"--runbook-report={runbook_path}",
            f"--output={output_path}",
        ],
        cwd="/workspaces/revops-funnel-reconciliation-engine",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["contract_version"] == "phase10.v2"
    assert payload["incident_open"] is True
    assert "incident_priority" in payload
    assert "incident_state" in payload
    assert "command_center_actions" in payload


def test_run_incident_operations_cli_policy_file(tmp_path: Path) -> None:
    output_path = tmp_path / "incident_operations.json"
    runbook_path = tmp_path / "runbook.json"
    policy_path = tmp_path / "policy.json"

    runbook_path.write_text(
        json.dumps(
            {
                "incident_required": True,
                "highest_severity": "p1",
                "quality_gate_passed": True,
                "failure_patterns": [{"pattern_id": "health_unhealthy"}],
            }
        ),
        encoding="utf-8",
    )
    policy_path.write_text(
        json.dumps(
            {
                "contract_version": "phase10.policy.v1",
                "require_dispatch_sent": True,
                "require_escalation_sent": True,
                "fatigue_pattern_repeat_threshold": 2,
                "fatigue_decay_half_life_hours": 12,
                "min_evidence_completeness": 0.8,
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ops/run_incident_operations.py",
            f"--runbook-report={runbook_path}",
            f"--policy={policy_path}",
            f"--output={output_path}",
        ],
        cwd="/workspaces/revops-funnel-reconciliation-engine",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["policy_source"] == "file"


def test_run_incident_operations_cli_strict_fails(tmp_path: Path) -> None:
    output_path = tmp_path / "incident_operations.json"
    health_path = tmp_path / "health.json"
    dashboard_path = tmp_path / "dashboard.json"
    runbook_path = tmp_path / "runbook.json"
    dispatch_path = tmp_path / "dispatch.json"
    escalation_path = tmp_path / "escalation.json"

    health_path.write_text(json.dumps({"overall_status": "unhealthy"}), encoding="utf-8")
    dashboard_path.write_text(
        json.dumps({"operational_status": "critical", "sli_metrics": []}),
        encoding="utf-8",
    )

    runbook_path.write_text(
        json.dumps(
            {
                "incident_required": True,
                "highest_severity": "p1",
                "quality_gate_passed": False,
                "failure_patterns": [{"pattern_id": "health_unhealthy"}],
            }
        ),
        encoding="utf-8",
    )
    dispatch_path.write_text(json.dumps({"dispatch_status": "failed"}), encoding="utf-8")
    escalation_path.write_text(json.dumps({"escalation_status": "failed"}), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ops/run_incident_operations.py",
            f"--health-report={health_path}",
            f"--dashboard-report={dashboard_path}",
            f"--runbook-report={runbook_path}",
            f"--dispatch-report={dispatch_path}",
            f"--escalation-report={escalation_path}",
            "--strict-operations",
            "--require-dispatch-sent",
            "--require-escalation-sent",
            f"--output={output_path}",
        ],
        cwd="/workspaces/revops-funnel-reconciliation-engine",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "strict incident operations blockers" in result.stdout.lower()


def test_run_incident_operations_cli_strict_suppressed_low_evidence(tmp_path: Path) -> None:
    output_path = tmp_path / "incident_operations.json"
    runbook_path = tmp_path / "runbook.json"

    runbook_path.write_text(
        json.dumps(
            {
                "incident_required": True,
                "highest_severity": "p1",
                "quality_gate_passed": False,
                "failure_patterns": [{"pattern_id": "health_unhealthy"}],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ops/run_incident_operations.py",
            f"--runbook-report={runbook_path}",
            "--strict-operations",
            "--require-dispatch-sent",
            "--strict-min-evidence-completeness=1.0",
            f"--output={output_path}",
        ],
        cwd="/workspaces/revops-funnel-reconciliation-engine",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["strict_enforcement_suppressed"] is True
