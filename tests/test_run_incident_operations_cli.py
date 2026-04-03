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
    assert payload["contract_version"] == "phase10.v1"
    assert payload["incident_open"] is True


def test_run_incident_operations_cli_strict_fails(tmp_path: Path) -> None:
    output_path = tmp_path / "incident_operations.json"
    runbook_path = tmp_path / "runbook.json"
    dispatch_path = tmp_path / "dispatch.json"
    escalation_path = tmp_path / "escalation.json"

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
