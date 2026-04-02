from __future__ import annotations

import json
from pathlib import Path

from revops_funnel.deployment_ops import execute_deployment_rollback_playbook


def _write_rollback_report(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "release_id": "release-123",
                "rollback_actions": [
                    "Disable promotion flag for release release-123 to prevent new deployments.",
                    "Re-run release-readiness gate in strict mode before next promotion.",
                    "Attach rollback report and impacted checks to incident channel/ticket.",
                ],
            }
        ),
        encoding="utf-8",
    )


def test_execute_deployment_rollback_playbook_dry_run(tmp_path: Path) -> None:
    rollback_report = tmp_path / "artifacts" / "promotions" / "deployment_rollback.json"
    output = tmp_path / "artifacts" / "promotions" / "deployment_rollback_execution.json"
    _write_rollback_report(rollback_report)

    report = execute_deployment_rollback_playbook(
        rollback_report_path=rollback_report,
        execution_enabled=False,
        environment="production",
        output_path=output,
    )

    assert report.execution_mode == "dry-run"
    assert report.applied_actions == []
    assert len(report.deferred_actions) == 3
    assert output.exists()


def test_execute_deployment_rollback_playbook_controlled_mode(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    rollback_report = tmp_path / "artifacts" / "promotions" / "deployment_rollback.json"
    output = tmp_path / "artifacts" / "promotions" / "deployment_rollback_execution.json"
    _write_rollback_report(rollback_report)

    report = execute_deployment_rollback_playbook(
        rollback_report_path=rollback_report,
        execution_enabled=True,
        environment="production",
        output_path=output,
    )

    assert report.execution_mode == "controlled"
    assert len(report.applied_actions) == 2
    assert len(report.deferred_actions) == 1
    assert "artifacts/promotions/release_lock.json" in report.generated_artifacts
    assert "artifacts/promotions/rollback_incident_payload.json" in report.generated_artifacts
    assert output.exists()
