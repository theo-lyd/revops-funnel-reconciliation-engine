from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_run_oncall_runbooks_skips_without_artifacts(tmp_path: Path) -> None:
    output_path = tmp_path / "runbook.json"
    missing_health = tmp_path / "missing-health.json"
    missing_dashboard = tmp_path / "missing-dashboard.json"
    missing_rollback = tmp_path / "missing-rollback.json"
    missing_dispatch = tmp_path / "missing-dispatch.json"
    missing_escalation = tmp_path / "missing-escalation.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ops/run_oncall_runbooks.py",
            f"--health-report={missing_health}",
            f"--dashboard-report={missing_dashboard}",
            f"--rollback-report={missing_rollback}",
            f"--incident-dispatch-report={missing_dispatch}",
            f"--dead-letter-escalation-report={missing_escalation}",
            f"--output={output_path}",
        ],
        cwd="/workspaces/revops-funnel-reconciliation-engine",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["overall_status"] == "skipped"


def test_run_oncall_runbooks_strict_fails_without_artifacts(tmp_path: Path) -> None:
    output_path = tmp_path / "runbook.json"
    missing_health = tmp_path / "missing-health.json"
    missing_dashboard = tmp_path / "missing-dashboard.json"
    missing_rollback = tmp_path / "missing-rollback.json"
    missing_dispatch = tmp_path / "missing-dispatch.json"
    missing_escalation = tmp_path / "missing-escalation.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ops/run_oncall_runbooks.py",
            "--strict-artifacts",
            f"--health-report={missing_health}",
            f"--dashboard-report={missing_dashboard}",
            f"--rollback-report={missing_rollback}",
            f"--incident-dispatch-report={missing_dispatch}",
            f"--dead-letter-escalation-report={missing_escalation}",
            f"--output={output_path}",
        ],
        cwd="/workspaces/revops-funnel-reconciliation-engine",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "no runbook artifacts found" in result.stdout.lower()


def test_run_oncall_runbooks_with_input_artifacts(tmp_path: Path) -> None:
    health_path = tmp_path / "health.json"
    dashboard_path = tmp_path / "dashboard.json"
    output_path = tmp_path / "runbook.json"

    health_path.write_text(json.dumps({"overall_status": "unhealthy"}), encoding="utf-8")
    dashboard_path.write_text(
        json.dumps({"operational_status": "critical", "sli_metrics": []}),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ops/run_oncall_runbooks.py",
            f"--health-report={health_path}",
            f"--dashboard-report={dashboard_path}",
            f"--output={output_path}",
        ],
        cwd="/workspaces/revops-funnel-reconciliation-engine",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["overall_status"] == "incident"
    assert payload["incident_required"] is True
    assert payload["highest_severity"] == "p1"
